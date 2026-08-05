#!/usr/bin/env python3
"""
Real-Time Inspection Dashboard
Framework: Flask + Flask-SocketIO + MQTT
"""

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import paho.mqtt.client as mqtt
import json
import threading
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'warehouse-inspection-secret'
sio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Live metrics
metrics = {
    'total': 0,
    'rejected': 0,
    'accuracy': 0.96,
    'avg_time_ms': 36.0,
    'status': 'ACTIVE',
    'throughput_per_min': 0,
    'defect_log': [],
    'hourly_counts': [0] * 24
}

# MQTT callbacks
def on_connect(client, userdata, flags, rc):
    print(f"[MQTT] Connected with result code {rc}")
    client.subscribe("inspection/log")
    client.subscribe("inspection/status")

def on_message(client, userdata, msg):
    global metrics
    payload = msg.payload.decode()
    topic = msg.topic

    if topic == 'inspection/log':
        if payload.startswith('LOG:'):
            parts = payload.split(':')
            if len(parts) >= 2:
                event_type = parts[1]
                metrics['total'] += 1

                if event_type != 'ACCEPT':
                    metrics['rejected'] += 1
                    defect_entry = {
                        'timestamp': datetime.now().strftime('%H:%M:%S'),
                        'class': event_type,
                        'confidence': float(parts[2]) if len(parts) > 2 else 0.0
                    }
                    metrics['defect_log'].append(defect_entry)
                    # Keep only last 50 entries
                    metrics['defect_log'] = metrics['defect_log'][-50:]

                # Update accuracy
                if metrics['total'] > 0:
                    metrics['accuracy'] = 1.0 - (metrics['rejected'] / metrics['total'])

                # Update hourly count
                hour = datetime.now().hour
                metrics['hourly_counts'][hour] += 1

                # Calculate throughput
                metrics['throughput_per_min'] = metrics['total'] / max(
                    (datetime.now() - start_time).total_seconds() / 60, 1
                )

                sio.emit('update', metrics)

    elif topic == 'inspection/status':
        metrics['status'] = payload
        sio.emit('update', metrics)

# MQTT client setup
mqttc = mqtt.Client()
mqttc.on_connect = on_connect
mqttc.on_message = on_message

try:
    mqttc.connect("localhost", 1883, 60)
    mqttc.loop_start()
    print("[OK] MQTT client connected")
except Exception as e:
    print(f"[WARN] MQTT connection failed: {e}")

start_time = datetime.now()

@app.route('/')
def index():
    return render_template('dashboard.html')

@sio.on('connect')
def handle_connect():
    emit('update', metrics)
    print('[SOCKET] Client connected')

@sio.on('disconnect')
def handle_disconnect():
    print('[SOCKET] Client disconnected')

if __name__ == '__main__':
    print('[INFO] Starting dashboard server on http://0.0.0.0:5000')
    sio.run(app, host='0.0.0.0', port=5000, debug=False)
