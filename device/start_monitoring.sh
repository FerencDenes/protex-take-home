#!/bin/bash

cd /app
/usr/bin/python3 device/monitoring.py >> /var/log/cron.monitoring.log 2>&1
