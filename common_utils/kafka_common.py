import os

# Kafka broker (Change 'your-ec2-public-ip' to your actual EC2 public IP or hostname)
KAFKA_BROKER_HOST = os.getenv('KAFKA_BROKER_HOST')
if not KAFKA_BROKER_HOST:
    raise ValueError("KAFKA_BROKER found!")
KAFKA_BROKER_PORT = os.getenv('KAFKA_BROKER_PORT')

KAFKA_BROKER = f"{KAFKA_BROKER_HOST}:{KAFKA_BROKER_PORT}"


# Topics names
USER_REQUESTS_TOPIC_NAME = "user-requests-queue-v1"
TRANSFORMER_TOPIC_NAME = "intermediate_queue_v1"
RESULTS_TOPIC_NAME = "results_queue_v1"
