from flask import Flask, request, g
from flask_cors import CORS
from db_manager import DatabaseManager
import time

http_server = Flask(__name__)
CORS(http_server)

def get_db():
    if "db" not in g:
        g.db = DatabaseManager()
    return g.db

@http_server.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        try:
            db.close()
        except Exception:
            pass

@http_server.get("/api/v1/devices")
def devices_list():
    try:
        limit = request.args.get("limit", 50, type=int)
        offset = request.args.get("offset", 0, type=int)
        db = get_db()
        devices = g.db.get_devices(limit=limit, offset=offset)
        return devices, 200, {"Content-Type": "application/json"}
    except Exception as e:
        return {"error": str(e)}, 500, {"Content-Type": "application/json"}


@http_server.get("/api/v1/devices/<device_id>/metrics/<metric_key>/timeseries")
def metric_values(device_id, metric_key):
    try:
        replaced_metric_key = metric_key.replace("_-_", "/")
        limit = request.args.get("limit", 50, type=int)
        offset = request.args.get("offset", 0, type=int)
        default_offset = 24 * 60 * 60
        from_ts = request.args.get("from_ts", int(time.time()) - default_offset, type=int)
        db = get_db()
        metric_values = db.get_metrics(device_id=device_id, from_ts=from_ts, metric_key=replaced_metric_key, limit=limit, offset=offset)
        return metric_values, 200, {"Content-Type": "application/json"}
    except Exception as e:
        return {"error": str(e)}, 500, {"Content-Type": "application/json"}

@http_server.get("/api/v1/devices/<device_id>/metrics/latest")
def latest_device_metrics(device_id):
    try:
        limit = request.args.get("limit", 50, type=int)
        offset = request.args.get("offset", 0, type=int)
        db = get_db()
        metric_values = db.get_latest_for_device(device_id=device_id,  limit=limit, offset=offset)
        return metric_values, 200, {"Content-Type": "application/json"}
    except Exception as e:
        print(e)
        return {"error": str(e)}, 500, {"Content-Type": "application/json"}
    
@http_server.get("/api/v1/devices/<device_id>/metrics")
def metric_list(device_id):
    try:
        limit = request.args.get("limit", 50, type=int)
        offset = request.args.get("offset", 0, type=int)
        db = get_db()
        metric_names = db.get_metric_names(device_id=device_id, limit=limit, offset=offset)
        return metric_names, 200, {"Content-Type": "application/json"}
    except Exception as e:
        return {"error": str(e)}, 500, {"Content-Type": "application/json"}
    
def run_http_server():
    http_server.run(host="0.0.0.0", port=8000)

if __name__ == "__main__":
    run_http_server()