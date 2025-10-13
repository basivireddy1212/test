Here’s a simple **AWS Lambda Python example** that connects to a **PostgreSQL** database (for example, on Amazon RDS or Aurora).

---

### ✅ **1. Lambda Function Example**

```python
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
```

---

### ✅ **2. Lambda Environment Variables**

Add these environment variables in your Lambda configuration:

```
DB_HOST=<your-database-endpoint>
DB_NAME=<database-name>
DB_USER=<username>
DB_PASSWORD=<password>
DB_PORT=5432
```

---

### ✅ **3. Packaging psycopg2**

The built-in Lambda environment doesn’t include `psycopg2`.
You must **deploy it with your code** or use a **Lambda Layer**.

**Option 1 — Use Layer (recommended):**
Use the prebuilt `psycopg2` Lambda Layer (compiled for Amazon Linux):

```bash
arn:aws:lambda:<region>:898466741470:layer:psycopg2-py311:1
```

(Use the ARN matching your Python version & region)

**Option 2 — Package manually:**
On an Amazon Linux machine or Docker:

```bash
mkdir package
cd package
pip install psycopg2-binary -t .
zip -r ../function.zip .
cd ..
zip -g function.zip lambda_function.py
```

Then upload `function.zip` to Lambda.

---

### ✅ **4. IAM & Networking**

* **VPC:** If your DB is in a private subnet, make sure your Lambda function runs in the same VPC and subnets with correct security groups.
* **Security Group:** Allow inbound connections from Lambda SG to Postgres port (default `5432`).

---

Would you like me to show how to **connect using SQLAlchemy** instead (for easier ORM queries)?
