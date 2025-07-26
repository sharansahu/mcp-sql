# MCP Database Assistant

An AI-powered multi-database assistant built with OpenAI's GPT models and Model Context Protocol (MCP). This project demonstrates how to create an intelligent database query interface that can understand natural language requests and execute SQL queries with full schema awareness across MySQL, Oracle, and SQLite databases.

<a href="https://glama.ai/mcp/servers/@sharansahu/mcp-sql">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@sharansahu/mcp-sql/badge" alt="SQL Agent MCP server" />
</a>

## 🌟 Key Features

- **🤖 AI-Powered SQL Assistant** - Natural language to SQL query conversion using OpenAI GPT-4o
- **🔧 Model Context Protocol Integration** - Seamless tool calling and context management
- **🗄️ Multi-Database Support** - Works with MySQL, Oracle, and SQLite databases
- **🌐 Modern Web Interface** - Clean, responsive chat interface with real-time query processing
- **📊 Schema Discovery** - Automatic database structure exploration and validation
- **🔍 Smart Search** - Find tables and columns by keywords
- **💾 Session Management** - Persistent chat history during browser sessions
- **⚡ Real-time Processing** - Async handling for fast query execution
- **🛡️ Safe Query Execution** - Protected SQL execution with error handling
- **🔄 Dual API Support** - Multiple endpoint formats for different frontend requirements

## 📋 Prerequisites

- **Python 3.12+** (specified in `.python-version`)
- **OpenAI API Key** - Get one from [OpenAI Platform](https://platform.openai.com/api-keys)
- **Database** - One of the following:
  - SQLite database file (`.db`)
  - MySQL server with accessible database
  - Oracle database with proper connection string

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
git clone https://github.com/sharansahu/mcp-sql
cd mcp-sql

# Create virtual environment and install dependencies
uv sync
```

### 3. Environment Configuration

Create a `.env` file in the project root with your database configuration:

**For SQLite:**
```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
DB_TYPE=sqlite
DB_PATH=./dod_synthetic.db
```

**For MySQL:**
```env
# OpenAI Configuration  
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
DB_TYPE=mysql
DB_HOST=localhost
DB_PORT=3306
DB_NAME=your_database_name
DB_USER=your_username
DB_PASSWORD=your_password
```

**For Oracle:**
```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Database Configuration
DB_TYPE=oracle
DB_USER=your_username
DB_PASSWORD=your_password
DB_DSN=hostname:port/service_name
```

## 📁 Project Structure

```
mcp-database-assistant/
├── README.md           # Project documentation
├── mcp_client.py       # Flask web application (main entry point)
├── servers/            # MCP server implementations
│   ├── mcp_server_sqlite.py   # SQLite MCP server with database tools
│   ├── mcp_server_mysql.py    # MySQL MCP server with database tools  
│   └── mcp_server_oracle.py   # Oracle MCP server with database tools
├── dod_synthetic.db    # Sample SQLite database (if using SQLite)
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
   - Example: "What's the structure of the users table?"

## 💡 Example Queries

The AI assistant can handle various types of database queries:

### Schema Exploration
- "What tables are available in this database?"
- "Describe the structure of the personnel table"
- "Search for tables related to maintenance"
- "Show me the schema for all tables"

### Data Analysis
- "How many records are in each table?"
- "Show me the first 5 personnel records"
- "Find all equipment of type 'tank'"
- "What are the column names in the orders table?"

### Complex Queries
- "Show personnel who performed maintenance on tanks in the last 90 days"
- "What's the average number of maintenance tasks per person?"
- "List equipment that hasn't been maintained recently"
- "Find the top 10 customers by order value"

## 🛠️ Database Tools

The MCP servers provide several powerful tools for database interaction:

- **`get_schema()`** - Get complete database schema with sample data
- **`list_tables()`** - List all available tables
- **`describe_table(table_name)`** - Detailed table information including columns and sample data
- **`search_tables(keyword)`** - Find tables/columns by keyword
- **`query_data(sql)`** - Execute SQL queries safely

## 📡 API Endpoints

The Flask app provides several REST API endpoints:

- `GET /` - Serve the main web interface
- `POST /api/query` - Process natural language queries (returns detailed status)
- `POST /api/chat` - Alternative query endpoint (returns simplified response)
- `POST /api/clear` - Clear chat session history
- `GET /api/history` - Retrieve chat history
- `GET /health` - Health check endpoint

## 🔍 How It Works

1. **Database Type Detection** - System loads appropriate MCP server based on `DB_TYPE` environment variable
2. **User Input** - Natural language query via web interface
3. **Schema Discovery** - AI explores database structure using MCP tools
4. **Query Generation** - AI generates appropriate SQL based on schema and database type
5. **Safe Execution** - SQL query executed with proper error handling
6. **Result Formatting** - Results formatted and returned to user
7. **Session Management** - Conversation history maintained for context

## 🔧 Database-Specific Features

### SQLite
- File-based database support
- Full schema introspection
- Sample data preview

### MySQL  
- Connection pooling
- UTF-8 support with proper collation
- Primary key detection
- Row count and sample data

### Oracle
- Case-sensitive table/column handling (uppercase)
- ROWNUM-based pagination
- Primary key constraint detection
- User schema awareness

## 🚨 Troubleshooting

### Common Issues

**"Invalid DB_TYPE" error**
- Ensure `DB_TYPE` is set to one of: `sqlite`, `mysql`, or `oracle`
- Check that your `.env` file is properly formatted

**"No module named 'openai'"**
```bash
uv sync  # Reinstall dependencies
```

**"OPENAI_API_KEY not found"**
- Ensure your `.env` file exists and contains your API key
- Check that the API key is valid and has sufficient credits

**Database connection errors**
- **SQLite**: Verify the `DB_PATH` points to your database file
- **MySQL**: Check `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD`
- **Oracle**: Verify `DB_USER`, `DB_PASSWORD`, and `DB_DSN` format

**Web interface not loading**
- Check that Flask is running on the correct port (10000)
- Verify static files are in the `static/` directory

### Database-Specific Issues

**MySQL Connection Issues:**
- Ensure MySQL server is running
- Verify user has proper permissions
- Check firewall settings if connecting remotely

**Oracle Connection Issues:**
- Verify Oracle Instant Client is installed
- Check TNS names configuration
- Ensure service name in DSN is correct

### Debug Mode

Run with additional logging:
```bash
FLASK_DEBUG=True uv run python mcp_client.py
```

## 🛡️ Security Considerations

- Never commit your `.env` file with real credentials
- Use environment variables or secure vaults in production
- Implement proper database user permissions
- Consider SQL injection protection (built into the MCP tools)
- Use HTTPS in production environments

## 🚀 Deployment

### Local Development
The current setup is optimized for local development with the Flask development server.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.