"""Tests for the inference module."""
import struct
import pytest
import torch

from app.inference.processor import AudioProcessor


class TestAudioProcessor:
    """Tests for AudioProcessor class."""

    @pytest.fixture
    def processor(self):
        """Create an AudioProcessor instance."""
        return AudioProcessor(
            sample_rate=16000,
            n_mels=128,
            n_fft=1024,
            hop_length=512,
        )

    def test_pcm_to_tensor_basic(self, processor):
        """Test converting PCM bytes to tensor."""
        # Create 100 samples of silence (zeros)
        pcm_bytes = struct.pack("<100h", *([0] * 100))
        tensor = processor.pcm_to_tensor(pcm_bytes)

        assert tensor.shape == (1, 100)
        assert tensor.dtype == torch.float32
        assert torch.allclose(tensor, torch.zeros(1, 100))

    def test_pcm_to_tensor_values(self, processor):
        """Test PCM conversion with actual values."""
        # Max positive value (32767) should normalize to ~1.0
        # Max negative value (-32768) should normalize to -1.0
        samples = [32767, -32768, 0, 16384, -16384]
        pcm_bytes = struct.pack(f"<{len(samples)}h", *samples)
        tensor = processor.pcm_to_tensor(pcm_bytes)

        assert tensor.shape == (1, 5)
        assert abs(tensor[0, 0].item() - 1.0) < 0.001  # Max positive
        assert abs(tensor[0, 1].item() + 1.0) < 0.001  # Max negative
        assert tensor[0, 2].item() == 0.0  # Zero

    def test_compute_loudness_silence(self, processor):
        """Test loudness computation for silence."""
        silence = torch.zeros(1, 1000)
        loudness = processor.compute_loudness_db(silence)

        assert loudness == -100.0  # Defined value for silence

    def test_compute_loudness_full_scale(self, processor):
        """Test loudness computation for full-scale signal."""
        # Full scale sine wave would have RMS of 1/sqrt(2) = 0.707
        # For simplicity, test with constant 1.0
        full_scale = torch.ones(1, 1000)
        loudness = processor.compute_loudness_db(full_scale)

        # RMS of constant 1.0 is 1.0, so 20*log10(1) = 0 dB
        assert loudness == 0.0

    def test_compute_loudness_half_scale(self, processor):
        """Test loudness computation for half-scale signal."""
        half_scale = torch.ones(1, 1000) * 0.5
        loudness = processor.compute_loudness_db(half_scale)

        # 20*log10(0.5) = -6.02 dB
        assert abs(loudness - (-6.02)) < 0.1

    def test_preprocess_output_shape(self, processor):
        """Test that preprocess returns correct shapes for MelSpectrogram."""
        # 1 second of 16kHz audio = 16000 samples
        num_samples = 16000
        pcm_bytes = struct.pack(f"<{num_samples}h", *([0] * num_samples))

        mel_spec, loudness = processor.preprocess(pcm_bytes)

        # MelSpectrogram output: (1, n_mels, time_steps)
        assert mel_spec.dim() == 3
        assert mel_spec.shape[0] == 1  # channel dimension
        assert mel_spec.shape[1] == 128  # n_mels
        assert isinstance(loudness, float)


class TestSoundInference:
    """Tests for SoundInference class with mocked model."""

    @pytest.fixture
    def mock_model_checkpoint(self, tmp_path):
        """Create mock model checkpoint with embedded config."""
        from app.inference.model import SoundClassificationModel

        # Create model with 7 classes
        class_names = [
            "alarms", "carts_rolling", "coughing", "door_knock",
            "door_open_close", "footsteps", "speech"
        ]
        model = SoundClassificationModel(num_classes=len(class_names), n_mels=128)

        # Create checkpoint with embedded config
        checkpoint = {
            "model_state_dict": model.state_dict(),
            "test_accuracy": 95.0,
            "class_names": class_names,
            "n_mels": 128,
            "n_fft": 1024,
            "hop_length": 512,
            "sample_rate": 16000,
            "threshold": 0.5,
        }
        model_path = tmp_path / "model.pth"
        torch.save(checkpoint, model_path)

        return str(model_path)

    def test_model_loading(self, mock_model_checkpoint):
        """Test that model loads correctly from checkpoint with embedded config."""
        from app.inference.model import SoundInference

        inference = SoundInference(model_path=mock_model_checkpoint)

        assert inference.model is not None
        assert len(inference.idx_to_class) == 7
        assert "alarms" in inference.idx_to_class.values()
        assert "speech" in inference.idx_to_class.values()
        assert inference.n_mels == 128
        assert inference.threshold == 0.5

    def test_threshold_override(self, mock_model_checkpoint):
        """Test that threshold can be overridden."""
        from app.inference.model import SoundInference

        inference = SoundInference(
            model_path=mock_model_checkpoint,
            threshold_override=0.7,
        )

        assert inference.threshold == 0.7

    def test_predict_returns_structure(self, mock_model_checkpoint):
        """Test that predict returns correct structure."""
        from app.inference.model import SoundInference

        inference = SoundInference(model_path=mock_model_checkpoint)

        # Create 1 second of silence (16kHz, 16-bit)
        num_samples = 16000
        pcm_bytes = struct.pack(f"<{num_samples}h", *([0] * num_samples))

        result = inference.predict(pcm_bytes, threshold=0.3)

        assert "detected_events" in result
        assert "all_probabilities" in result
        assert "loudness_db" in result
        assert isinstance(result["detected_events"], list)
        assert isinstance(result["all_probabilities"], dict)
        assert len(result["all_probabilities"]) == 7  # 7 classes

    def test_health_check(self, mock_model_checkpoint):
        """Test health check returns correct info."""
        from app.inference.model import SoundInference

        inference = SoundInference(model_path=mock_model_checkpoint)

        health = inference.health_check()

        assert health["model_loaded"] is True
        assert health["num_classes"] == 7
        assert "alarms" in health["classes"]
        assert "speech" in health["classes"]
        assert health["n_mels"] == 128
        assert health["n_fft"] == 1024
        assert health["hop_length"] == 512
        assert health["threshold"] == 0.5

    def test_multi_label_probabilities(self, mock_model_checkpoint):
        """Test that multi-label mode returns independent probabilities."""
        from app.inference.model import SoundInference

        inference = SoundInference(model_path=mock_model_checkpoint)

        num_samples = 16000
        pcm_bytes = struct.pack(f"<{num_samples}h", *([0] * num_samples))

        result = inference.predict(pcm_bytes, threshold=0.0, multi_label=True)

        # With multi-label (sigmoid), probabilities can sum > 1 or < 1
        probs = list(result["all_probabilities"].values())
        assert all(0 <= p <= 1 for p in probs)
        assert len(probs) == 7
