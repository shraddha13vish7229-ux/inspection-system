# User Manual

## Assembly Instructions

### Step 1: Frame Construction
- Assemble the 2020 aluminum extrusion frame to dimensions 800mm (L) x 200mm (W) x 300mm (H).
- Install timing belt pulleys at both ends and thread the GT2 belt through the carriage.
- Mount the NEMA 17 stepper motor to the drive pulley end.

### Step 2: Camera and Lighting
- Mount the LED ring light centrally above the belt path at 250mm working distance.
- Mount the USB camera coaxially with the ring light, ensuring the belt centerline bisects the frame.
- Connect camera to Jetson Nano USB 3.0 port.

### Step 3: Sensor Installation
- Install the photogate emitter and receiver across the belt, 150mm upstream of the camera focal plane.
- Align emitter and receiver so the IR beam crosses perpendicular to belt travel.
- Connect photogate output to Arduino Pin 6.

### Step 4: Diverter Mechanism
- Mount the solenoid pusher perpendicular to belt travel, 300mm downstream of the camera.
- Position the quarantine bin immediately adjacent to the pusher exit trajectory.
- Wire solenoid through NPN transistor (TIP120) to Arduino Pin 5.
- Install 1N4007 flyback diode across solenoid coil.

### Step 5: Controller Setup
- Mount Arduino Uno near the stepper driver.
- Connect A4988 driver to stepper motor and Arduino Pins 2, 3, 4.
- Mount Jetson Nano in ventilated enclosure beneath the frame.
- Connect Jetson to Arduino via USB cable.

### Step 6: Power and Safety
- Connect 12V SMPS to mains through IEC socket with fuse.
- Route 12V to A4988 VMOT and LM2596 input.
- Route 5V output to Arduino Vin and Jetson barrel jack.
- Install emergency stop button on accessible panel, wired to Arduino Pin 7.

## Software Setup

### Jetson Nano
1. Flash JetPack 5.1 to microSD card using NVIDIA SDK Manager.
2. Complete initial setup (user, WiFi, etc.).
3. Update packages: `sudo apt update && sudo apt upgrade -y`
4. Install Python dependencies:
   ```bash
   pip3 install torch torchvision opencv-python pyserial flask flask-socketio paho-mqtt numpy pillow scikit-learn matplotlib seaborn
   ```
5. Install TensorRT (included in JetPack).

### Arduino
1. Open Arduino IDE.
2. Open `src/arduino/belt_controller.ino`.
3. Select **Tools > Board > Arduino Uno**.
4. Select correct COM port.
5. Click **Upload**.

### Model Training (if not using pretrained)
1. Prepare dataset in `data/processed/` with subfolders: `conforming`, `absent`, `fracture`, `dimension`, `color`.
2. Run augmentation:
   ```bash
   python3 src/python/augment.py --input data/raw --output data/processed --num-aug 5
   ```
3. Train model:
   ```bash
   python3 src/python/train.py --dataset data/processed --epochs 50 --output model.pth
   ```
4. Export to TensorRT:
   ```bash
   python3 src/python/export_trt.py --weights model.pth --output model.trt --fp16
   ```

## Operating Instructions

### Startup Sequence
1. Apply 12V power to SMPS.
2. Wait for Jetson to boot (green LED solid).
3. Verify Arduino sends `CONTROLLER_READY` over serial.
4. Launch inference engine:
   ```bash
   python3 src/python/inspection_engine.py --engine model.trt --port /dev/ttyACM0
   ```
5. Launch dashboard (in new terminal):
   ```bash
   python3 src/python/dashboard.py
   ```
6. Open browser to `http://jetson-ip:5000`.

### Calibration
1. Place a known conforming article on the belt.
2. Verify photogate triggers (Arduino sends `GATE:<timestamp>`).
3. Verify camera captures clear, focused image.
4. Adjust LED ring brightness if reflections are visible.
5. Adjust solenoid timing if diverter misses articles.

### Production Operation
1. Load articles onto belt infeed.
2. Start belt via dashboard or send `START` command.
3. Monitor dashboard for real-time metrics.
4. System auto-classifies and diverts defective units.

### Emergency Procedures
- **Press red Emergency Stop button** at any time.
- Belt halts immediately; solenoid de-energizes.
- Fault LED turns red.
- To resume: release E-stop, send `START` command.

## Troubleshooting

| Problem | Possible Cause | Solution |
|---------|---------------|----------|
| Belt not moving | Stepper disabled | Check ENABLE pin; verify Arduino powered |
| Camera not detected | USB bandwidth issue | Try different USB port; check `ls /dev/video*` |
| High false reject rate | Threshold too sensitive | Adjust confidence threshold in `inspection_engine.py` |
| Solenoid not firing | Transistor failure | Check TIP120 wiring; verify flyback diode |
| Serial communication errors | Ground loop | Use USB isolator; verify common ground |
| Slow inference | TensorRT not loaded | Verify `.trt` file exists; check GPU memory |
| Dashboard not updating | MQTT not running | Install and start Mosquitto: `sudo apt install mosquitto` |

## Maintenance
- Clean camera lens daily to remove dust.
- Check photogate alignment weekly.
- Verify solenoid force monthly (should push 500g test weight).
- Calibrate belt speed if articles drift on belt.
- Backup model weights and logs weekly.
