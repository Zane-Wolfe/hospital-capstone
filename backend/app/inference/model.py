"""Sound classification model for multi-label audio event detection."""
import logging
from pathlib import Path

import torch
import torch.nn as nn

from app.inference.processor import AudioProcessor

logger = logging.getLogger(__name__)


class BasicBlock(nn.Module):
    """Basic residual block for ResNet18."""

    expansion = 1

    def __init__(self, in_channels: int, out_channels: int, stride: int = 1):
        super().__init__()
        self.conv1 = nn.Conv2d(
            in_channels, out_channels, kernel_size=3, stride=stride, padding=1, bias=False
        )
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.conv2 = nn.Conv2d(
            out_channels, out_channels, kernel_size=3, stride=1, padding=1, bias=False
        )
        self.bn2 = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU(inplace=True)

        # Downsample layer for skip connection when dimensions change
        self.downsample = None
        if stride != 1 or in_channels != out_channels:
            self.downsample = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=stride, bias=False),
                nn.BatchNorm2d(out_channels),
            )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        identity = x

        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)

        out = self.conv2(out)
        out = self.bn2(out)

        if self.downsample is not None:
            identity = self.downsample(x)

        out += identity
        out = self.relu(out)

        return out


class ResNet18(nn.Module):
    """ResNet18 implementation for audio classification."""

    def __init__(self, num_classes: int = 7, in_channels: int = 1):
        super().__init__()

        self.in_planes = 64

        # Initial convolution layer (modified for 1-channel input)
        self.conv1 = nn.Conv2d(in_channels, 64, kernel_size=7, stride=2, padding=3, bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)

        # Residual layers
        self.layer1 = self._make_layer(64, 2, stride=1)
        self.layer2 = self._make_layer(128, 2, stride=2)
        self.layer3 = self._make_layer(256, 2, stride=2)
        self.layer4 = self._make_layer(512, 2, stride=2)

        # Classification head
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(512, num_classes)

    def _make_layer(self, out_channels: int, num_blocks: int, stride: int) -> nn.Sequential:
        layers = []
        layers.append(BasicBlock(self.in_planes, out_channels, stride))
        self.in_planes = out_channels
        for _ in range(1, num_blocks):
            layers.append(BasicBlock(out_channels, out_channels))
        return nn.Sequential(*layers)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        x = self.layer4(x)

        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        x = self.fc(x)

        return x


class SoundClassificationModel(nn.Module):
    """ResNet18-based model for sound classification using MelSpectrogram input."""

    def __init__(self, num_classes: int = 7, n_mels: int = 128):
        super().__init__()

        self.n_mels = n_mels
        self.base_model = ResNet18(num_classes=num_classes, in_channels=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass.

        Args:
            x: Input tensor of shape (batch_size, 1, n_mels, time_steps)

        Returns:
            Output logits of shape (batch_size, num_classes)
        """
        return self.base_model(x)


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
        mel_spec, loudness_dba = self.processor.preprocess(pcm_bytes)

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
            "loudness_dba": loudness_dba,
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
