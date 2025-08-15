import mysql.connector
import os

from loguru import logger
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("Demo")

load_dotenv()

# MySQL connection parameters
db_config = {
    'host': os.getenv("DB_HOST", "localhost"),
    'port': int(os.getenv("DB_PORT", 3306)),
    'database': os.getenv("DB_NAME"),
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD"),
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}

def get_database_schema() -> str:
    """Get the database schema information"""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # Get all table names
        tables_query = """
        SELECT TABLE_NAME 
        FROM information_schema.TABLES 
        WHERE TABLE_SCHEMA = %s
        """
        cursor.execute(tables_query, (db_config['database'],))
        tables = cursor.fetchall()
        
        schema_info = f"Database Schema for '{db_config['database']}':\n\n"
        
        for (table_name,) in tables:
            schema_info += f"Table: {table_name}\n"
            
            # Get column information for each table
            columns_query = """
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_KEY, EXTRA
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            ORDER BY ORDINAL_POSITION
            """
            cursor.execute(columns_query, (db_config['database'], table_name))
            columns = cursor.fetchall()
            
            for column in columns:
                col_name, data_type, is_nullable, default_value, column_key, extra = column
                pk_indicator = " (PRIMARY KEY)" if column_key == "PRI" else ""
                null_indicator = " NOT NULL" if is_nullable == "NO" else ""
                default_indicator = f" DEFAULT {default_value}" if default_value else ""
                auto_inc = f" {extra}" if extra else ""
                schema_info += f"  - {col_name}: {data_type}{pk_indicator}{null_indicator}{default_indicator}{auto_inc}\n"
            
            # Get sample data (first 3 rows)
            sample_query = f"SELECT * FROM `{table_name}` LIMIT 3"
            try:
                cursor.execute(sample_query)
                sample_data = cursor.fetchall()
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
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@mcp.tool()
def get_schema() -> str:
    """Get the complete database schema with table structures and sample data"""
    return get_database_schema()

