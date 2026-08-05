# System Design Document

## 1. Problem Statement

Develop an AI-assisted robotic inspection system capable of detecting manufacturing defects on products moving along a conveyor belt and automatically sorting defective items.

## 2. System Architecture

The inspection platform follows a pipeline architecture with six sequential stages:

### 2.1 Acquisition Stage
- **USB3 Machine Vision Camera**: Captures 640x480 frames at 30 FPS.
- **Photogate Sensor**: IR breakbeam triggers frame capture when article leading edge crosses inspection plane.
- **LED Ring Light**: 6500K diffuse illumination eliminates shadows and specular reflections.

### 2.2 Preprocessing Stage
- Resize to 224x224 (MobileNetV2 input).
- Convert BGR to RGB.
- Normalize using ImageNet statistics.
- Optional: Gaussian blur for noise reduction.

### 2.3 Inference Stage
- **Backbone**: MobileNetV2 (pretrained on ImageNet).
- **Head**: Custom 5-class classifier with dropout.
- **Optimization**: TensorRT FP16 quantization on Jetson Nano.
- **Latency Target**: < 50 ms per frame.

### 2.4 Decision Stage
- Softmax probability threshold: 0.75 minimum confidence.
- Temporal majority voting over 5 consecutive frames.
- Verdict: ACCEPT or REJECT (with defect class).

### 2.5 Actuation Stage
- **Belt Control**: NEMA 17 stepper at 400 PPS (constant speed).
- **Diverter**: 12V solenoid pusher, 60ms pulse, 850ms delay from photogate.
- **Synchronization**: Arduino schedules solenoid based on belt velocity lookup table.

### 2.6 Telemetry Stage
- MQTT broker relays inspection events.
- Flask dashboard renders real-time metrics.
- CSV log persists all events with timestamps.

## 3. AI Model Architecture

### 3.1 MobileNetV2 Backbone
- Input: 224x224x3 RGB tensor
- Stem: 3x3 conv, 32 filters, stride 2
- Bottleneck layers: 17 inverted residual blocks
- Expansion factors: t ∈ {1, 6}
- Output: 1280-dim feature vector

### 3.2 Custom Classifier Head
```
Dropout(0.2) → Linear(1280 → 5) → Softmax
```

### 3.3 Training Regimen
- **Phase 1** (20 epochs): Freeze backbone, train head only, lr=1e-3
- **Phase 2** (30 epochs): Unfreeze last 4 bottleneck layers, lr=1e-4
- **Optimizer**: Adam with ReduceLROnPlateau scheduler
- **Loss**: Categorical Cross-Entropy
- **Early Stopping**: Patience = 5 epochs

### 3.4 TensorRT Optimization
- Export PyTorch → ONNX (opset 11)
- Convert ONNX → TensorRT with FP16 quantization
- Engine size: ~6.8 MB
- Inference speed: 28 FPS on Jetson Nano

## 4. Dataset

### 4.1 Classes
1. Conforming
2. Absent Constituent
3. Fracture
4. Dimensional Deviation
5. Chromatic Aberration

### 4.2 Composition
- Total: 4,800 labeled frames
- Train: 3,600 (75%)
- Validation: 600 (12.5%)
- Test: 600 (12.5%)

### 4.3 Augmentation
- Random rotation (±15°)
- Horizontal flip (p=0.5)
- Brightness jitter (0.8x-1.2x)
- Gaussian noise (σ=0.01)
- Random cutout (8x8 patch)

## 5. Evaluation Metrics

| Metric | Formula | Purpose |
|--------|---------|---------|
| Precision | TP / (TP + FP) | Minimize false rejects |
| Recall | TP / (TP + FN) | Catch all defects |
| F1-Score | 2 * (P * R) / (P + R) | Balanced measure |
| Accuracy | (TP + TN) / Total | Overall correctness |

### 5.1 Test Results
- Macro Precision: 0.921
- Macro Recall: 0.913
- Macro F1-Score: 0.916
- Overall Accuracy: 96.0%

## 6. Performance Benchmarks

| Platform | Latency | Throughput |
|----------|---------|------------|
| Jetson Nano + TensorRT FP16 | 36 ms | 27.8 FPS |
| Workstation RTX 3060 | 12 ms | 83.3 FPS |
| Raspberry Pi 4 + ONNX | 180 ms | 5.6 FPS |

## 7. Known Limitations

- Solenoid duty cycle limited to 10%.
- Camera autofocus introduces timing variability.
- Fracture detection degrades on glossy surfaces.
- Jetson Nano RAM limits batch size during training.

## 8. Future Enhancements

- Multi-spectral imaging (NIR/UV) for subsurface defects.
- Vision Transformer (ViT) backbone for improved accuracy.
- Active learning loop for continuous model improvement.
- Digital twin simulation for offline validation.
- Predictive maintenance via vibration analysis.
- Fleet analytics across multiple inspection stations.
