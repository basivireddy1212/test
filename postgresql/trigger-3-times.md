Perfect 👍 — you want **two separate Lambda functions**:

1. **Lambda A → Producer**: Sends messages to an SQS queue.
2. **Lambda B → Consumer**: Triggered by that SQS queue, processes messages (with 3 retry logic).

Below is the full working setup.

---

## 🧩 Architecture

```
Lambda A (Producer) ───▶ SQS Queue ───▶ Lambda B (Consumer)
                                        │
                                        └──▶ Retry (3 times) → DLQ (optional)
```

---

## ✅ 1️⃣ Lambda A — Send messages to SQS

### **Code (lambda_producer.py)**

```python
import json
import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sqs = boto3.client('sqs')
QUEUE_URL = os.getenv('QUEUE_URL')

def lambda_handler(event, context):
    """
    Sends a message to the SQS queue.
    """
    try:
        # Example: message content comes from event or predefined payload
        message_body = event.get('body', 'Test message from producer')
        
        # Send message to SQS
        response = sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=message_body,
            MessageAttributes={
                'RetryCount': {
                    'StringValue': '0',
                    'DataType': 'Number'
                }
            }
        )

        logger.info(f"Message sent to SQS: {response['MessageId']}")
        return {
            'statusCode': 200,
            'body': json.dumps({'messageId': response['MessageId']})
        }

    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        return {'statusCode': 500, 'body': json.dumps('Error sending message')}
```

### **Environment Variables**

* `QUEUE_URL`: your SQS queue URL (e.g. `https://sqs.us-east-1.amazonaws.com/123456789012/MyQueue`)

### **IAM Permissions**

Lambda A needs:

```json
{
  "Effect": "Allow",
  "Action": ["sqs:SendMessage"],
  "Resource": "*"
}
```

---

## ✅ 2️⃣ Lambda B — Process messages with retry logic

### **Code (lambda_consumer.py)**

```python
import json
import boto3
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sqs = boto3.client('sqs')
DLQ_URL = os.getenv('DLQ_URL', None)

def process_message(message_body):
    """
    Replace this function with your business logic.
    Raise an exception to simulate a processing failure.
    """
    logger.info(f"Processing message: {message_body}")
    if "fail" in message_body.lower():
        raise Exception("Simulated failure")
    logger.info("Message processed successfully.")


def lambda_handler(event, context):
    for record in event['Records']:
        message_body = record['body']
        message_attributes = record.get('messageAttributes', {})
        
        retry_count = int(message_attributes.get('RetryCount', {}).get('stringValue', '0'))

        try:
            process_message(message_body)

        except Exception as e:
            retry_count += 1
            logger.error(f"Error: {e}, Retry attempt {retry_count}/3")

            queue_arn = record['eventSourceARN']
            queue_name = queue_arn.split(':')[-1]
            region = queue_arn.split(':')[3]
            account_id = queue_arn.split(':')[4]

            # Build queue URL
            queue_url = f"https://sqs.{region}.amazonaws.com/{account_id}/{queue_name}"

            if retry_count < 3:
                sqs.send_message(
                    QueueUrl=queue_url,
                    MessageBody=message_body,
                    MessageAttributes={
                        'RetryCount': {
                            'StringValue': str(retry_count),
                            'DataType': 'Number'
                        }
                    }
                )
                logger.info(f"Requeued message for retry {retry_count}")
            else:
                if DLQ_URL:
                    sqs.send_message(QueueUrl=DLQ_URL, MessageBody=message_body)
                    logger.warning("Message sent to DLQ after 3 failed attempts")
                else:
                    logger.warning("Message failed after 3 retries, DLQ not configured")

    return {"statusCode": 200, "body": json.dumps("Batch processed")}
```

### **Environment Variables**

* `DLQ_URL` (optional): your Dead Letter Queue URL.

### **IAM Permissions**

Lambda B needs:

```json
{
  "Effect": "Allow",
  "Action": [
    "sqs:SendMessage",
    "sqs:ReceiveMessage",
    "sqs:DeleteMessage",
    "sqs:GetQueueAttributes"
  ],
  "Resource": "*"
}
```

---

## 🚀 Example Flow

1. Invoke **Lambda A** (Producer) manually or via an event:

   ```bash
   aws lambda invoke --function-name LambdaA --payload '{"body":"process this"}' output.json
   ```

2. Message goes to SQS.

3. **Lambda B** (Consumer) automatically triggers.

4. If processing fails, message is retried up to 3 times.

   * After 3rd failure → moves to DLQ (if configured).

---

## 🧠 Optional Enhancement: Delayed Retries

If you want retries after a **delay** (like exponential backoff), you can use:

```python
DelaySeconds = retry_count * 10  # e.g. 10s, 20s, 30s
```

inside the `sqs.send_message()` call.

---

Would you like me to add that **delayed retry version** (10s, 30s, 60s retry intervals)?
