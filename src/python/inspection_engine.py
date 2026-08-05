#!/usr/bin/env python3
"""
AI-Assisted Quality Inspection Engine
Host: NVIDIA Jetson Nano
Responsibilities: Frame acquisition, TensorRT inference,
                  verdict arbitration, serial command dispatch
"""

import cv2
import numpy as np
import serial
import tensorrt as trt
import pycuda.driver as cuda
import pycuda.autoinit
import time
import argparse
from collections import deque
from datetime import datetime


class InspectionEngine:
    """Real-time defect classification using TensorRT-optimized CNN."""

    def __init__(self, engine_path, serial_port='/dev/ttyACM0', camera_id=0):
        self.cap = cv2.VideoCapture(camera_id)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # Serial link to Arduino belt controller
        try:
            self.link = serial.Serial(serial_port, 115200, timeout=0.1)
            time.sleep(2)
            print(f"[OK] Serial connected on {serial_port}")
        except serial.SerialException as e:
            print(f"[WARN] Serial not available: {e}")
            self.link = None

        # Load TensorRT engine
        self.trt_logger = trt.Logger(trt.Logger.WARNING)
        self.runtime = trt.Runtime(self.trt_logger)
        with open(engine_path, "rb") as f:
            self.engine = self.runtime.deserialize_cuda_engine(f.read())
        self.context = self.engine.create_execution_context()

        # Allocate GPU memory
        self.input_shape = (1, 3, 224, 224)
        self.output_shape = (1, 5)
        self.d_input = cuda.mem_alloc(
            np.prod(self.input_shape) * np.dtype(np.float32).itemsize
        )
        self.d_output = cuda.mem_alloc(
            np.prod(self.output_shape) * np.dtype(np.float32).itemsize
        )
        self.stream = cuda.Stream()

        # Class labels
        self.labels = [
            'conforming',
            'absent_constituent',
            'fracture',
            'dimensional_deviation',
            'chromatic_aberration'
        ]

        # Temporal voting buffer
        self.buffer = deque(maxlen=5)

        # Session statistics
        self.stats = {
            'total': 0,
            'rejected': 0,
            'times': [],
            'defect_counts': {label: 0 for label in self.labels[1:]}
        }

    def preprocess(self, frame):
        """Convert raw frame to model input tensor."""
        blob = cv2.resize(frame, (224, 224))
        blob = cv2.cvtColor(blob, cv2.COLOR_BGR2RGB)
        blob = blob.astype(np.float32) / 255.0
        mean = np.array([0.485, 0.456, 0.406])
        std = np.array([0.229, 0.224, 0.225])
        blob = (blob - mean) / std
        blob = np.transpose(blob, (2, 0, 1))
        return np.expand_dims(blob, axis=0).ravel()

    def infer(self, frame):
        """Run single-frame inference on GPU."""
        host_input = self.preprocess(frame)
        cuda.memcpy_htod_async(self.d_input, host_input, self.stream)
        self.context.execute_async_v2(
            bindings=[int(self.d_input), int(self.d_output)],
            stream_handle=self.stream.handle
        )
        host_output = np.empty(self.output_shape, dtype=np.float32)
        cuda.memcpy_dtoh_async(host_output, self.d_output, self.stream)
        self.stream.synchronize()
        return host_output[0]

    def arbitrate(self, logits):
        """Apply softmax and temporal majority voting."""
        probs = np.exp(logits) / np.sum(np.exp(logits))
        self.buffer.append(np.argmax(probs))

        if len(self.buffer) < self.buffer.maxlen:
            return None, 0.0

        # Majority vote
        mode = max(set(self.buffer), key=list(self.buffer).count)
        confidence = float(probs[mode])
        return self.labels[mode], confidence

    def dispatch(self, verdict, confidence):
        """Send actuation command to Arduino."""
        if verdict == 'conforming':
            if self.link and self.link.is_open:
                self.link.write(b"ACCEPT\n")
        else:
            cmd = f"REJECT:{verdict}\n".encode()
            if self.link and self.link.is_open:
                self.link.write(cmd)

        self.stats['total'] += 1
        if verdict != 'conforming':
            self.stats['rejected'] += 1
            self.stats['defect_counts'][verdict] += 1

    def annotate(self, frame, verdict, confidence):
        """Draw classification result on frame."""
        color = (0, 255, 0) if verdict == 'conforming' else (0, 0, 255)
        text = f"{verdict.upper()}: {confidence:.2%}"
        cv2.putText(frame, text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.putText(frame, f"Total: {self.stats['total']}", (10, 60),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(frame, f"Rejected: {self.stats['rejected']}", (10, 80),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        return frame

    def run(self):
        """Main inspection loop."""
        print("[INFO] Inspection engine active. Press 'q' to quit.")

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("[WARN] Frame capture failed")
                continue

            t0 = time.perf_counter()
            logits = self.infer(frame)
            verdict, conf = self.arbitrate(logits)

            if verdict is not None and conf > 0.75:
                self.dispatch(verdict, conf)
                dt = (time.perf_counter() - t0) * 1000
                self.stats['times'].append(dt)
                print(f"[RESULT] {verdict} ({conf:.3f}) | {dt:.1f}ms")

            display = self.annotate(frame.copy(), verdict or 'analyzing', conf)
            cv2.imshow('Inspection Feed', display)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        self.shutdown()

    def shutdown(self):
        """Release all resources."""
        self.cap.release()
        cv2.destroyAllWindows()
        if self.link and self.link.is_open:
            self.link.close()
        self.summarize()

    def summarize(self):
        """Print session summary."""
        print("\n===== INSPECTION SESSION SUMMARY =====")
        print(f"Articles Examined: {self.stats['total']}")
        print(f"Articles Rejected: {self.stats['rejected']}")
        if self.stats['times']:
            print(f"Mean Latency: {np.mean(self.stats['times']):.1f}ms")
            print(f"Max Latency: {np.max(self.stats['times']):.1f}ms")
        if self.stats['total'] > 0:
            print(f"Yield Rate: {1 - self.stats['rejected']/self.stats['total']:.2%}")
        print("Defect Breakdown:")
        for defect, count in self.stats['defect_counts'].items():
            print(f"  {defect}: {count}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Quality Inspection Engine')
    parser.add_argument('--engine', required=True, help='Path to TensorRT engine')
    parser.add_argument('--port', default='/dev/ttyACM0', help='Serial port')
    parser.add_argument('--camera', type=int, default=0, help='Camera ID')
    args = parser.parse_args()

    engine = InspectionEngine(args.engine, args.port, args.camera)
    engine.run()
