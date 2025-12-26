"""Unit tests for configuration schema."""

import pytest
from pathlib import Path

from scandium.config.schema import (
    ScandiumConfig,
    ProjectConfig,
    CameraConfig,
    FiducialsConfig,
    MavlinkConfig,
    ControlConfig,
    LogLevel,
    RunMode,
    CameraSource,
    FiducialBackend,
)


class TestProjectConfig:
    """Tests for ProjectConfig."""

    def test_default_values(self) -> None:
        """Test default project configuration."""
        config = ProjectConfig()
        assert config.name == "Scandium"
        assert config.mode == RunMode.SITL
        assert config.log_level == LogLevel.INFO

    def test_auto_run_id(self) -> None:
        """Test auto-generated run ID."""
        config = ProjectConfig(run_id="auto")
        assert len(config.run_id) == 8
        assert config.run_id != "auto"

    def test_explicit_run_id(self) -> None:
        """Test explicit run ID."""
        config = ProjectConfig(run_id="my-run-123")
        assert config.run_id == "my-run-123"


class TestCameraConfig:
    """Tests for CameraConfig."""

    def test_default_values(self) -> None:
        """Test default camera configuration."""
        config = CameraConfig()
        assert config.source == CameraSource.AIRSIM
        assert config.width == 1280
        assert config.height == 720
        assert config.fps == 30

    def test_video_file_source(self) -> None:
        """Test video file source configuration."""
        config = CameraConfig(
            source=CameraSource.VIDEO_FILE,
            video_path="/path/to/video.mp4",
        )
        assert config.source == CameraSource.VIDEO_FILE
        assert config.video_path == "/path/to/video.mp4"


class TestFiducialsConfig:
    """Tests for FiducialsConfig."""

    def test_default_values(self) -> None:
        """Test default fiducials configuration."""
        config = FiducialsConfig()
        assert config.backend == FiducialBackend.ARUCO
        assert config.marker_size_m == 0.20
        assert 1 in config.target_id_allowlist

    def test_aruco_settings(self) -> None:
        """Test ArUco-specific settings."""
        config = FiducialsConfig()
        assert config.aruco.dictionary == "DICT_4X4_100"
        assert config.aruco.refine is True


class TestMavlinkConfig:
    """Tests for MavlinkConfig."""

    def test_default_values(self) -> None:
        """Test default MAVLink configuration."""
        config = MavlinkConfig()
        assert config.udp.address == "127.0.0.1"
        assert config.udp.port == 14550
        assert config.system_id == 42
        assert config.landing_target_rate_hz == 20


class TestControlConfig:
    """Tests for ControlConfig."""

    def test_default_thresholds(self) -> None:
        """Test default control thresholds."""
        config = ControlConfig()
        assert config.thresholds.acquire_confidence == 0.70
        assert config.thresholds.align_error_m == 0.25
        assert config.thresholds.abort_landability == 0.40


class TestScandiumConfig:
    """Tests for root ScandiumConfig."""

    def test_default_config(self) -> None:
        """Test complete default configuration."""
        config = ScandiumConfig()
        assert config.project.name == "Scandium"
        assert config.camera.source == CameraSource.AIRSIM
        assert config.fiducials.backend == FiducialBackend.ARUCO

    def test_from_dict(self) -> None:
        """Test configuration from dictionary."""
        data = {
            "project": {"name": "TestProject", "mode": "airsim"},
            "camera": {"width": 640, "height": 480},
        }
        config = ScandiumConfig(**data)
        assert config.project.name == "TestProject"
        assert config.project.mode == RunMode.AIRSIM
        assert config.camera.width == 640

    def test_extra_fields_forbidden(self) -> None:
        """Test that extra fields raise error."""
        with pytest.raises(Exception):
            ScandiumConfig(unknown_field="value")
