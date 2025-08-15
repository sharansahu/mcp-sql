import cx_Oracle
import os

from loguru import logger
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Create an MCP server
mcp = FastMCP("Demo")

load_dotenv()

# Oracle connection parameters
db_config = {
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD"),
    'dsn': os.getenv("DB_DSN"),  # Format: host:port/service_name
    'encoding': 'UTF-8'
}

def get_database_schema() -> str:
    """Get the database schema information"""
    try:
        conn = cx_Oracle.connect(**db_config)
        cursor = conn.cursor()
        
        # Get current user/schema
        cursor.execute("SELECT USER FROM DUAL")
        current_user = cursor.fetchone()[0]
        
        # Get all table names for current user
        tables_query = """
        SELECT table_name 
        FROM user_tables 
        ORDER BY table_name
        """
        cursor.execute(tables_query)
        tables = cursor.fetchall()
        
        schema_info = f"Database Schema for user '{current_user}':\n\n"
        
        for (table_name,) in tables:
            schema_info += f"Table: {table_name}\n"
            
            # Get column information for each table
            columns_query = """
            SELECT 
                column_name, 
                data_type, 
                nullable, 
                data_default,
                CASE WHEN column_name IN (
                    SELECT column_name 
                    FROM user_cons_columns ucc
                    JOIN user_constraints uc ON ucc.constraint_name = uc.constraint_name
                    WHERE uc.table_name = ? AND uc.constraint_type = 'P'
                ) THEN 'Y' ELSE 'N' END as is_primary_key
            FROM user_tab_columns 
            WHERE table_name = ?
            ORDER BY column_id
            """
            cursor.execute(columns_query, (table_name, table_name))
            columns = cursor.fetchall()
            
            for column in columns:
                col_name, data_type, nullable, default_value, is_pk = column
                pk_indicator = " (PRIMARY KEY)" if is_pk == 'Y' else ""
                null_indicator = " NOT NULL" if nullable == 'N' else ""
                default_indicator = f" DEFAULT {default_value}" if default_value else ""
                schema_info += f"  - {col_name}: {data_type}{pk_indicator}{null_indicator}{default_indicator}\n"
            
            # Get sample data (first 3 rows)
            sample_query = f"SELECT * FROM {table_name} WHERE ROWNUM <= 3"
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
        conn = cx_Oracle.connect(**db_config)
        cursor = conn.cursor()
        
        tables_query = """
        SELECT table_name 
        FROM user_tables 
        ORDER BY table_name
        """
        cursor.execute(tables_query)
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
        conn = cx_Oracle.connect(**db_config)
        cursor = conn.cursor()
        
        # Check if table exists
        table_name_upper = table_name.upper()
        check_query = "SELECT table_name FROM user_tables WHERE table_name = :1"
        cursor.execute(check_query, (table_name_upper,))
        exists = cursor.fetchone()
        
        if not exists:
            return f"Table '{table_name}' does not exist."
        
        # Get column information
        columns_query = """
        SELECT 
            column_name, 
            data_type, 
            nullable, 
            data_default,
            CASE WHEN column_name IN (
                SELECT column_name 
                FROM user_cons_columns ucc
                JOIN user_constraints uc ON ucc.constraint_name = uc.constraint_name
                WHERE uc.table_name = :1 AND uc.constraint_type = 'P'
            ) THEN 'Y' ELSE 'N' END as is_primary_key
        FROM user_tab_columns 
        WHERE table_name = :2
        ORDER BY column_id
        """
        cursor.execute(columns_query, (table_name_upper, table_name_upper))
        columns = cursor.fetchall()
        
        table_info = f"Table: {table_name_upper}\n\nColumns:\n"
        column_names = []
        for column in columns:
            col_name, data_type, nullable, default_value, is_pk = column
            column_names.append(col_name)
            pk_indicator = " (PRIMARY KEY)" if is_pk == 'Y' else ""
            null_indicator = " NOT NULL" if nullable == 'N' else ""
            default_indicator = f" DEFAULT {default_value}" if default_value else ""
            table_info += f"  - {col_name}: {data_type}{pk_indicator}{null_indicator}{default_indicator}\n"
        
        # Get row count
        count_query = f"SELECT COUNT(*) FROM {table_name_upper}"
        cursor.execute(count_query)
        row_count = cursor.fetchone()[0]
        table_info += f"\nTotal rows: {row_count}\n"
        
        # Get sample data
        sample_query = f"SELECT * FROM {table_name_upper} WHERE ROWNUM <= 5"
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
        conn = cx_Oracle.connect(**db_config)
        cursor = conn.cursor()
        
        cursor.execute(sql)
        
        # Handle different types of queries
        if sql.strip().upper().startswith(('SELECT', 'WITH')):
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
        conn = cx_Oracle.connect(**db_config)
        cursor = conn.cursor()
        
        # Get all tables
        tables_query = """
        SELECT table_name 
        FROM user_tables 
        ORDER BY table_name
        """
        cursor.execute(tables_query)
        tables = cursor.fetchall()
        
        matches = []
        
        for (table_name,) in tables:
            # Check if table name contains keyword
            if keyword.upper() in table_name.upper():
                matches.append(f"Table: {table_name}")
            
            # Check columns
            columns_query = """
            SELECT column_name 
            FROM user_tab_columns 
            WHERE table_name = :1
            """
            cursor.execute(columns_query, (table_name,))
            columns = cursor.fetchall()
            
            matching_columns = []
            for (column_name,) in columns:
                if keyword.upper() in column_name.upper():
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
+)
{get_database_schema()}

