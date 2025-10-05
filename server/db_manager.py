import sqlite3

DB_PATH = "/tmp/metrics.db"

class DatabaseManager:
    def __init__(self):
        self.db_path = DB_PATH
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_tables()

    def _connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
    
    def _create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                timestamp INTEGER,
                device_id TEXT,
                metric_key TEXT,
                metric_value REAL,
                PRIMARY KEY (timestamp, device_id, metric_key)
            )
        ''')
        self.cursor.execute("CREATE INDEX IF NOT EXISTS metrics_devices ON metrics (device_id)")
        self.conn.commit()
    
    def add_metric(self, timestamp: int, device_id: str, key: str, value: float):
        try:
            self.cursor.execute(
                "INSERT INTO metrics VALUES (?, ?, ?, ?)",
                (timestamp, device_id, key, value)
            )
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            self._connect()
    def get_devices(self, limit=50, offset=0):
        devices = self.cursor.execute(
                'SELECT DISTINCT device_id FROM metrics LIMIT ? OFFSET ?',
                (limit, offset)
            ).fetchall()
        return {'devices': [device[0] for device in devices]}
    def get_metric_names(self, device_id, limit=50, offset=0):
        metric_names = self.cursor.execute(
                'SELECT DISTINCT metric_key FROM metrics WHERE device_id = ? LIMIT ? OFFSET ?',
                (device_id, limit, offset)
            ).fetchall()
        return {'metric_names': [metric_name[0] for metric_name in metric_names]}
    def get_metrics(self, device_id, metric_key, from_ts=0, limit=100, offset=0):
        metric_values = self.cursor.execute(
            'SELECT timestamp, metric_value FROM metrics WHERE device_id = ? AND metric_key = ? AND timestamp >= ? ORDER BY timestamp DESC LIMIT ? OFFSET ?',
            (device_id, metric_key, from_ts, limit, offset)
        ).fetchall()
        return {'metric_values': [(metric_value[0], metric_value[1]) for metric_value in metric_values]}
    def get_latest_for_device(self, device_id, limit = 50, offset = 0):        
        metrics = self.cursor.execute(
            'SELECT metric_key, metric_value, timestamp FROM metrics WHERE device_id = ? and timestamp = (SELECT max(timestamp) FROM metrics WHERE device_id = ?) LIMIT ? OFFSET ?',
            (device_id, device_id, limit, offset)
            ).fetchall()
        if (len(metrics) == 0):
             return {}
        else:
            timestamp = metrics[0][2]
            return {'timestamp': timestamp, 'metrics': { metric[0]: metric[1] for metric in metrics}}

    def close(self):
        if self.conn:
            try:
                self.conn.close()
            except sqlite3.Error as e:
                print(f"Database close error: {e}")

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
