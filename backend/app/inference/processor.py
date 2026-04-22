"""Audio preprocessing for raw PCM data from ESP32 sensors."""
import struct
import numpy as np
import torch
import torchaudio.transforms as T


class AudioProcessor:
    """Process raw PCM audio data for inference."""

    # SPH0645 sensitivity: -26 dBFS at 94 dB SPL → calibration offset = +120 dB
    _SPH0645_CALIBRATION_DB = 120.0

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
        num_samples = len(pcm_bytes) // 2
        samples = struct.unpack(f"<{num_samples}h", pcm_bytes)

        # Normalize to [-1, 1]
        waveform = np.array(samples, dtype=np.float32) / 32768.0

        return torch.from_numpy(waveform).unsqueeze(0)

    @staticmethod
    def _a_weighting_weights(freqs: np.ndarray) -> np.ndarray:
        """
        IEC 61672:2003 A-weighting frequency response.

        Returns linear amplitude weights (not dB), normalized so that
        A(1000 Hz) = 1.0 (0 dB at the standard 1 kHz reference).
        DC bin (freq=0) is zeroed to suppress the DC component.
        """
        # Avoid division by zero at DC; use inf so the result is 0 there
        f2 = np.where(freqs == 0, np.inf, freqs ** 2)

        ra = (12200.0 ** 2 * freqs ** 4) / (
            (f2 + 20.6 ** 2)
            * np.sqrt((f2 + 107.7 ** 2) * (f2 + 737.9 ** 2))
            * (f2 + 12200.0 ** 2)
        )

        # Normalize to 0 dB at 1 kHz
        ra_1k = (12200.0 ** 2 * 1000.0 ** 4) / (
            (1000.0 ** 2 + 20.6 ** 2)
            * np.sqrt((1000.0 ** 2 + 107.7 ** 2) * (1000.0 ** 2 + 737.9 ** 2))
            * (1000.0 ** 2 + 12200.0 ** 2)
        )

        return ra / ra_1k

    def compute_loudness_dba(self, waveform: torch.Tensor) -> float:
        """
        Compute A-weighted loudness in absolute dBA (sound pressure level).

        Applies IEC 61672:2003 A-weighting in the frequency domain using an FFT,
        then adds the SPH0645 calibration offset (+120 dB) to convert from
        dBFS(A) to absolute dBA SPL.

        Args:
            waveform: Audio tensor of shape (1, num_samples), normalized to [-1, 1]

        Returns:
            Loudness in dBA. Returns 0.0 for silence.
        """
        # Use float64 for FFT precision
        samples = waveform.squeeze().numpy().astype(np.float64)
        n = len(samples)

        freqs = np.fft.rfftfreq(n, d=1.0 / self.sample_rate)
        spectrum = np.fft.rfft(samples)

        weights = self._a_weighting_weights(freqs)
        weighted_spectrum = spectrum * weights

        # RMS via Parseval's theorem: sum(|X[k]|²) / N² gives mean square
        rms = np.sqrt(np.sum(np.abs(weighted_spectrum) ** 2) / n ** 2)

        if rms < 1e-10:
            return 0.0

        dbfs_a = 20.0 * np.log10(rms)
        return round(dbfs_a + self._SPH0645_CALIBRATION_DB, 2)

    def preprocess(self, pcm_bytes: bytes) -> tuple[torch.Tensor, float]:
        """
        Preprocess raw PCM bytes for model inference.

        Args:
            pcm_bytes: Raw PCM data (16-bit signed, 16kHz, mono)

        Returns:
            Tuple of (MelSpectrogram tensor of shape (1, n_mels, time_steps), loudness_dba)
        """
        waveform = self.pcm_to_tensor(pcm_bytes)

        loudness_dba = self.compute_loudness_dba(waveform)

        mel_spec = self.mel_transform(waveform)
        mel_spec_db = self.amplitude_to_db(mel_spec)

        return mel_spec_db, loudness_dba
