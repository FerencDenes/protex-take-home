# DESIGN.md

This document summarizes the architecture, trade-offs, scaling approach, and security considerations for the Edge Device Hardware Monitoring prototype.

Architecture overview

- Device agent (Python)

  - Periodically collects host metrics (CPU, RAM, Disk, optional GPU via NVML) using psutil/pynvml.

  - Publishes a JSON payload over MQTT to AWS IoT Core on topic devices/<CLIENT_ID>/monitoring using mutual TLS.

- Server (Python)

  - MQTT collector subscribes to devices/+/monitoring.

  - Flattens nested JSON metrics into dash-separated keys and writes rows into SQLite (timestamp, device_id, metric_key, metric_value).

  - HTTP API (Flask) exposes read-only endpoints used by the UI: list devices, list metrics, latest snapshot, and time series queries.

- Frontend (React + Vite)

  - Simple UI to select a device and metric, view latest snapshot and time series.

Key trade-offs

- Transport: MQTT over AWS IoT Core vs. HTTP push or S3 writes

  - Chosen MQTT for bidirectional, lightweight pub/sub, easy device ID scoping, built-in mutual TLS, and compatibility with Greengrass/IoT Core. HTTP push would be simpler to demo but less aligned with the edge fleet control plane used in production.

- Storage: SQLite for prototype

  - Chosen for zero-ops local persistence and easy querying. In production, a managed time-series or relational store would be used behind the server/API.

- Data model: Flattened key space

  - Simpler ingestion and querying for a heterogeneous set of metrics without schema migrations. The trade-off is looser typing and fewer constraints; the API can later evolve to typed projections per metric.

Scaling across thousands of devices

- Ingestion fan-in

  - Use AWS IoT Core rules to route MQTT messages to a scalable backend (Kinesis/Data Streams or SQS) for serverless consumers that persist into a central database. The current SQLite-based collector is suitable for local dev; at scale, replace with a stateless consumer and a remote DB.

- Query/API

  - Frontend API should query a centralized store with proper indexes/partitioning (by device_id and time). Add pagination and server-side downsampling for time series.

- Fleet management

  - Devices authenticate via X.509 certificates, managed/rotated by AWS IoT. Configuration (publish interval, metric set, alert thresholds) is distributed via Greengrass components or IoT Jobs/Shadow.

Security considerations

- Mutual TLS for device → cloud using X.509 certificates (no long-lived secrets on device). Cert/key paths are configurable via environment variables and not embedded in the code.

- Principle of least privilege: MQTT publish policy limited to devices/<CLIENT_ID>/\* topics for each device certificate.

- Data exposure: Payload is metrics-only; avoid including PII. Ensure API enforces CORS appropriately and is read-only.

- Hardening: For production, enable message signing, implement payload validation schemas, and add rate limiting/DoS protection at the API gateway.

Operations and reliability

- Device agent

  - Non-blocking periodic reporting using a scheduler; metrics collection is lightweight and bounded. Errors are logged and publishing retries occur on reconnect.

- Server

  - WAL mode enabled for SQLite to improve concurrent read/write during local dev. API closes DB connections per request to avoid leaks. Structured logging aids troubleshooting.

Extensibility

- Add local alerting (e.g., CPU > 90% logs a warning) within the device agent. Integrations (Slack webhook) can be hung off a periodic summary job.

- Add a Greengrass component recipe to package and deploy the device agent; add a Dockerfile for containerized deployment on edge devices if desired.
