import sqlite3
import os

from loguru import logger
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("Demo")

load_dotenv()

db_path = os.getenv("DB_PATH")

def get_database_schema() -> str:
    """Get the database schema information"""
    conn = sqlite3.connect(db_path)
    try:
        # Get all table names
        tables_query = "SELECT name FROM sqlite_master WHERE type='table';"
        tables = conn.execute(tables_query).fetchall()
        
        schema_info = "Database Schema:\n\n"
        
        for (table_name,) in tables:
            schema_info += f"Table: {table_name}\n"
            
            # Get column information for each table
            pragma_query = f"PRAGMA table_info({table_name});"
            columns = conn.execute(pragma_query).fetchall()
            
            for column in columns:
                cid, name, data_type, notnull, default_value, pk = column
                pk_indicator = " (PRIMARY KEY)" if pk else ""
                null_indicator = " NOT NULL" if notnull else ""
                default_indicator = f" DEFAULT {default_value}" if default_value else ""
                schema_info += f"  - {name}: {data_type}{pk_indicator}{null_indicator}{default_indicator}\n"
            
            # Get sample data (first 3 rows)
            sample_query = f"SELECT * FROM {table_name} LIMIT 3;"
            try:
                sample_data = conn.execute(sample_query).fetchall()
                if sample_data:
                    schema_info += f"  Sample data:\n"
                    for row in sample_data:
                        schema_info += f"    {row}\n"
            except Exception as e:
                schema_info += f"  Sample data: Error reading sample data - {e}\n"
            
            schema_info += "\n"
        
        return schema_info
        
    except Exception as e:
        return f"Error getting schema: {str(e)}"
    finally:
        conn.close()

@mcp.tool()
def get_schema() -> str:
    """Get the complete database schema with table structures and sample data"""
    return get_database_schema()

@mcp.tool()
def list_tables() -> str:
    """List all tables in the database"""
    conn = sqlite3.connect(db_path)
    try:
        tables_query = "SELECT name FROM sqlite_master WHERE type='table';"
        tables = conn.execute(tables_query).fetchall()
        table_list = "Available tables:\n"
        for (table_name,) in tables:
            table_list += f"- {table_name}\n"
        return table_list
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        conn.close()

@mcp.tool()
def describe_table(table_name: str) -> str:
    """Get detailed information about a specific table including columns and sample data"""
    conn = sqlite3.connect(db_path)
    try:
        # Check if table exists
        check_query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?;"
        exists = conn.execute(check_query, (table_name,)).fetchone()
        
        if not exists:
            return f"Table '{table_name}' does not exist."
        
        # Get column information
        pragma_query = f"PRAGMA table_info({table_name});"
        columns = conn.execute(pragma_query).fetchall()
        
        table_info = f"Table: {table_name}\n\nColumns:\n"
        for column in columns:
            cid, name, data_type, notnull, default_value, pk = column
            pk_indicator = " (PRIMARY KEY)" if pk else ""
            null_indicator = " NOT NULL" if notnull else ""
            default_indicator = f" DEFAULT {default_value}" if default_value else ""
            table_info += f"  - {name}: {data_type}{pk_indicator}{null_indicator}{default_indicator}\n"
        
        # Get row count
        count_query = f"SELECT COUNT(*) FROM {table_name};"
        row_count = conn.execute(count_query).fetchone()[0]
        table_info += f"\nTotal rows: {row_count}\n"
        
        # Get sample data
        sample_query = f"SELECT * FROM {table_name} LIMIT 5;"
        sample_data = conn.execute(sample_query).fetchall()
        if sample_data:
            table_info += f"\nSample data (first 5 rows):\n"
            # Get column names for header
            column_names = [col[1] for col in columns]
            table_info += f"  {' | '.join(column_names)}\n"
            table_info += f"  {'-' * (len(' | '.join(column_names)))}\n"
            for row in sample_data:
                table_info += f"  {' | '.join(str(val) for val in row)}\n"
        
        return table_info
        
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        conn.close()

@mcp.tool()
def query_data(sql: str) -> str:
    """Execute SQL queries safely. Use get_schema() first to understand the database structure."""
    logger.info(f"Executing SQL query: {sql}")
    conn = sqlite3.connect(db_path)
    try:
        result = conn.execute(sql).fetchall()
        conn.commit()
        
        if not result:
            return "Query executed successfully but returned no results."
        
        # Format results nicely
        output = f"Query returned {len(result)} row(s):\n\n"
        for i, row in enumerate(result, 1):
            output += f"Row {i}: {row}\n"
        
        return output
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        conn.close()

@mcp.tool()
def search_tables(keyword: str) -> str:
    """Search for tables or columns containing a specific keyword"""
    conn = sqlite3.connect(db_path)
    try:
        # Get all tables
        tables_query = "SELECT name FROM sqlite_master WHERE type='table';"
        tables = conn.execute(tables_query).fetchall()
        
        matches = []
        
        for (table_name,) in tables:
            # Check if table name contains keyword
            if keyword.lower() in table_name.lower():
                matches.append(f"Table: {table_name}")
            
            # Check columns
            pragma_query = f"PRAGMA table_info({table_name});"
            columns = conn.execute(pragma_query).fetchall()
            
            matching_columns = []
            for column in columns:
                column_name = column[1]
                if keyword.lower() in column_name.lower():
                    matching_columns.append(column_name)
            
            if matching_columns:
                matches.append(f"Table '{table_name}' has columns: {', '.join(matching_columns)}")
        
        if matches:
            return f"Found matches for '{keyword}':\n" + "\n".join(matches)
        else:
            return f"No tables or columns found containing '{keyword}'"
            
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        conn.close()

@mcp.prompt()
def database_context() -> str:
    """Provides context about the database schema for the AI assistant"""
    return f"""Database Context:

{get_database_schema()}

Instructions for querying:
1. Always use get_schema() or list_tables() first to understand the database structure
2. Use describe_table(table_name) to get detailed information about specific tables
3. Use search_tables(keyword) to find tables or columns related to specific concepts
4. When writing SQL queries, make sure to reference the correct table and column names
5. Always validate table and column names exist before writing complex queries

Available tools:
- get_schema(): Get complete database schema
- list_tables(): List all available tables
- describe_table(table_name): Get detailed table information
- search_tables(keyword): Search for tables/columns by keyword
- query_data(sql): Execute SQL queries
"""

@mcp.prompt()
def example_prompt(code: str) -> str:
    return f"Please review this code:\n\n{code}"


if __name__ == "__main__":
    print("Starting server...")
    # Initialize and run the server
    mcp.run(transport="stdio")
    