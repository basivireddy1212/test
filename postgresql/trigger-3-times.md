Here’s a clean **example of how to implement retry logic (up to 3 times)** in an **AWS Lambda function triggered by SQS**, using **Python**.

---

### ✅ **Goal**

When the Lambda receives a message from SQS:

* Try processing it.
* If it fails, retry up to 3 times.
* On 3rd failure, send it to a **Dead-Letter Queue (DLQ)** or log it as failed.

---

### **Architecture**

```
SQS Queue → Lambda Function → Retry 3 times → DLQ (optional)
```

---

### **Python Lambda Code**

```python
import json
import boto3
import logging
import os

# Setup logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

sqs = boto3.client('sqs')

# Environment variable for DLQ URL (optional)
DLQ_URL = os.getenv('DLQ_URL', None)

def process_message(message_body):
    """
    Replace this function with your actual message processing logic.
    Raise an exception to simulate failure.
    """
    logger.info(f"Processing message: {message_body}")
    if "fail" in message_body.lower():
        raise Exception("Simulated failure")
    logger.info("Processing successful.")


def lambda_handler(event, context):
    for record in event['Records']:
        message_body = record['body']
        message_attributes = record.get('messageAttributes', {})
        
        # Get retry count
        retry_count = int(message_attributes.get('RetryCount', {}).get('stringValue', '0'))

        try:
            process_message(message_body)

        except Exception as e:
            retry_count += 1
            logger.error(f"Error processing message: {e}. Retry attempt {retry_count}/3")

            if retry_count < 3:
                # Re-send message to SQS with updated retry count
                sqs.send_message(
                    QueueUrl=record['eventSourceARN'].split(':')[-1],  # same queue
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
                # Move to DLQ or log permanently failed message
                if DLQ_URL:
                    sqs.send_message(
                        QueueUrl=DLQ_URL,
                        MessageBody=message_body
                    )
                    logger.warning("Message sent to DLQ after 3 failed attempts")
                else:
                    logger.warning("Message failed after 3 retries, DLQ not configured")

    return {"statusCode": 200, "body": json.dumps("Processed batch")}
```

---

### **Setup Steps**

1. **Create an SQS queue** (e.g., `MainQueue`).
2. (Optional) **Create a DLQ** (e.g., `DLQQueue`) and set its URL in Lambda environment variable:

   ```
   DLQ_URL = https://sqs.<region>.amazonaws.com/<account-id>/DLQQueue
   ```
3. **Attach the Lambda to the SQS queue** as a trigger.
4. Add the following **IAM permissions** to the Lambda’s execution role:

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

### **How It Works**

* The message starts with no retry count.
* On failure:

  * Lambda catches the exception.
  * Increments `RetryCount`.
  * Re-sends message back to SQS with that count.
* After 3 retries, message is either sent to DLQ or logged as failed.

---

### 💡**Alternative (Simpler) Option**

Instead of manual retries, you can also configure:

* **SQS redrive policy** (automatically retries up to `maxReceiveCount`).
* Then sends the message to **DLQ** — no custom retry logic needed.

Example:

```json
{
  "RedrivePolicy": {
    "maxReceiveCount": 3,
    "deadLetterTargetArn": "arn:aws:sqs:region:account-id:DLQQueue"
  }
}
```

This is often simpler and AWS-native, but the above Python version gives you **custom control** (e.g., adding delays, exponential backoff, etc.).

---

Would you like me to modify this version to include **delayed retries** (e.g., 10s, 30s, 60s between attempts)?
