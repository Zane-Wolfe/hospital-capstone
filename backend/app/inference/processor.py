"""Audio preprocessing for raw PCM data from ESP32 sensors."""
import struct
import numpy as np
import torch
import torchaudio.transforms as T


class AudioProcessor:
    """Process raw PCM audio data for inference."""

    def __init__(
        self,
        sample_rate: int = 16000,
        n_mels: int = 128,
        n_fft: int = 1024,
        hop_length: int = 512,
    ):
        """
        Initialize the audio processor.

        Args:
            sample_rate: Sample rate of audio (ESP32 sends 16kHz, model expects 16kHz)
            n_mels: Number of mel filterbanks
            n_fft: FFT window size
            hop_length: Hop length for spectrogram
        """
        self.sample_rate = sample_rate
        self.n_mels = n_mels
        self.n_fft = n_fft
        self.hop_length = hop_length

        # MelSpectrogram transform
        self.mel_transform = T.MelSpectrogram(
            sample_rate=sample_rate,
            n_fft=n_fft,
            hop_length=hop_length,
            n_mels=n_mels,
            power=2.0,
        )

        # Convert to dB scale
        self.amplitude_to_db = T.AmplitudeToDB(stype='power', top_db=80)

    def pcm_to_tensor(self, pcm_bytes: bytes) -> torch.Tensor:
        """
        Convert raw PCM bytes to a torch tensor.

        Args:
            pcm_bytes: Raw PCM data (16-bit signed, mono)

        Returns:
            Tensor of shape (1, num_samples)
        """
        # Unpack 16-bit signed integers (little-endian)
        num_samples = len(pcm_bytes) // 2
        samples = struct.unpack(f"<{num_samples}h", pcm_bytes)

        # Convert to numpy and normalize to [-1, 1]
        waveform = np.array(samples, dtype=np.float32) / 32768.0

        # Convert to torch tensor with channel dimension
        return torch.from_numpy(waveform).unsqueeze(0)

    def compute_loudness_db(self, waveform: torch.Tensor) -> float:
        """
        Compute loudness in dBFS (decibels relative to full scale).

        Args:
            waveform: Audio tensor of shape (1, num_samples)

        Returns:
            Loudness in dBFS (0 is maximum, negative values are quieter)
        """
        # Compute RMS
        rms = torch.sqrt(torch.mean(waveform**2))

        # Convert to dB (with small epsilon to avoid log(0))
        if rms < 1e-10:
            return -100.0  # Essentially silence

        db = 20 * torch.log10(rms).item()
        return round(db, 2)

    def preprocess(self, pcm_bytes: bytes) -> tuple[torch.Tensor, float]:
        """
        Preprocess raw PCM bytes for model inference.

        Args:
            pcm_bytes: Raw PCM data (16-bit signed, 16kHz, mono)

        Returns:
            Tuple of (MelSpectrogram tensor of shape (1, n_mels, time_steps), loudness_db)
        """
        # Convert PCM bytes to tensor
        waveform = self.pcm_to_tensor(pcm_bytes)

        # Compute loudness
        loudness_db = self.compute_loudness_db(waveform)

        # Extract MelSpectrogram features
        mel_spec = self.mel_transform(waveform)

        # Convert to dB scale
        mel_spec_db = self.amplitude_to_db(mel_spec)

        # Shape is now (1, n_mels, time) - keep channel dimension for Conv2D input
        return mel_spec_db, loudness_db