@mcp.tool()
def list_tables() -> str:
    """List all tables in the database"""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        tables_query = """
        SELECT TABLE_NAME 
        FROM information_schema.TABLES 
        WHERE TABLE_SCHEMA = %s
        """
        cursor.execute(tables_query, (db_config['database'],))
        tables = cursor.fetchall()
        
        table_list = "Available tables:\n"
        for (table_name,) in tables:
            table_list += f"- {table_name}\n"
        return table_list
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@mcp.tool()
def describe_table(table_name: str) -> str:
    """Get detailed information about a specific table including columns and sample data"""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # Check if table exists
        check_query = """
        SELECT TABLE_NAME 
        FROM information_schema.TABLES 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        """
        cursor.execute(check_query, (db_config['database'], table_name))
        exists = cursor.fetchone()
        
        if not exists:
            return f"Table '{table_name}' does not exist."
        
        # Get column information
        columns_query = """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, COLUMN_KEY, EXTRA
        FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        ORDER BY ORDINAL_POSITION
        """
        cursor.execute(columns_query, (db_config['database'], table_name))
        columns = cursor.fetchall()
        
        table_info = f"Table: {table_name}\n\nColumns:\n"
        column_names = []
        for column in columns:
            col_name, data_type, is_nullable, default_value, column_key, extra = column
            column_names.append(col_name)
            pk_indicator = " (PRIMARY KEY)" if column_key == "PRI" else ""
            null_indicator = " NOT NULL" if is_nullable == "NO" else ""
            default_indicator = f" DEFAULT {default_value}" if default_value else ""
            auto_inc = f" {extra}" if extra else ""
            table_info += f"  - {col_name}: {data_type}{pk_indicator}{null_indicator}{default_indicator}{auto_inc}\n"
        
        # Get row count
        count_query = f"SELECT COUNT(*) FROM `{table_name}`"
        cursor.execute(count_query)
        row_count = cursor.fetchone()[0]
        table_info += f"\nTotal rows: {row_count}\n"
        
        # Get sample data
        sample_query = f"SELECT * FROM `{table_name}` LIMIT 5"
        cursor.execute(sample_query)
        sample_data = cursor.fetchall()
        if sample_data:
            table_info += f"\nSample data (first 5 rows):\n"
            table_info += f"  {' | '.join(column_names)}\n"
            table_info += f"  {'-' * (len(' | '.join(column_names)))}\n"
            for row in sample_data:
                table_info += f"  {' | '.join(str(val) for val in row)}\n"
        
        return table_info
        
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@mcp.tool()
def query_data(sql: str) -> str:
    """Execute SQL queries safely. Use get_schema() first to understand the database structure."""
    logger.info(f"Executing SQL query: {sql}")
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        cursor.execute(sql)
        
        # Handle different types of queries
        if sql.strip().upper().startswith(('SELECT', 'SHOW', 'DESCRIBE', 'EXPLAIN')):
            result = cursor.fetchall()
            if not result:
                return "Query executed successfully but returned no results."
            
            # Format results nicely
            output = f"Query returned {len(result)} row(s):\n\n"
            for i, row in enumerate(result, 1):
                output += f"Row {i}: {row}\n"
        else:
            # For INSERT, UPDATE, DELETE, etc.
            conn.commit()
            output = f"Query executed successfully. Affected rows: {cursor.rowcount}"
        
        return output
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@mcp.tool()
def search_tables(keyword: str) -> str:
    """Search for tables or columns containing a specific keyword"""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        
        # Get all tables
        tables_query = """
        SELECT TABLE_NAME 
        FROM information_schema.TABLES 
        WHERE TABLE_SCHEMA = %s
        """
        cursor.execute(tables_query, (db_config['database'],))
        tables = cursor.fetchall()
        
        matches = []
        
        for (table_name,) in tables:
            # Check if table name contains keyword
            if keyword.lower() in table_name.lower():
                matches.append(f"Table: {table_name}")
            
            # Check columns
            columns_query = """
            SELECT COLUMN_NAME 
            FROM information_schema.COLUMNS 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            """
            cursor.execute(columns_query, (db_config['database'], table_name))
            columns = cursor.fetchall()
            
            matching_columns = []
            for (column_name,) in columns:
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
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@mcp.prompt()
def database_context() -> str:
    """Provides context about the database schema for the AI assistant"""
    return f"""Database Context:

    {get_database_schema()}

    Instructions for querying:
    1) Start with get_schema() or list_tables() to view the overall structure.
    2) Use describe_table(table_name) to confirm column names and data types.
    3) Use search_tables(keyword) to locate relevant tables/columns.
    4) When writing SQL for query_data(sql), ALWAYS:
    - Use parameterized queries (bind variables). Do NOT concatenate user input.
    - Prefer LIKE over '=' for any substring/partial text intent; reserve '=' for true exact IDs.
    - Normalize text (Unicode spaces/dashes & collapsed whitespace) **before** filtering.
    - Escape user-supplied '%', '_' and '\\' for LIKE patterns.
    - Force case/diacritic-insensitive comparison with an appropriate collation.

    Text matching policy (CRITICAL):
    - Default to LIKE for partial text:
        -- contains
        {{col_norm}} COLLATE utf8mb4_0900_ai_ci LIKE CONCAT('%', {{term_esc}}, '%')
        -- starts with
        {{col_norm}} COLLATE utf8mb4_0900_ai_ci LIKE CONCAT({{term_esc}}, '%')
        -- ends with
        {{col_norm}} COLLATE utf8mb4_0900_ai_ci LIKE CONCAT('%', {{term_esc}})
    - Use '=' ONLY for explicit exact-match requests or unique identifiers (numeric IDs, UUIDs, exact codes).

    LIKE wildcard escaping (MySQL):
    - MySQL uses '\\' as the LIKE escape (unless NO_BACKSLASH_ESCAPES is set).
    - Always transform the bound term inside SQL (so prepared statements stay safe):
        -- term_esc := REPLACE(REPLACE(REPLACE(?, '\\\\', '\\\\\\\\'), '%', '\\\\%'), '_', '\\\\_')
    Example usage:
        WHERE {{col_norm}} COLLATE utf8mb4_0900_ai_ci LIKE CONCAT('%', term_esc, '%')
    - Ensure NO_BACKSLASH_ESCAPES is **not** enabled for the session when relying on '\\' escapes.

    Unicode & punctuation normalization (define once per filtered column):
    - Normalize to a stable form **in the predicate** (or via a generated column) to survive NBSPs, narrow NBSPs, and fancy dashes, and to collapse whitespace:
        -- col_norm :=
        REGEXP_REPLACE(                                      -- collapse all whitespace to single space
            REGEXP_REPLACE(                                    -- unify dashes/hyphens to '-'
            REGEXP_REPLACE(col, '[\\x{{00A0}}\\x{{202F}}]', ' '),   -- NBSP, narrow NBSP -> space
            '[\\x{{2010}}-\\x{{2015}}]', '-'
            ),
            '[[:space:]]+', ' '
        )
    - Always apply LIKE to col_norm, not the raw column.

    Handling common field types in your dataset:
    - Booleans like 'Yes, (HLC [Higher Learning Commission])':
        CASE
        WHEN REGEXP_LIKE(UPPER(col)), '^\\s*Y(ES)?\\b') THEN 1
        WHEN REGEXP_LIKE(UPPER(col), '^\\s*N(O)?\\b')  THEN 0
        ELSE NULL
        END
    - Numeric price from strings like '$250 ':
        CAST(REGEXP_SUBSTR(price_col, '[0-9]+(\\.[0-9]+)?') AS DECIMAL(10,2))
    - Hours/CEUs from strings like '~4–6 hours (1 CEU)':
        -- low hours:  REGEXP_SUBSTR(dur_col, '([0-9]+(\\.[0-9]+)?)', 1, 1)
        -- high hours: REGEXP_SUBSTR(dur_col, '([0-9]+(\\.[0-9]+)?)', 1, 2)
        -- CEUs:       REGEXP_SUBSTR(dur_col, '([0-9]+(\\.[0-9]+)?)\\s*CEU', 1, 1)

    Zero-results recovery:
    1) Re-check table/column names & types via describe_table().
    2) Switch '=' to LIKE over col_norm with proper escaping & case-insensitive collation.
    3) Search across multiple plausible columns (institution, campus, state, title, roles).
    4) Sample rows (e.g., LIMIT 20) to validate coverage and spot formatting anomalies.
    5) If still empty, broaden terms, remove leading/trailing punctuation, and verify session SQL mode (NO_BACKSLASH_ESCAPES).

    Performance tips (MySQL 8):
    - Prefer "starts with" (no leading '%') to enable index usage.
    - Create a functional index or generated column for normalization:
        -- Example generated column & index:
        ALTER TABLE t
        ADD COLUMN col_norm_gen VARCHAR(1024)
            GENERATED ALWAYS AS (
            REGEXP_REPLACE(
                REGEXP_REPLACE(
                REGEXP_REPLACE(col, '[\\x{{00A0}}\\x{{202F}}]', ' '),
                '[\\x{{2010}}-\\x{{2015}}]', '-'
                ),
                '[[:space:]]+', ' '
            )
            ) STORED,
        ADD INDEX idx_col_norm (col_norm_gen);
    Then filter on UPPER(col_norm_gen) or with COLLATE utf8mb4_0900_ai_ci.
    - Use EXPLAIN to confirm index usage; avoid leading '%' unless necessary.

    Conventions:
    - Use backticks for identifiers with special characters: `table`, `column`.
    - LIMIT result size for exploratory queries.
    - Always narrate steps briefly so the user understands what you’re checking and why.

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
    print("Starting MySQL server...")
    # Initialize and run the server
    mcp.run(transport="stdio")