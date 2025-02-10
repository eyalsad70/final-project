
from kafka import KafkaConsumer
import json
import os
from common_utils.local_logger import logger
import common_utils.kafka_common as kfk
import message_handler

KAFKA_BROKER_HOST = os.getenv('KAFKA_BROKER_HOST')
if not KAFKA_BROKER_HOST:
    raise ValueError("KAFKA_BROKER found!")
KAFKA_BROKER_PORT = os.getenv('KAFKA_BROKER_PORT')

KAFKA_BROKER = f"{KAFKA_BROKER_HOST}:{KAFKA_BROKER_PORT}"


def poll_messages():
    # Create Kafka Consumer
    consumer = KafkaConsumer(
        kfk.USER_REQUESTS_TOPIC_NAME,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="json-consumer-group"
    )

    logger.info(f"Listening on topic {kfk.USER_REQUESTS_TOPIC_NAME} for messages...")

    for message in consumer:
        #print(f"Received: {message.value}")
        data = json.loads(message.value)
        message_handler.process_message(data)
