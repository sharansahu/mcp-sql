# MCP with SQL Agent

An AI-powered SQLite assistant built with OpenAI's GPT models and Model Context Protocol (MCP). This project demonstrates how to create an intelligent database query interface that can understand natural language requests and execute SQL queries with full schema awareness.

## 🌟 Key Features

- **🤖 AI-Powered SQL Assistant** - Natural language to SQL query conversion using OpenAI GPT-4o
- **🔧 Model Context Protocol Integration** - Seamless tool calling and context management
- **🌐 Modern Web Interface** - Clean, responsive chat interface with real-time query processing
- **📊 Schema Discovery** - Automatic database structure exploration and validation
- **🔍 Smart Search** - Find tables and columns by keywords
- **💾 Session Management** - Persistent chat history during browser sessions
- **⚡ Real-time Processing** - Async handling for fast query execution
- **🛡️ Safe Query Execution** - Protected SQL execution with error handling

## 📋 Prerequisites

- **Python 3.12+** (specified in `.python-version`)
- **OpenAI API Key** - Get one from [OpenAI Platform](https://platform.openai.com/api-keys)
- **SQLite Database** - A `.db` file to query against

## 🚀 Installation

### 1. Install uv (in case you haven't installed it yet)

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows:**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Alternative (via pip):**
```bash
pip install uv
```

### 2. Clone and Setup Project

```bash
git clone <your-repo-url>
cd introduction-to-mcp-with-sql-agent

# Create virtual environment and install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Environment Configuration

Create a `.env` file in the project root:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
DB_PATH=./dod_synthetic.db

# Flask Configuration (optional)
FLASK_ENV=development
FLASK_DEBUG=True
```

## 📁 Project Structure

```
introduction-to-mcp-with-sql-agent/
├── README.md           # Project documentation
├── mcp_client.py       # Flask web application
├── mcp_server.py       # MCP server with database tools
├── dod_synthetic.db    # SQLite database
├── pyproject.toml      # Project dependencies and configuration
├── .env                # Environment variables (create this)
├── .python-version     # Python version specification
├── static/             # Web interface files
│   ├── index.html      # Main web interface
│   ├── script.js       # Frontend JavaScript
│   └── styles.css      # Interface styling
├── .gitignore          # Git ignore file
└── .venv/              # Virtual environment (created by uv)
```

## 🎯 Usage

### Web Interface (Recommended)

1. **Start the Flask application:**
   ```bash
   uv run python mcp_client.py
   ```

2. **Access the web interface:**
   Open your browser and go to: http://localhost:10000

3. **Start querying:**
   - Type natural language questions about your database
   - Example: "Show me all tables in the database"
   - Example: "Find personnel who worked on tank maintenance in the last 90 days"

### Terminal Interface (Alternative)

If you prefer command-line interaction, you can run the client directly:
```bash
uv run python mcp_client.py --terminal
```

## 💡 Example Queries

The AI assistant can handle various types of database queries:

### Schema Exploration
- "What tables are available in this database?"
- "Describe the structure of the personnel table"
- "Search for tables related to maintenance"

### Data Analysis
- "How many records are in each table?"
- "Show me the first 5 personnel records"
- "Find all equipment of type 'tank'"

### Complex Queries
- "Show personnel who performed maintenance on tanks in the last 90 days"
- "What's the average number of maintenance tasks per person?"
- "List equipment that hasn't been maintained recently"

## 🛠️ Database Tools

The MCP server provides several powerful tools for database interaction:

- **`get_schema()`** - Get complete database schema with sample data
- **`list_tables()`** - List all available tables
- **`describe_table(table_name)`** - Detailed table information
- **`search_tables(keyword)`** - Find tables/columns by keyword
- **`query_data(sql)`** - Execute SQL queries safely

## 📡 API Endpoints

The Flask app provides several REST API endpoints:

- `GET /` - Serve the main web interface
- `POST /api/query` - Process natural language queries
- `POST /api/clear` - Clear chat session history
- `GET /api/history` - Retrieve chat history
- `GET /health` - Health check endpoint

## 🔍 How It Works

1. **User Input** - Natural language query via web interface
2. **Schema Discovery** - AI explores database structure using MCP tools
3. **Query Generation** - AI generates appropriate SQL based on schema
4. **Safe Execution** - SQL query executed with error handling
5. **Result Formatting** - Results formatted and returned to user

## 🚨 Troubleshooting

### Common Issues

**"No module named 'openai'"**
```bash
uv sync  # Reinstall dependencies
```

**"OPENAI_API_KEY not found"**
- Ensure your `.env` file exists and contains your API key
- Check that the API key is valid

**"Database file not found"**
- Verify the `DB_PATH` in your `.env` file points to your database
- Ensure the database file exists and is readable

**Web interface not loading**
- Check that Flask is running on the correct port (10000)
- Verify static files are in the `static/` directory

### Debug Mode

Run with additional logging:
```bash
FLASK_DEBUG=True uv run python mcp_client.py
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.