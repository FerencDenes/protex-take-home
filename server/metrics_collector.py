import paho.mqtt.client as mqtt
import ssl
import json
import time
from db_manager import DatabaseManager

# TODO make conf
AWS_IOT_ENDPOINT = "a3j514h4zjsng3-ats.iot.eu-north-1.amazonaws.com"
PORT = 8883
TOPIC = "devices/+/monitoring"

# TODO centralise
CA_PATH = "../certs/root-CA.crt"
CERT_PATH = "../certs/edge_device_01.cert.pem"
KEY_PATH = "../certs/edge_device_01.private.key"

db: DatabaseManager
def on_connect(client, userdata, flags, rc, properties=None):
    client.subscribe(TOPIC)
    print(f"Subscribed to {TOPIC}")

def construct_metric_key(prefix, key):
    if prefix == "":
        return key
    else:
        return prefix + "-" + key

def handle_metric(timestamp, device_id, metric_prefix, metric_value):
    if isinstance(metric_value, dict):
        for metric_key in metric_value:
            handle_metric(
                timestamp,
                device_id,
                construct_metric_key(metric_prefix, metric_key),
                metric_value[metric_key])
    elif isinstance(metric_value, list):
        for index in range(len(metric_key)):
            handle_metric(
                timestamp,
                device_id,
                construct_metric_key(metric_prefix, index),
                metric_value[index]
            )
    else:
        key = metric_prefix
        print(f"Metric {key}, {metric_value}")
        db.add_metric(timestamp, device_id, key, metric_value)

def process_message(message):
    timestamp = int(message["timestamp"])
    device_id = message["device"]
    handle_metric(timestamp, device_id, "", message["metrics"])

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        print(f"Topic: {msg.topic}")
        print(f"Message: {json.dumps(payload, indent=2)}")
        process_message(payload)
    except json.JSONDecodeError as e:
        print(f"Error decoding message: {e}")

def on_log(client, userdata, level, buf):
    print(f"MQTT Log: {buf}")

def create_client():
    client = mqtt.Client(
        protocol=mqtt.MQTTv5,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2
    )

    client.tls_set(
        ca_certs=CA_PATH,
        certfile=CERT_PATH,
        keyfile=KEY_PATH,
        tls_version=ssl.PROTOCOL_TLSv1_2
    )

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_log = on_log
    return client

def collect_metrics():
    client = create_client()
    try:
        print("Connecting to AWS IoT...")
        client.connect(AWS_IOT_ENDPOINT, PORT, keepalive=60)
        print("Starting MQTT loop...")
        client.loop_forever()
    except Exception as e:
        print(f"Error occurred: {str(e)}")
    finally:
        print("Disconnecting...")
        client.disconnect()

def collect_metrics_manager():
    while True:
        try:
            global db
            db = DatabaseManager()
            collect_metrics()
        except Exception as e:
            print(f"Metrics collector exited with {e}")
            time.sleep(5)

if __name__ == "__main__":
    collect_metrics_manager()