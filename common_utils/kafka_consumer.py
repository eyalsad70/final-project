
from kafka import KafkaConsumer
import json
import os
import signal
import sys
from common_utils.local_logger import logger
import common_utils.kafka_common as kfk

KAFKA_BROKER_HOST = os.getenv('KAFKA_BROKER_HOST')
if not KAFKA_BROKER_HOST:
    raise ValueError("KAFKA_BROKER found!")
KAFKA_BROKER_PORT = os.getenv('KAFKA_BROKER_PORT')

KAFKA_BROKER = f"{KAFKA_BROKER_HOST}:{KAFKA_BROKER_PORT}"

#default_offset = 'earliest'
default_offset = 'latest'

def poll_and_process_messages(topic_name, data_handler_func):
    # Create Kafka Consumer
    consumer = KafkaConsumer(
        topic_name,
        bootstrap_servers=KAFKA_BROKER,
        value_deserializer=lambda x: json.loads(x.decode("utf-8")),
        auto_offset_reset=default_offset,
        enable_auto_commit=True,
        group_id="json-consumer-group"
    )

    logger.info(f"Listening on topic {topic_name} for messages...")

    for message in consumer:
        #print(f"Received: {message.value}")
        data = json.loads(message.value)
        data_handler_func(data)
