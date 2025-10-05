import paho.mqtt.client as mqtt
import ssl
import json
import time
import os
from pathlib import Path
import logging
from db_manager import DatabaseManager

REPO_ROOT = Path(__file__).resolve().parents[1]
CERTS_DIR = Path(os.getenv("CERTS_DIR", REPO_ROOT / "certs"))

AWS_IOT_ENDPOINT = os.getenv("AWS_IOT_ENDPOINT", "a3j514h4zjsng3-ats.iot.eu-north-1.amazonaws.com")
PORT = int(os.getenv("AWS_IOT_PORT", "8883"))
TOPIC = os.getenv("AWS_IOT_TOPIC", "devices/+/monitoring")

CA_PATH = os.getenv("AWS_IOT_CA_PATH", str(CERTS_DIR / "root-CA.crt"))
CERT_PATH = os.getenv("AWS_IOT_CERT_PATH", str(CERTS_DIR / "edge_device_01.cert.pem"))
KEY_PATH = os.getenv("AWS_IOT_KEY_PATH", str(CERTS_DIR / "edge_device_01.private.key"))

db: DatabaseManager
def on_connect(client, userdata, flags, rc, properties=None):
    client.subscribe(TOPIC)
    logging.info(f"Subscribed to {TOPIC}")

def iter_flatten(prefix, value):
    if isinstance(value, dict):
        for k, v in value.items():
            new_prefix = f"{prefix}-{k}" if prefix else k
            yield from iter_flatten(new_prefix, v)
    elif isinstance(value, list):
        for i, v in enumerate(value):
            new_prefix = f"{prefix}-{i}" if prefix else str(i)
            yield from iter_flatten(new_prefix, v)
    else:
        yield (prefix, value)

def process_message(message):
    timestamp = int(message["timestamp"])
    device_id = message["device"]
    metrics = message.get("metrics", {})
    for key, value in iter_flatten("", metrics):
        logging.debug(f"Metric {key} = {value}")
        try:
            db.add_metric(timestamp, device_id, key, float(value))
        except Exception as e:
            logging.error(f"Failed to persist metric {key}: {e}")

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
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