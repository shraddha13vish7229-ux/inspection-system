# Automated Robotic Quality Inspection System

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8%2B-green.svg)](https://www.python.org/)
[![TensorRT](https://img.shields.io/badge/TensorRT-8.5-orange.svg)](https://developer.nvidia.com/tensorrt)
[![Arduino](https://img.shields.io/badge/Arduino-Uno-blue.svg)](https://www.arduino.cc/)

An AI-assisted manufacturing inspection platform that detects defects on products moving along a conveyor belt and automatically sorts defective items using a robotic actuator.

## Features

- **Real-Time Defect Detection**: TensorRT-optimized MobileNetV2 CNN running on NVIDIA Jetson Nano at 28 FPS
- **Five-Class Classification**: Conforming, Absent Constituent, Fracture, Dimensional Deviation, Chromatic Aberration
- **Temporal Consistency**: Sliding-window majority voting reduces sporadic misclassifications by 62%
- **Synchronized Actuation**: Photogate-triggered solenoid pusher diverts defective items with millisecond precision
- **Live Dashboard**: Flask web interface showing throughput, yield rate, and inspection metrics in real time
- **Comprehensive Logging**: Every inspection event logged with timestamp, classification, and confidence score
- **Emergency Stop**: Hardware-level belt halt and actuator disable

## Hardware Requirements

| Component | Model | Quantity |
|-----------|-------|----------|
| Edge Computer | NVIDIA Jetson Nano 4GB | 1 |
| Camera | Logitech C920 HD Pro / USB3 Industrial Camera | 1 |
| Transport Drive | NEMA 17 Stepper + A4988 Driver | 1 |
| Presence Sensor | TCST2103 Photogate / IR Breakbeam | 1 |
| Diverter Actuator | 12V Solenoid Pusher (5N, 20mm stroke) | 1 |
| Microcontroller | Arduino Uno R3 | 1 |
| Illumination | LED Ring Light 6500K + Diffuser | 1 |
| Display | 15.6" HDMI Portable Monitor | 1 |
| Power Supply | 12V 10A SMPS + 5V 3A Buck Module | 1 |
| Chassis | Aluminum Extrusion 2020 + Acrylic Platform | 1 |
| Collection Bin | ABS Plastic Tray | 1 |
| Emergency Stop | NC Mushroom Pushbutton | 1 |

## Software Requirements

### Jetson Nano (Inference Host)
- JetPack 5.1
- Python 3.8+
- PyTorch 1.13+
- TensorRT 8.5+
- OpenCV 4.7+

### Python Packages
```bash
pip install torch torchvision opencv-python pyzbar pyserial flask flask-socketio paho-mqtt numpy
```

### Arduino
- Arduino IDE 1.8.x or 2.x
- No external libraries required (uses built-in Servo and Wire)

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/inspection-system.git
cd inspection-system
```

### 2. Train the Model (or use pretrained)
```bash
cd src/python
python3 train.py --dataset ../../data/processed --epochs 50
```

### 3. Export to TensorRT
```bash
python3 export_trt.py --weights model.pth --output model.trt
```

### 4. Upload Arduino Firmware
1. Open `src/arduino/belt_controller.ino` in Arduino IDE
2. Select **Tools > Board > Arduino Uno**
3. Select the correct COM port
4. Click **Upload**

### 5. Launch the System
```bash
# Terminal 1: Start inference engine
python3 inspection_engine.py --engine model.trt --port /dev/ttyACM0

# Terminal 2: Start dashboard
python3 dashboard.py
```

### 6. Open Dashboard
Navigate to `http://jetson-ip:5000` in your browser.

## Project Structure

```
inspection-system/
├── README.md
├── LICENSE
├── .gitignore
├── src/
│   ├── python/
│   │   ├── inspection_engine.py    # TensorRT inference & serial I/O
│   │   ├── train.py                  # PyTorch training pipeline
│   │   ├── export_trt.py             # ONNX -> TensorRT converter
│   │   ├── augment.py                # Offline data augmentation
│   │   ├── evaluate.py               # Holdout test evaluation
│   │   ├── dashboard.py              # Flask web dashboard
│   │   └── requirements.txt          # Python dependencies
│   └── arduino/
│       └── belt_controller.ino       # Belt & actuator control
├── docs/
│   ├── SYSTEM_DESIGN.md              # Architecture & algorithms
│   ├── USER_MANUAL.md                # Assembly & operation
│   └── WIRING.md                     # Pinout & circuit diagrams
├── hardware/
│   └── components_list.md            # BOM with sources & costs
├── dashboard/
│   ├── templates/
│   │   └── dashboard.html            # Real-time metric UI
│   └── static/
│       ├── css/
│       │   └── style.css             # Dashboard styles
│       └── js/
│           └── socket_client.js      # WebSocket client logic
└── tests/
    └── unit_tests.md                 # Component validation procedures
```

## Operating Modes

| Mode | LED Color | Description |
|------|-----------|-------------|
| ACTIVE | Green | Belt running, inspection active |
| IDLE | Blue | Belt stopped, awaiting start command |
| CALIBRATION | Yellow | Camera focus and lighting adjustment |
| FAULT | Red + Buzzer | Error detected, system halted |

## Dashboard Metrics

The web dashboard displays:
- **Total Products Inspected**: Cumulative count since shift start
- **Defective Products**: Count and percentage of rejected items
- **Detection Accuracy**: Real-time classifier accuracy
- **Average Inspection Time**: Mean latency per article (ms)
- **System Status**: Current operational mode
- **Defect Log**: Timestamped table of all rejections with class and confidence

## Serial Protocol

| Command | Direction | Description |
|---------|-----------|-------------|
| `GATE:<timestamp>` | Arduino → Jetson | Photogate triggered |
| `REJECT:<class>` | Jetson → Arduino | Divert article (class = defect type) |
| `ACCEPT` | Jetson → Arduino | Article is conforming |
| `LOG:<event>` | Arduino → Jetson | Actuation confirmation |
| `EMERGENCY_STOP` | Arduino → Jetson | E-stop activated |

## Safety

- **Always test the Emergency Stop button before each shift**
- Keep hands clear of the solenoid pusher stroke zone
- Ensure LED ring operates below 50°C enclosure temperature
- Ground all metal frame elements to prevent ESD
- Maintain belt guard panels during operation

## Documentation

- **[System Design](docs/SYSTEM_DESIGN.md)**: CNN architecture, training regimen, evaluation metrics
- **[User Manual](docs/USER_MANUAL.md)**: Mechanical assembly, calibration, and operation
- **[Wiring Guide](docs/WIRING.md)**: Complete pin mapping and power distribution

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'feat: add new feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Robotics Automation Engineering Capstone Project
- August 2026
