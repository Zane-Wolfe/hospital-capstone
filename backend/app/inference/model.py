"""Sound classification model for multi-label audio event detection."""
import logging
from pathlib import Path

import torch
import torch.nn as nn

from app.inference.processor import AudioProcessor

logger = logging.getLogger(__name__)


class SoundClassificationModel(nn.Module):
    """Conv2D CNN model for sound classification using MelSpectrogram input."""

    def __init__(self, num_classes: int = 7, n_mels: int = 128):
        super().__init__()

        self.n_mels = n_mels

        # Convolutional layers (4 layers: 32→64→128→256)
        self.conv1 = nn.Conv2d(1, 32, kernel_size=3, stride=1, padding=1)
        self.bn1 = nn.BatchNorm2d(32)
        self.pool1 = nn.MaxPool2d(2)

        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, stride=1, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.pool2 = nn.MaxPool2d(2)

        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.pool3 = nn.MaxPool2d(2)

        self.conv4 = nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1)
        self.bn4 = nn.BatchNorm2d(256)
        self.pool4 = nn.MaxPool2d(2)

        # Global average pooling
        self.global_pool = nn.AdaptiveAvgPool2d((1, 1))

        # Fully connected layers: 256→128→64→num_classes
        self.fc1 = nn.Linear(256, 128)
        self.dropout1 = nn.Dropout(0.5)
        self.fc2 = nn.Linear(128, 64)
        self.dropout2 = nn.Dropout(0.5)
        self.fc3 = nn.Linear(64, num_classes)

        self.relu = nn.ReLU()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input tensor of shape (batch_size, 1, n_mels, time_steps)

        Returns:
            Output logits of shape (batch_size, num_classes)
        """
        # Conv block 1
        x = self.relu(self.bn1(self.conv1(x)))
        x = self.pool1(x)

        # Conv block 2
        x = self.relu(self.bn2(self.conv2(x)))
        x = self.pool2(x)

        # Conv block 3
        x = self.relu(self.bn3(self.conv3(x)))
        x = self.pool3(x)

        # Conv block 4
        x = self.relu(self.bn4(self.conv4(x)))
        x = self.pool4(x)

        # Global average pooling
        x = self.global_pool(x)
        x = x.view(x.size(0), -1)

        # Fully connected layers
        x = self.relu(self.fc1(x))
        x = self.dropout1(x)
        x = self.relu(self.fc2(x))
        x = self.dropout2(x)
        x = self.fc3(x)

        return x


class SoundInference:
    """Inference engine for sound classification."""

    def __init__(
        self,
        model_path: str,
        input_sample_rate: int = 16000,
        threshold_override: float | None = None,
        device: str | None = None,
    ):
        """
        Initialize the inference engine.

        Args:
            model_path: Path to the saved model checkpoint (contains embedded config)
            input_sample_rate: Sample rate of incoming audio
            threshold_override: Optional override for confidence threshold (uses checkpoint default if None)
            device: Device to use ('cuda' or 'cpu'). Auto-detected if None.
        """
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model_path = Path(model_path)

        logger.info(f"Initializing SoundInference on device: {self.device}")

        # Load checkpoint (contains model weights and config)
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")

        checkpoint = torch.load(self.model_path, map_location=self.device, weights_only=False)

        # Extract config from checkpoint
        self.class_names = checkpoint.get("class_names", [])
        self.n_mels = checkpoint.get("n_mels", 128)
        self.n_fft = checkpoint.get("n_fft", 1024)
        self.hop_length = checkpoint.get("hop_length", 512)
        self.sample_rate = checkpoint.get("sample_rate", 16000)

        # Threshold: use override if provided, otherwise use checkpoint default
        checkpoint_threshold = checkpoint.get("threshold", 0.5)
        self.threshold = threshold_override if threshold_override is not None else checkpoint_threshold

        # Build index mappings from class_names list
        self.idx_to_class = {i: name for i, name in enumerate(self.class_names)}
        self.class_to_idx = {name: i for i, name in enumerate(self.class_names)}

        logger.info(f"Loaded config from checkpoint - Classes: {self.class_names}")
        logger.info(f"Using threshold: {self.threshold} (override: {threshold_override is not None})")

        # Load model
        num_classes = len(self.class_names)
        self.model = SoundClassificationModel(num_classes=num_classes, n_mels=self.n_mels)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.model = self.model.to(self.device)
        self.model.eval()

        test_accuracy = checkpoint.get("test_accuracy", "N/A")
        logger.info(f"Loaded model from {model_path} (test accuracy: {test_accuracy}%)")

        # Initialize audio processor with checkpoint config
        self.processor = AudioProcessor(
            sample_rate=self.sample_rate,
            n_mels=self.n_mels,
            n_fft=self.n_fft,
            hop_length=self.hop_length,
        )

    def predict(
        self,
        pcm_bytes: bytes,
        threshold: float | None = None,
        multi_label: bool = True,
    ) -> dict:
        """
        Make predictions for raw PCM audio data.

        Args:
            pcm_bytes: Raw PCM data (16-bit signed, mono)
            threshold: Confidence threshold (uses instance threshold if None)
            multi_label: If True, use sigmoid for multi-label classification;
                        if False, use softmax for single-label

        Returns:
            Dictionary with prediction results
        """
        # Use provided threshold or fall back to instance threshold
        effective_threshold = threshold if threshold is not None else self.threshold

        # Preprocess audio
        mel_spec, loudness_db = self.processor.preprocess(pcm_bytes)

        # Add batch dimension: (1, n_mels, time) -> (batch, 1, n_mels, time)
        mel_spec = mel_spec.unsqueeze(0).to(self.device)

        # Make prediction
        with torch.no_grad():
            outputs = self.model(mel_spec)

            if multi_label:
                # Multi-label: use sigmoid to get independent probabilities
                probabilities = torch.sigmoid(outputs)
            else:
                # Single-label: use softmax
                probabilities = torch.softmax(outputs, dim=1)

        # Get all class probabilities
        all_probs = {}
        detected_events = []

        for idx, class_name in self.idx_to_class.items():
            prob = probabilities[0, idx].item()
            all_probs[class_name] = round(prob, 4)

            if prob >= effective_threshold:
                detected_events.append({
                    "label": class_name,
                    "confidence": round(prob, 4),
                })

        # Sort detected events by confidence (highest first)
        detected_events.sort(key=lambda x: x["confidence"], reverse=True)

        return {
            "detected_events": detected_events,
            "all_probabilities": all_probs,
            "loudness_db": loudness_db,
        }

    def health_check(self) -> dict:
        """Check if the model is properly loaded and ready."""
        return {
            "model_loaded": self.model is not None,
            "device": self.device,
            "num_classes": len(self.idx_to_class),
            "classes": list(self.idx_to_class.values()),
            "n_mels": self.n_mels,
            "n_fft": self.n_fft,
            "hop_length": self.hop_length,
            "sample_rate": self.sample_rate,
            "threshold": self.threshold,
        }


# Global inference instance (initialized during app startup)
_inference: SoundInference | None = None


def get_inference() -> SoundInference | None:
    """Get the global inference instance."""
    return _inference


def init_inference(
    model_path: str,
    input_sample_rate: int = 16000,
    threshold_override: float | None = None,
    device: str | None = None,
) -> SoundInference:
    """Initialize the global inference instance."""
    global _inference
    _inference = SoundInference(
        model_path=model_path,
        input_sample_rate=input_sample_rate,
        threshold_override=threshold_override,
        device=device,
    )
    return _inference


def close_inference():
    """Clean up inference resources."""
    global _inference
    if _inference is not None:
        # PyTorch cleanup if needed
        _inference = None
        logger.info("Inference engine closed")
