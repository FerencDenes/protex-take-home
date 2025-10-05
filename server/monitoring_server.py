import threading
from metrics_collector import collect_metrics_manager
from metrics_api import run_http_server

if __name__ == '__main__':
    metrics_collector = threading.Thread(target=collect_metrics_manager, daemon=True)
    http_server_thread = threading.Thread(target=run_http_server, daemon=True)
    metrics_collector.start()
    http_server_thread.start()
    try:
        while True:
            metrics_collector.join(timeout=1.0)
            http_server_thread.join(timeout=1.0)
    except Exception as e:
        print(f"Exception in server {e}")
        

