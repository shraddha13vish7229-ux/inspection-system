# Unit Test Procedures

## Test 1: Camera Frame Capture
**Objective**: Verify camera acquisition at target resolution and framerate.
**Setup**: Connect camera to Jetson USB 3.0 port.
**Procedure**:
1. Run `python3 -c "import cv2; cap=cv2.VideoCapture(0); print(cap.read()[1].shape)"`
2. Verify output is (480, 640, 3) or higher.
3. Run for 60 seconds and count frames.
**Pass Criteria**: ≥ 25 FPS sustained; no dropped frames.

## Test 2: Photogate Response
**Objective**: Verify trigger timing and reliability.
**Setup**: Connect photogate to Arduino Pin 6; open Serial Monitor.
**Procedure**:
1. Pass a cardboard sheet through the beam 10 times.
2. Record timestamps from `GATE:<ms>` messages.
**Pass Criteria**: All 10 passes detected; timestamp jitter < 5ms.

## Test 3: Stepper Velocity Stability
**Objective**: Verify constant belt speed.
**Setup**: Mark belt with tape; measure distance over time.
**Procedure**:
1. Start belt with `START` command.
2. Measure time for tape to travel 500mm.
3. Repeat 5 times.
**Pass Criteria**: Travel time consistent within ±5%; no missed steps.

## Test 4: Solenoid Force and Timing
**Objective**: Verify pusher can divert 500g article.
**Setup**: Place 500g test weight on belt at photogate position.
**Procedure**:
1. Send `REJECT:test` command.
2. Measure time from command to solenoid activation.
3. Verify weight is pushed into quarantine bin.
**Pass Criteria**: Activation within 900ms of photogate; weight clears belt.

## Test 5: TensorRT Inference Latency
**Objective**: Verify model meets real-time requirements.
**Setup**: Load `model.trt` on Jetson Nano.
**Procedure**:
1. Run `inspection_engine.py` with `--engine model.trt`.
2. Process 100 frames and log latencies.
**Pass Criteria**: Mean latency < 50ms; 95th percentile < 80ms.

## Test 6: Emergency Stop
**Objective**: Verify hardware interrupt functionality.
**Setup**: Belt running at production speed.
**Procedure**:
1. Press E-stop button.
2. Measure time from press to belt halt.
3. Verify solenoid is de-energized.
4. Release button and send `START`.
**Pass Criteria**: Halt within 100ms; system resumes normally.

## Test 7: Serial Protocol
**Objective**: Verify Arduino-Jetson command exchange.
**Setup**: Arduino connected to Jetson via USB.
**Procedure**:
1. Send `START` → expect `ACK:START`.
2. Send `STOP` → expect `ACK:STOP`.
3. Trigger photogate → expect `GATE:<timestamp>`.
4. Send `REJECT:fracture` → expect `LOG:REJECT:fracture`.
**Pass Criteria**: All commands acknowledged within 100ms.

## Test 8: Dashboard Connectivity
**Objective**: Verify web dashboard receives MQTT updates.
**Setup**: Mosquitto broker running; dashboard launched.
**Procedure**:
1. Open browser to `http://jetson-ip:5000`.
2. Publish test message: `mosquitto_pub -t inspection/log -m "LOG:fracture,0.92"`.
3. Verify dashboard updates counters and defect log.
**Pass Criteria**: Dashboard reflects published data within 2 seconds.
