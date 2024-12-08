import psycopg2

# PostgreSQL connection details
pg_host = "localhost"
pg_dbname = "privacydb"
pg_user = "postgres"
pg_password = "postgres"

def clear_postgres_database(pg_host, pg_dbname, pg_user, pg_password):
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=pg_host,
            database=pg_dbname,
            user=pg_user,
            password=pg_password
        )
        conn.autocommit = True  # Allow schema-level changes
        cursor = conn.cursor()

        # Drop the schema and recreate it
        cursor.execute("DROP SCHEMA public CASCADE;")
        cursor.execute("CREATE SCHEMA public;")

        print("PostgreSQL database cleared successfully.")

        # Close connections
        cursor.close()
        conn.close()

    except psycopg2.Error as e:
        print(f"Error: {e}")
        if conn:
            conn.rollback()
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# Run the script
clear_postgres_database(pg_host, pg_dbname, pg_user, pg_password)
