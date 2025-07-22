import asyncio
import os
import json
from dataclasses import dataclass, field
from typing import cast
from enum import Enum

import openai
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='static')

openai_client = openai.AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

class DatabaseType(Enum):
    ORACLE = "oracle"
    SQLITE = "sqlite"
    MYSQL = "mysql"

# Validate the env var
db_type_str = os.getenv("DB_TYPE", "").lower()
try:
    db_type = DatabaseType(db_type_str)
except ValueError:
    raise ValueError(f"Invalid DB_TYPE: {db_type_str}. Must be one of: {[e.value for e in DatabaseType]}")

db_type_string_value = db_type.value
# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="python",  # Executable
    args=[f"./servers/mcp_server_{db_type_string_value}.py"],  # link to where the mcp server is with tools for agent
    env=None,  # Optional environment variables
)

@dataclass
class ChatSession:
    messages: list[dict] = field(default_factory=list)
    session_id: str = ""

    system_prompt: str = """You are a master database assistant with access to database tools.

    CRITICAL: You MUST use the available tools to interact with the database. Never make assumptions about data without querying first.

    MANDATORY WORKFLOW:
    1. ALWAYS start by calling get_schema() or list_tables() to understand the database structure
    2. If the user asks about specific data, use describe_table() to understand table structure
    3. Use search_tables() to find relevant tables/columns for the user's question
    4. THEN write and execute SQL queries using query_data()

    IMPORTANT RULES:
    - Never guess table or column names - always verify them first using the schema tools
    - Always use the tools even for simple questions - the database structure may not be what you expect
    - If a query returns no results, double-check the table/column names and try alternative approaches
    - Be explicit about what you're doing: "Let me first check the database structure..."
    - ALWAYS provide a response to the user, even if it's just explaining what you're doing

    Your job is to use the available database tools to answer user questions accurately. Always use tools - never provide answers without querying the database first.
    """

    async def process_query(self, session: ClientSession, query: str) -> dict:
        try:
            response = await session.list_tools()
            available_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description or "",
                        "parameters": tool.inputSchema,
                    }
                }
                for tool in response.tools
            ]

            if not self.messages:
                self.messages.append({"role": "system", "content": self.system_prompt})

            # Add user message
            self.messages.append({"role": "user", "content": query})

            max_iterations = 5  # Prevent infinite loops
            iteration = 0
            response_text = ""

            while iteration < max_iterations:
                iteration += 1
                
                # Make API call to OpenAI
                res = await openai_client.chat.completions.create(
                    model="gpt-4o",
                    max_tokens=8000,
                    messages=self.messages,
                    tools=available_tools,
                    temperature=0.1,  # Lower temperature for more consistent responses
                )

                assistant_message = res.choices[0].message
                
                if assistant_message.content:
                    response_text = assistant_message.content
                    self.messages.append({"role": "assistant", "content": assistant_message.content})

                # Handle tool calls
                if assistant_message.tool_calls:
                    self.messages.append({
                        "role": "assistant", 
                        "content": assistant_message.content or "", 
                        "tool_calls": [
                            {
                                "id": tool_call.id,
                                "type": "function",
                                "function": {
                                    "name": tool_call.function.name,
                                    "arguments": tool_call.function.arguments
                                }
                            }
                            for tool_call in assistant_message.tool_calls
                        ]
                    })

                    # Execute each tool call
                    for tool_call in assistant_message.tool_calls:
                        tool_name = tool_call.function.name
                        try:
                            tool_args = json.loads(tool_call.function.arguments)
                        except json.JSONDecodeError:
                            tool_args = {}

                        # Execute tool call
                        result = await session.call_tool(tool_name, cast(dict, tool_args))
                        
                        result_content = ""
                        if result.content and len(result.content) > 0:
                            result_content = getattr(result.content[0], "text", "")

                        # Add tool result to messages
                        self.messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result_content,
                        })

                    # Continue the loop to get the next response
                    continue
                
                # If we got a text response and no tool calls, we're done
                if response_text:
                    break
                
                # If we got neither text nor tool calls, that's problematic
                if not assistant_message.content and not assistant_message.tool_calls:
                    # Add a follow-up message to prompt a response
                    self.messages.append({
                        "role": "user", 
                        "content": "Please provide a response to my previous question."
                    })
                    continue

            # If we still don't have a response after all iterations, provide a fallback
            if not response_text:
                # Make one final attempt with a more explicit prompt
                self.messages.append({
                    "role": "user", 
                    "content": "Please summarize what you found and provide your answer."
                })
                
                res = await openai_client.chat.completions.create(
                    model="gpt-4o",
                    max_tokens=8000,
                    messages=self.messages,
                    temperature=0.3,  # Slightly higher temperature to encourage response
                )
                
                final_response = res.choices[0].message.content
                if final_response:
                    self.messages.append({"role": "assistant", "content": final_response})
                    response_text = final_response
                else:
                    response_text = "I apologize, but I'm having trouble generating a response. Please try rephrasing your question."

            # Return format 
            return {
                "status": "success",
                "result": response_text,
                "message_count": len(self.messages)
            }

        except Exception as e:
            # Return error format 
            return {
                "status": "error",
                "message": str(e),
                "result": f"Error: {str(e)}"
            }


