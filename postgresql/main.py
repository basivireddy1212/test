import os
import psycopg2

def lambda_handler(event, context):
    # Database connection details
    db_host = os.environ['DB_HOST']
    db_name = os.environ['DB_NAME']
    db_user = os.environ['DB_USER']
    db_password = os.environ['DB_PASSWORD']
    db_port = os.environ.get('DB_PORT', '5432')

    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=db_host,
            dbname=db_name,
            user=db_user,
            password=db_password,
            port=db_port
        )

        cur = conn.cursor()

        # Example query
        cur.execute("SELECT version();")
        record = cur.fetchone()

        # Close connection
        cur.close()
        conn.close()

        return {
            'statusCode': 200,
            'body': f"Connected successfully: {record}"
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': f"Error: {str(e)}"
        }
