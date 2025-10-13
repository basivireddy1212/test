import os
import psycopg2
import boto3
import json

def lambda_handler(event, context):
    # Database connection details
    db_host = os.environ['DB_HOST']
    db_name = os.environ['DB_NAME']
    db_user = os.environ['DB_USER']
    db_password = os.environ['DB_PASSWORD']
    db_port = os.environ.get('DB_PORT', '5432')
    sqs_url = os.environ['SQS_URL']

    sqs_client = boto3.client('sqs')
    status_message = {}

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
        version = cur.fetchone()[0]


        # Build success message
        status_message = {
            "status": "success",
            "message": f"Connected to PostgreSQL successfully: {version}"
        }

        # Close connection
        cur.close()
        conn.close()

        return {
            'statusCode': 200,
            'body': f"Connected successfully: {record}"
        }

    except Exception as e:
        status_message = {
            "status": "error",
            "message": str(e)
        }
        return {
            'statusCode': 500,
            'body': f"Error: {str(e)}"
        }
    
    # Send message to SQS
    try:
        sqs_client.send_message(
            QueueUrl=sqs_url,
            MessageBody=json.dumps(status_message)
        )
    except Exception as sqs_err:
        return {
            'statusCode': 500,
            'body': f"Failed to send message to SQS: {sqs_err}"
        }

    return {
            'statusCode': 200,
            'body': json.dumps(status_message)
        }