# Store chat sessions (in production, use Redis or a database)
chat_sessions = {}

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/api/query', methods=['POST'])
def query():
    """Handle query requests"""
    data = request.get_json()

    if not data or 'query' not in data:
        return jsonify({
            "status": "error",
            "message": "No query provided"
        }), 400
    
    query_text = data['query'].strip()
    session_id = data.get('session_id', 'default')
    
    if not query_text:
        return jsonify({
            "status": "error",
            "message": "Empty query"
        }), 400
    
    if session_id not in chat_sessions:
        chat_sessions[session_id] = ChatSession(session_id=session_id)
    
    chat_session = chat_sessions[session_id]
    
    async def process_async():
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await chat_session.process_query(session, query_text)
    
    try:
        result = asyncio.run(process_async())
        print(f"Query result: {result}") 
        return jsonify(result)
    except Exception as e:
        print(f"Error processing query: {str(e)}")  
        return jsonify({
            "status": "error",
            "message": f"Server error: {str(e)}"
        }), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    """Alternative endpoint with different response format"""
    data = request.get_json()
    
    if not data or 'query' not in data:
        return jsonify({"error": "No query provided"}), 400
    
    query_text = data['query'].strip()
    session_id = data.get('session_id', 'default')
    
    if not query_text:
        return jsonify({"error": "Empty query"}), 400
    
    if session_id not in chat_sessions:
        chat_sessions[session_id] = ChatSession(session_id=session_id)
    
    chat_session = chat_sessions[session_id]
    
    async def process_async():
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await chat_session.process_query(session, query_text)
    
    try:
        result = asyncio.run(process_async())
        if result["status"] == "success":
            return jsonify({
                "success": True,
                "response": result["result"],
                "message_count": result.get("message_count", 0)
            })
        else:
            return jsonify({
                "success": False,
                "error": result["message"],
                "response": f"Error: {result['message']}"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "response": f"Server error: {str(e)}"
        }), 500


@app.route('/api/clear', methods=['POST'])
def clear_chat():
    data = request.get_json()
    session_id = data.get('session_id', 'default') if data else 'default'
    
    if session_id in chat_sessions:
        chat_sessions[session_id] = ChatSession(session_id=session_id)
    
    return jsonify({"success": True, "message": "Chat history cleared"})


@app.route('/api/history', methods=['GET'])
def get_history():
    session_id = request.args.get('session_id', 'default')
    
    if session_id not in chat_sessions:
        return jsonify({"messages": []})
    
    chat_session = chat_sessions[session_id]
    
    # Filter out system messages and tool calls for display
    display_messages = []
    for msg in chat_session.messages:
        if msg['role'] in ['user', 'assistant'] and 'tool_calls' not in msg:
            display_messages.append({
                'role': msg['role'],
                'content': msg['content']
            })
    
    return jsonify({"messages": display_messages})


@app.route('/health')
def health_check():
    return jsonify({"status": "healthy", "service": "Database Assistant"})


if __name__ == '__main__':
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment variables")
        print("Please set your OpenAI API key in your .env file")
        exit(1)
    
    print("Starting Database Assistant Flask App...")
    print("Access the web interface at: http://localhost:10000")
    app.run(debug=True, host='0.0.0.0', port=10000)
