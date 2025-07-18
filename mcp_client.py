import asyncio
import os
import json
from dataclasses import dataclass, field
from typing import cast

import openai
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_from_directory
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='static')

# Initialize OpenAI client with API key from environment
openai_client = openai.AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="python",  # Executable
    args=["./mcp_server.py"],  # Updated to match your server file name
    env=None,  # Optional environment variables
)


@dataclass
class ChatSession:
    messages: list[dict] = field(default_factory=list)
    session_id: str = ""

    system_prompt: str = """You are a master SQLite assistant with access to database tools.

    IMPORTANT: Before writing any SQL queries, you MUST:
    1. First call get_schema() to understand the complete database structure
    2. Use list_tables() to see available tables
    3. Use describe_table(table_name) for detailed information about specific tables
    4. Use search_tables(keyword) to find relevant tables/columns

    When a user asks about data:
    1. Start by exploring the schema to understand what tables exist
    2. Look for tables that might contain the requested information
    3. Examine the structure of relevant tables
    4. Then write appropriate SQL queries using the correct table and column names

    Always validate that tables and columns exist before writing queries. If you're unsure about the database structure, use the schema tools to investigate.

    Your job is to use the tools at your disposal to execute SQL queries and provide accurate results to the user."""

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

            # Add system message if this is the first message
            if not self.messages:
                self.messages.append({"role": "system", "content": self.system_prompt})

            # Add user message
            self.messages.append({"role": "user", "content": query})

            # Initial OpenAI API call
            res = await openai_client.chat.completions.create(
                model="gpt-4o",
                max_tokens=8000,
                messages=self.messages,
                tools=available_tools,
            )

            assistant_message = res.choices[0].message
            response_text = ""

            # Handle text response
            if assistant_message.content:
                response_text = assistant_message.content
                self.messages.append({"role": "assistant", "content": assistant_message.content})

            # Handle tool calls
            if assistant_message.tool_calls:
                # Add assistant message with tool calls
                self.messages.append({
                    "role": "assistant", 
                    "content": assistant_message.content,
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

                    # Add tool result to messages
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": getattr(result.content[0], "text", ""),
                    })

                # Get next response from OpenAI
                res = await openai_client.chat.completions.create(
                    model="gpt-4o",
                    max_tokens=8000,
                    messages=self.messages,
                    tools=available_tools,
                )

                final_response = res.choices[0].message.content
                if final_response:
                    self.messages.append({"role": "assistant", "content": final_response})
                    response_text = final_response

            # Return format expected by your JavaScript
            return {
                "status": "success",
                "result": response_text,
                "message_count": len(self.messages)
            }

        except Exception as e:
            # Return error format expected by your JavaScript
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
    """Handle query requests - matches your JavaScript expectations"""
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
    
    # Get or create chat session
    if session_id not in chat_sessions:
        chat_sessions[session_id] = ChatSession(session_id=session_id)
    
    chat_session = chat_sessions[session_id]
    
    # Process query asynchronously
    async def process_async():
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await chat_session.process_query(session, query_text)
    
    # Run async function
    try:
        result = asyncio.run(process_async())
        return jsonify(result)
    except Exception as e:
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
    
    # Get or create chat session
    if session_id not in chat_sessions:
        chat_sessions[session_id] = ChatSession(session_id=session_id)
    
    chat_session = chat_sessions[session_id]
    
    # Process query asynchronously
    async def process_async():
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await chat_session.process_query(session, query_text)
    
    # Run async function
    try:
        result = asyncio.run(process_async())
        # Convert to the format expected by the other frontend
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
    return jsonify({"status": "healthy", "service": "SQLite Assistant"})


if __name__ == '__main__':
    # Check if required environment variables are set
    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY not found in environment variables")
        print("Please set your OpenAI API key in your .env file")
        exit(1)
    
    print("Starting SQLite Assistant Flask App...")
    print("Access the web interface at: http://localhost:10000")
    app.run(debug=True, host='0.0.0.0', port=10000)
    