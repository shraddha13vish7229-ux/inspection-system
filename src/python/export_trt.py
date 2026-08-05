#!/usr/bin/env python3
"""
PyTorch -> ONNX -> TensorRT Export Utility
Converts trained MobileNetV2 to optimized TensorRT engine
"""

import torch
import torch.onnx
import tensorrt as trt
import argparse
import os
from torchvision import models
import numpy as np


def pth_to_onnx(model_path, output_onnx, num_classes=5):
    """Export PyTorch model to ONNX format."""
    print(f"[INFO] Loading PyTorch model from {model_path}")
    model = models.mobilenet_v2(pretrained=False)
    model.classifier = torch.nn.Sequential(
        torch.nn.Dropout(0.2),
        torch.nn.Linear(model.last_channel, num_classes)
    )
    model.load_state_dict(torch.load(model_path, map_location='cpu'))
    model.eval()

    dummy_input = torch.randn(1, 3, 224, 224)

    print(f"[INFO] Exporting to ONNX: {output_onnx}")
    torch.onnx.export(
        model,
        dummy_input,
        output_onnx,
        export_params=True,
        opset_version=11,
        do_constant_folding=True,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={'input': {0: 'batch_size'}, 'output': {0: 'batch_size'}}
    )
    print(f"[OK] ONNX export complete")
    return output_onnx


def onnx_to_tensorrt(onnx_path, output_trt, fp16=True):
    """Convert ONNX model to TensorRT engine."""
    print(f"[INFO] Building TensorRT engine from {onnx_path}")

    logger = trt.Logger(trt.Logger.INFO)
    builder = trt.Builder(logger)
    network = builder.create_network(
        1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)
    )
    parser = trt.OnnxParser(network, logger)

    with open(onnx_path, 'rb') as f:
        if not parser.parse(f.read()):
            for error in range(parser.num_errors):
                print(parser.get_error(error))
            raise RuntimeError("ONNX parsing failed")

    config = builder.create_builder_config()
    config.max_workspace_size = 1 << 30  # 1GB
    if fp16:
        config.set_flag(trt.BuilderFlag.FP16)
        print("[INFO] FP16 quantization enabled")

    profile = builder.create_optimization_profile()
    profile.set_shape('input', (1, 3, 224, 224), (1, 3, 224, 224), (8, 3, 224, 224))
    config.add_optimization_profile(profile)

    print("[INFO] Building engine (this may take several minutes)...")
    engine = builder.build_engine(network, config)

    if engine is None:
        raise RuntimeError("Engine build failed")

    with open(output_trt, 'wb') as f:
        f.write(engine.serialize())

    print(f"[OK] TensorRT engine saved: {output_trt}")
    print(f"[INFO] Engine size: {os.path.getsize(output_trt) / 1024 / 1024:.2f} MB")


def main():
    parser = argparse.ArgumentParser(description='Export PyTorch to TensorRT')
    parser.add_argument('--weights', required=True, help='Path to .pth file')
    parser.add_argument('--output', default='model.trt', help='Output .trt path')
    parser.add_argument('--onnx', default='model.onnx', help='Intermediate ONNX path')
    parser.add_argument('--fp16', action='store_true', help='Enable FP16 quantization')
    args = parser.parse_args()

    # Step 1: PyTorch -> ONNX
    onnx_path = pth_to_onnx(args.weights, args.onnx)

    # Step 2: ONNX -> TensorRT
    onnx_to_tensorrt(onnx_path, args.output, fp16=args.fp16)

    print("\n[OK] Export pipeline complete!")


if __name__ == '__main__':
    main()