Instructions for querying:
1) Start with get_schema() or list_tables() to understand the overall structure.
2) Use describe_table(table_name) to confirm column names and data types.
3) Use search_tables(keyword) to locate relevant tables/columns.
4) When writing SQL for query_data(sql), ALWAYS:
   - Use bind variables (no string concatenation of user input).
   - Prefer LIKE for substring/partial text; reserve '=' for explicit exact IDs (numeric ID, UUID, exact code).
   - Make string filters case-insensitive (UPPER(...) on both sides OR use a case-insensitive NLS_SORT/COMP session if explicitly set).
   - Normalize Unicode spaces/dashes and collapse whitespace before filtering.
   - Escape '%' and '_' in user terms and specify an ESCAPE character.

Identifier casing (Oracle):
- Unquoted identifiers are stored UPPERCASE and are case-insensitive.
- Case-sensitive identifiers only exist if created with double quotes; then you MUST reference them with the exact case and quotes.
- Avoid creating/depending on quoted identifiers; if they exist, use "ExactCaseName".

Result limiting and ordering:
- Prefer FETCH FIRST n ROWS ONLY (Oracle 12c+). Example: ... ORDER BY ... FETCH FIRST 20 ROWS ONLY
- If you must use ROWNUM with ORDER BY, wrap the ordered subquery:
    SELECT * FROM (SELECT ... FROM ... ORDER BY ...) WHERE ROWNUM <= :n

TEXT MATCHING POLICY (CRITICAL):
- Default to LIKE for partial text:
    -- contains:
       UPPER({{col_norm}}) LIKE UPPER('%' || :term_esc || '%') ESCAPE '\\'
    -- starts with:
       UPPER({{col_norm}}) LIKE UPPER(:term_esc || '%') ESCAPE '\\'
    -- ends with:
       UPPER({{col_norm}}) LIKE UPPER('%' || :term_esc) ESCAPE '\\'
- Exact '=' ONLY for explicit exact-match requests or true unique identifiers.

LIKE wildcard escaping (bind-side):
- Always escape user wildcards inside SQL using bind operations:
    -- :term_esc := REPLACE(REPLACE(:raw_term, '%', '\\%'), '_', '\\_')
  Then use ESCAPE '\\' in the predicate.

Unicode & punctuation normalization (use in predicates or via function-based index):
- Define a normalized expression per filtered column to survive NBSPs, narrow NBSPs, and fancy dashes, and to collapse whitespace:
    -- {{col_norm}} :=
       REGEXP_REPLACE(
         REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(col,
           CHR(160),' '),            -- NBSP U+00A0
           UNISTR('\\202F'),' '),    -- narrow NBSP U+202F
           UNISTR('\\2011'),'-'),    -- non-breaking hyphen
           UNISTR('\\2013'),'-'),    -- en dash
           UNISTR('\\2014'),'-'      -- em dash
         ),
         '\\s+', ' '                 -- collapse whitespace
       )
- Always apply LIKE to {{col_norm}}, not the raw column.

Common field normalization patterns:
- Treat 'None'/'N/A'/'' as NULL: NULLIF(TRIM({col}), 'None')
- Booleans (e.g., 'Yes, (HLC [...])'):
    CASE
      WHEN REGEXP_LIKE(UPPER(flag), '^\\s*Y(ES)?\\b') THEN 1
      WHEN REGEXP_LIKE(UPPER(flag), '^\\s*N(O)?\\b')  THEN 0
      ELSE NULL
    END
- Numeric price from '$250 ':
    TO_NUMBER(REGEXP_SUBSTR(price_col, '[0-9]+(\\.[0-9]+)?'))
- Hours/CEUs from '~4–6 hours (1 CEU)':
    -- low hours:  REGEXP_SUBSTR(dur_col, '([0-9]+(\\.[0-9]+)?)', 1, 1, NULL, 1)
    -- high hours: REGEXP_SUBSTR(dur_col, '([0-9]+(\\.[0-9]+)?)', 1, 2, NULL, 1)
    -- CEUs:       REGEXP_SUBSTR(dur_col, '([0-9]+(\\.[0-9]+)?)\\s*CEU', 1, 1, NULL, 1)

Zero-results recovery:
1) Re-check table/column names & data types via describe_table().
2) Switch '=' to LIKE over {{col_norm}} with case-insensitivity and escaped term.
3) Search across multiple plausible columns (institution, campus, state, title, roles).
4) Sample rows with FETCH FIRST n ROWS ONLY to validate coverage and spot formatting anomalies.
5) If still empty, broaden terms, verify hidden NBSP/dash issues, and consider full-text (Oracle Text).

Performance & indexing (Oracle):
- Prefer "starts with" patterns (no leading '%') to enable index usage.
- Create function-based indexes on UPPER({{col_norm}}) when frequent text filtering is expected.
- Consider Oracle Text (CONTEXT/CTXCAT) and CONTAINS(...) for multi-word or relevance-ranked search.
- Use EXPLAIN PLAN / DBMS_XPLAN to confirm index usage.

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
    print("Starting Oracle server...")
    # Initialize and run the server
    mcp.run(transport="stdio")