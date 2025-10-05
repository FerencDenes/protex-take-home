# Device Monitoring Tool

There are four components in the system

1. Metric capture and publish on the edge device

2. Data collector on the server side

3. API on the server side

4. Frontend application

<img width="1600" height="900" alt="image" src="https://github.com/user-attachments/assets/3dc9f808-3e01-47c0-be94-b83bacb292eb" />

## Environment

All the below should be started from the project's top level directory.

I have used the certificates, server address from my own AWS IoT Core setup for communication.

In order to run the solution you should have the certifications: https://docs.aws.amazon.com/iot/latest/developerguide/device-certs-create.html

Move the certificates to the `certs` directory with names

- AWS Root certificate: `./certs/root-CA.crt`
- PEM file `./certs/edge_device_01.cert.pem`
- Private key `./certs/edge_device_01.private.key`

These files will be picked up by the devices and the metrics collector.

## Metric capture and publish

Runs in a docker container. This will let us mimic the ubuntu environment easily as well as run several of edge devices. Written in python in the `device` directory.

```bash
docker build -t edge-device -f ./device/Dockerfile.device .
docker run -e CLIENT_ID=<device name> -e AWS_IOT_ENDPOINT=<Your AWS IoT Core address> -d edge-device
```

You can issue multiple `docker run ...` to have multiple edge devices.

You can run it locally as well

```bash
python3 -m venv device/.venv
source ./device/.venv/bin/activate
pip3 install --no-cache-dir -r ./device/requirements.txt
export CLIENT_ID=edge_device_03 && export AWS_IOT_ENDPOINT=<Your AWS IoT Core address> && python3 device/monitoring.py
```

### Communication

Collects data and sends it via MQTT QoS 1 periodically. This ensures scalability and delivery to the broker.

The solution is integrated with AWS IoT Core

## Data collector

Responsible for collecting the metrics from all devices and storing it into the (not sqlite) database.

It can re-use the same certificates which were generated for the Device Monitoring Tool. Also the IoT Core server's address (`AWS_IOT_ENDPOINT`) is now hard coded.

To start

```bash
cd server
python3 -m venv .venv
source ./.venv/bin/activate
pip3 install --no-cache-dir -r ./requirements.txt
python3 metrics_collector.py
```

It now observes _CPU usage_, _disk usage_ (per mount point), _memory usage_, and _GPU data_: utilization, memory utilization, temperature. This list is extensible.

### Internals

It connects the the MQTT server, and subscribes to all device topics. Parses the incoming messages and stores them into the database.

The database is sqlite for the PoC. At startup it creates the table to store the metrics in.

The metrics are parsed recursively (now in practice we have only two levels of metrics)

## Metrics API

Responsible for providing metrics and device data for the frontend via HTTP.

It can

- list devices

- get latest metrics for a device

- list the metrics of a device

- get the timeseries of a metric of a device

Start

```bash
cd server
python3 -m venv .venv
source ./.venv/bin/activate
pip3 install --no-cache-dir -r ./requirements.txt
python3 metrics_api.py
```

### Internals

The server uses the flask webserver (for ease of development). It bootstraps the database (as well as the metrics collector). Reads the data from the database.

The handlers are separated from the db related logic.

## Frontend

Simple React based frontend to demonstrate the functionality in Typescript. It can fetch the list of devices, show the latest metrics of the selected device and display the few latest metric values of the selected measure. The metrics data (the latest as well as the timeseries) is refreshed at a 5 minute interval.

To start for http://localhost:5173/

```bash
cd frontend
npm i
npm run dev
```

### Internals

The refresh is fetched by the client. There is no sync protocol. In case of refresh all the data is fetched again.

# Alternatives considered

## Device communication

- Monitoring tool logs into the devices and fetches data: Not scalable, requires connection management. The edge device should be exposed to the internet.

- Sending data directly tot he monitoring service (HTTP, SNMP, etc): Not too scalable, if the monitoring service is down temporarily, we loose some data. The monitoring tool might not be reachable from the edge device or its location is not static.

- MQTT QoS 0: Fire and forget, does not cater to monitoring service outages

- MQTT QoS 2: Messages can be de-duplicated by the timestamp/device id/metric, so this is an overkill

- MQTT connections are build every time there is a metric. We might reuse the same connection.

## Scheduling of metrics capture

- Used python with scheduler inside. Run it as a daemon, with a supervisor

  - Can handle sub-minute schedules

  - Long running process, might be able to extend to long running MQTT connection

  - More flexible in the long run

- Using cron, knowing the limitation of the minimum one minute granularity

  - Easy to implement, but have an other component to manage

  - Does not prone to failures due to python's failure, or memory leaks

## Security

The devices as well as the monitoring tool use a single key. This might be fine if we can keep it secure.

In reality in a production system each device should have its own key. A key management solution should be necessary.

Also AWS policy is too wide now. In reality the devices should only be able to send to their topic, while the monitoring tool should only subscribe.

The keys are accessible on the edge device. When they are installed on untrusted 3rd party sites they are prone to exploitation. When these are obtained with strict AWS rules they can only shoot themselves into the foot by ruining their own monitoring.

Now the API uses plain HTTP

# Further improvements, limitations

## General

Proper logging

Automated testing

Separation of certificates between devices and the collector server

Picking a DB that is good at storing, handling time series data

Creating proper indices to optimize the database

Scalability: the service should be able to handle 100s of devices
However one might create a topic scheme where the metrics publishing is sharded along with the db. Each device sends their data to the topic of their shard, the data is stored in that shard in the DB. We must make sure that the picked shard remains static. In this case we can have multiple collectors dealing with some shards.

## MMetric capture and publish

GPU not tested.

Device setup. Now I have simply added the certificate to the device manually

Now all the devices send monitoring metrics at once in practice. It would be great to shift with a random delay so we do not overload the network at once from several devices.

## Metrics collection

DB purging (the data keeps growing), there should be a retention period or some kind of compaction of the data

Checking the incoming data's validity

## API

API's business logic is not separated from the handlers.

HTTPS

Authentication for the API and the frontend

## Frontend

Styling, so it looks nice

Pagination is implemented on the API, however the frontend is not able to fetch more pages.

The frontend's metric refresh could be incremental relying on the limit parameters. This would cause less burden on the backend.
