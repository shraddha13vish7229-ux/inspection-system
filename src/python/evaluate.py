#!/usr/bin/env python3
"""
Model Evaluation Script
Computes Precision, Recall, F1-Score, and Confusion Matrix on holdout test set
"""

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import models, transforms
from sklearn.metrics import classification_report, confusion_matrix, precision_recall_fscore_support
import numpy as np
import argparse
import seaborn as sns
import matplotlib.pyplot as plt
from train import DefectDataset


def evaluate_model(model_path, test_dir, batch_size=32):
    """Evaluate trained model on test set."""
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Load model
    model = models.mobilenet_v2(pretrained=False)
    model.classifier = nn.Sequential(
        nn.Dropout(0.2),
        nn.Linear(model.last_channel, 5)
    )
    model.load_state_dict(torch.load(model_path, map_location=device))
    model = model.to(device)
    model.eval()

    # Test transforms
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    test_dataset = DefectDataset(test_dir, transform)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    all_preds = []
    all_labels = []
    all_probs = []

    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            outputs = model(images)
            probs = torch.softmax(outputs, dim=1)
            _, predicted = outputs.max(1)

            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.numpy())
            all_probs.extend(probs.cpu().numpy())

    # Metrics
    classes = test_dataset.classes
    print("\n===== CLASSIFICATION REPORT =====")
    print(classification_report(all_labels, all_preds, target_names=classes))

    precision, recall, f1, support = precision_recall_fscore_support(
        all_labels, all_preds, average='macro'
    )
    print(f"\nMacro Precision: {precision:.4f}")
    print(f"Macro Recall: {recall:.4f}")
    print(f"Macro F1-Score: {f1:.4f}")

    # Confusion matrix
    cm = confusion_matrix(all_labels, all_preds)
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=classes, yticklabels=classes)
    plt.title('Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    plt.savefig('confusion_matrix.png')
    print("\n[OK] Confusion matrix saved: confusion_matrix.png")

    # Per-class accuracy
    per_class_acc = cm.diagonal() / cm.sum(axis=1)
    print("\nPer-Class Accuracy:")
    for cls, acc in zip(classes, per_class_acc):
        print(f"  {cls}: {acc:.2%}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', required=True, help='Path to .pth file')
    parser.add_argument('--test-dir', required=True, help='Path to test dataset')
    parser.add_argument('--batch-size', type=int, default=32)
    args = parser.parse_args()

    evaluate_model(args.model, args.test_dir, args.batch_size)
