#!/usr/bin/env python3
"""
Offline Data Augmentation Pipeline
Generates synthetic training samples from original images
"""

import cv2
import numpy as np
import os
import argparse
from pathlib import Path


def apply_rotation(image, angle):
    """Rotate image by given angle."""
    h, w = image.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(image, M, (w, h), borderMode=cv2.BORDER_REFLECT)


def apply_brightness(image, factor):
    """Scale image brightness."""
    return np.clip(image * factor, 0, 255).astype(np.uint8)


def apply_noise(image, sigma=0.01):
    """Add Gaussian noise."""
    noise = np.random.normal(0, sigma * 255, image.shape)
    return np.clip(image + noise, 0, 255).astype(np.uint8)


def apply_cutout(image, patch_size=8):
    """Randomly mask out a square patch."""
    h, w = image.shape[:2]
    x = np.random.randint(0, w - patch_size)
    y = np.random.randint(0, h - patch_size)
    image = image.copy()
    image[y:y+patch_size, x:x+patch_size] = 128
    return image


def augment_image(image_path, output_dir, num_augmentations=5):
    """Generate augmented variants of a single image."""
    image = cv2.imread(str(image_path))
    if image is None:
        return

    base_name = Path(image_path).stem

    for i in range(num_augmentations):
        aug = image.copy()

        # Random rotation
        angle = np.random.uniform(-15, 15)
        aug = apply_rotation(aug, angle)

        # Random brightness
        factor = np.random.uniform(0.8, 1.2)
        aug = apply_brightness(aug.astype(np.float32), factor)

        # Random horizontal flip
        if np.random.random() > 0.5:
            aug = cv2.flip(aug, 1)

        # Random noise
        if np.random.random() > 0.5:
            aug = apply_noise(aug)

        # Random cutout
        if np.random.random() > 0.7:
            aug = apply_cutout(aug)

        out_path = os.path.join(output_dir, f"{base_name}_aug{i}.jpg")
        cv2.imwrite(out_path, aug)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', required=True, help='Input directory with class subfolders')
    parser.add_argument('--output', required=True, help='Output directory')
    parser.add_argument('--num-aug', type=int, default=5, help='Augmentations per image')
    args = parser.parse_args()

    os.makedirs(args.output, exist_ok=True)

    for class_name in os.listdir(args.input):
        class_dir = os.path.join(args.input, class_name)
        if not os.path.isdir(class_dir):
            continue

        out_class_dir = os.path.join(args.output, class_name)
        os.makedirs(out_class_dir, exist_ok=True)

        for fname in os.listdir(class_dir):
            if fname.lower().endswith(('.png', '.jpg', '.jpeg')):
                img_path = os.path.join(class_dir, fname)
                # Copy original
                img = cv2.imread(img_path)
                cv2.imwrite(os.path.join(out_class_dir, fname), img)
                # Generate augmentations
                augment_image(img_path, out_class_dir, args.num_aug)

        count = len(os.listdir(out_class_dir))
        print(f"[OK] {class_name}: {count} images")

    print("\n[INFO] Augmentation complete!")


if __name__ == '__main__':
    main()
