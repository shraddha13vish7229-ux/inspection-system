# Wiring Guide

Complete pin mapping and circuit connections for the Automated Quality Inspection System.

## Arduino Uno Pin Map

### Stepper Motor (NEMA 17 + A4988 Driver)
| A4988 Pin | Arduino Pin | Function |
|-----------|-------------|----------|
| STEP | 2 | Step pulse |
| DIR | 3 | Direction control |
| ENABLE | 4 | Driver enable/disable |
| MS1, MS2, MS3 | GND | Full step mode |
| VDD | 5V | Logic supply |
| GND | GND | Common ground |
| VMOT | 12V | Motor supply |
| A1, A2 | NEMA 17 Coil A | Motor phase A |
| B1, B2 | NEMA 17 Coil B | Motor phase B |

### Solenoid Actuator
| Component | Pin | Notes |
|-----------|-----|-------|
| Solenoid + | 5 | Via NPN transistor (TIP120) or MOSFET (IRF540) |
| Solenoid - | GND | Through flyback diode (1N4007) |

### Photogate Sensor
| Component | Pin | Notes |
|-----------|-----|-------|
| Photogate Output | 6 | INPUT_PULLUP, active LOW when beam broken |
| Photogate VCC | 5V | Modulated IR emitter |
| Photogate GND | GND | Common ground |

### Safety & Indicators
| Component | Pin | Notes |
|-----------|-----|-------|
| Emergency Stop | 7 | INPUT_PULLUP, NC switch, hardware interrupt |
| Run LED | 8 | Green, belt active indicator |
| Fault LED | 9 | Red, error state indicator |

## Jetson Nano Connections

### Camera
| Camera | Jetson Pin | Notes |
|--------|-----------|-------|
| USB Camera | USB 3.0 Port | Logitech C920 or equivalent |
| CSI Camera | CSI Connector | Raspberry Pi Camera V2 (optional) |

### Serial Communication (Arduino)
| Jetson | Arduino | Notes |
|--------|---------|-------|
| USB Port | USB Cable | /dev/ttyACM0 or /dev/ttyUSB0 |
| GND | GND | Common ground |

### Power
| Source | Destination | Notes |
|--------|-------------|-------|
| 12V 10A SMPS | A4988 VMOT | Motor power |
| 12V 10A SMPS | LM2596 Input | Step down to 5V |
| LM2596 Output | Arduino Vin | Arduino power |
| LM2596 Output | Jetson 5V Barrel | Jetson power (via barrel jack) |
| Jetson USB | Camera | USB power for webcam |

## Power Distribution Diagram

```
12V 10A SMPS
     |
     +-----> A4988 VMOT (Stepper Motor)
     |
     +-----> LM2596 Buck Converter
                   |
                   +-----> 5V Rail
                             |
                             +-----> Arduino Vin
                             +-----> Jetson Nano 5V
                             +-----> Photogate VCC
                             +-----> Solenoid Driver VCC
```

## Important Notes

- **Flyback Diode**: Always install a 1N4007 diode across the solenoid coil (cathode to positive) to protect the transistor from inductive kickback.
- **Stepper Current**: Adjust the A4988 current limit potentiometer so the motor runs warm but not hot (typically 0.5-1.0A per coil).
- **Common Ground**: Arduino GND, Jetson GND, and SMPS GND must be connected together.
- **USB Isolation**: If ground loops cause serial communication errors, use a USB isolator between Jetson and Arduino.
- **Photogate Alignment**: Ensure emitter and receiver are perfectly aligned; misalignment causes false triggers.
- **Solenoid Duty Cycle**: Do not exceed 10% duty cycle (1 second ON per 10 seconds) to prevent coil overheating.

## Serial Protocol

| Command | Direction | Description |
|---------|-----------|-------------|
| `GATE:<timestamp>` | Arduino → Jetson | Photogate beam broken |
| `REJECT:<class>` | Jetson → Arduino | Activate solenoid after delay |
| `ACCEPT` | Jetson → Arduino | Article is conforming |
| `START` | Jetson → Arduino | Start belt motion |
| `STOP` | Jetson → Arduino | Stop belt motion |
| `EMERGENCY_STOP` | Arduino → Jetson | E-stop activated |
| `CONTROLLER_READY` | Arduino → Jetson | Boot complete |
