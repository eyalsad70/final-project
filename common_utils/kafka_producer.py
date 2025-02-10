from kafka import KafkaProducer
import json
import os
from common_utils.local_logger import logger
from common_utils import kafka_common

# Create Kafka Producer
try:
    producer = KafkaProducer(
        bootstrap_servers=kafka_common.KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode("utf-8")  # Convert JSON to bytes
    )
except:
    producer = None
    logger.error("ERROR!!! Kafka Broker NOT Available")


def send_request_to_queue(json_data, topic_name):
    if producer:
        # Send message to Kafka topic
        producer.send(topic_name, json_data)
        producer.flush()  # Ensure all messages are sent
        logger.info(f"Message sent successfully to topic {topic_name}")
        return True
    else:
        logger.error("Kafka Producer is NOT available")
        return False

# Close producer
#producer.close()

if __name__ == "__main__":
    # Example JSON message
    message = {
        "user_id": 12345,
        "route_id": 67890,
        "origin": "Tel Aviv",
        "destination": "Haifa",
        "date": "04/02",
        "fueling": "yes",
        "dining": "coffee-break",
        "attractions": "mix"
    }
    send_request_to_queue(message, kafka_common.USER_REQUESTS_TOPIC_NAME)
    producer.close()

