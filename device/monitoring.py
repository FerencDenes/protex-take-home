import psutil
import paho.mqtt.client as mqtt
import ssl
import json
import time
import threading
import pynvml
from scheduler import Scheduler
import datetime
import os
from pathlib import Path

# Configuration
AWS_IOT_ENDPOINT = os.getenv("AWS_IOT_ENDPOINT", "a3j514h4zjsng3-ats.iot.eu-north-1.amazonaws.com")
PORT = int(os.getenv("AWS_IOT_PORT", "8883"))
CLIENT_ID = os.getenv("CLIENT_ID")
TOPIC = f"devices/{CLIENT_ID}/monitoring"

REPO_ROOT = Path(__file__).resolve().parents[1]
CERTS_DIR = Path(os.getenv("CERTS_DIR", REPO_ROOT / "certs"))
CA_PATH = os.getenv("AWS_IOT_CA_PATH", str(CERTS_DIR / "root-CA.crt"))
CERT_PATH = os.getenv("AWS_IOT_CERT_PATH", str(CERTS_DIR / "edge_device_01.cert.pem"))
KEY_PATH = os.getenv("AWS_IOT_KEY_PATH", str(CERTS_DIR / "edge_device_01.private.key"))

METRICS_INTERVAL_SECONDS = int(os.getenv("METRICS_INTERVAL_SECONDS", "15"))

def collect_metrics():
    try:
        payload = {}
        payload["cpuUsage"] = psutil.cpu_percent(percpu=False, interval=1.0)
        
        payload["diskUsage"] = {partition.mountpoint: psutil.disk_usage(partition.mountpoint).percent 
                    for partition in psutil.disk_partitions(all=False)}
        payload["diskUsage"]["/"] = psutil.disk_usage("/").percent
        memory_data = psutil.virtual_memory()
        payload["uptime"] = time.time() - psutil.boot_time()
        payload["memoryUsage"] = memory_data.percent

        try:
            pynvml.nvmlInit()
            handleNum = pynvml.nvmlDeviceGetCount()
            gpu_usages = []
            for deviceNum in range(handleNum):
                handle = pynvml.nvmlDeviceGetHandleByIndex(deviceNum)
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                gpu_usages.append({
                    "gpu_utilization": util.gpu,
                    "memory_utilization": util.memory,
                    "temperature": temperature,
                })
            pynvml.nvmlShutdown()
            payload["gpu_usages"] = gpu_usages
        except Exception as e:
            print(f"Failed to collect GPU stats, possibly no GPUs {e}")
    except Exception as e:
        print(f"Failed to collect metrics {e}")
    return payload

connected_flag = threading.Event()
def on_connect(client, userdata, flags, reason_code, properties=None):
    if mqtt.convert_connack_rc_to_reason_code(reason_code) == 0:
        connected_flag.set()
    else:
        print(f"Failed to connect. Reason code: {reason_code}")

def on_log(client, userdata, level, buf):
    print(f"MQTT Log: {buf}")

def create_client():
    client = mqtt.Client(
        client_id=CLIENT_ID,
        protocol=mqtt.MQTTv5,
        callback_api_version=mqtt.CallbackAPIVersion.VERSION2
        )
    client.on_connect = on_connect
    client.on_log = on_log

    client.tls_set(
        ca_certs=CA_PATH,
        certfile=CERT_PATH,
        keyfile=KEY_PATH,
        tls_version=ssl.PROTOCOL_TLSv1_2
    )
    return client

def send_metrics(client: mqtt.Client, metrics):
    try:
        print("Connecting to AWS IoT...")
        global connected_flag
        connected_flag.clear()
        client.connect(AWS_IOT_ENDPOINT, PORT, keepalive=60)
        client.loop_start()

        if not connected_flag.wait(timeout=10):
            raise RuntimeError("Failed to connect within timeout period")

        payload = {
            "metrics": metrics,
            "timestamp": int(time.time()),
            "device": CLIENT_ID,
        }
        payload_json = json.dumps(payload)
        
        result = client.publish(TOPIC, payload_json, qos=1)
        if not result.is_published():
            result.wait_for_publish(timeout=5)
        print("Message successfully published")

    except Exception as e:
        print(f"Error occurred: {str(e)}")
    finally:
        client.loop_stop()
        client.disconnect()

def report(client: mqtt.Client):
    metrics = collect_metrics()
    send_metrics(client, metrics)

def main():
    client = create_client()
    schedule = Scheduler()
    schedule.cyclic(datetime.timedelta(seconds=METRICS_INTERVAL_SECONDS), lambda: report(client))
    while True:
        schedule.exec_jobs()
        time.sleep(1)

if __name__ == "__main__":
    if not CLIENT_ID:
        raise RuntimeError("CLIENT_ID environment variable is required")
    main()
