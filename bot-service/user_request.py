""" 
This file create JSON requests from User BOT data, save it in DB and send it to Kafka topic for further processing
"""
import json
import common_utils.kafka_common as kfk
from common_utils.kafka_producer import send_request_to_queue
from common_utils.utils import UserRequestFieldNames

save_requests = False

def process_user_request(user_request):
    # Convert to pretty JSON
    pretty_json = json.dumps(user_request, indent=4, ensure_ascii=False)

    # Save to a local file
    if save_requests:
        origin = user_request[UserRequestFieldNames.ORIGIN.value]
        destination = user_request[UserRequestFieldNames.DESTINATION.value]
        file_name = f"route_request_{origin}_{destination}.json"
        with open(file_name, "w", encoding="utf-8") as json_file:
            json_file.write(pretty_json)
        
    send_request_to_queue(pretty_json, kfk.USER_REQUESTS_TOPIC_NAME)
