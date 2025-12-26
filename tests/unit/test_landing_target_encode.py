"""Unit tests for LANDING_TARGET message encoding."""

import pytest
import time

from scandium.mavlink.landing_target import (
    build_landing_target,
    LandingTargetData,
    MAV_FRAME_BODY_NED,
    MAV_FRAME_LOCAL_NED,
)


class TestBuildLandingTarget:
    """Tests for build_landing_target function."""

    def test_basic_construction(self) -> None:
        """Test basic message construction."""
        data = build_landing_target(
            angle_x=0.1,
            angle_y=-0.05,
            distance_m=5.0,
        )

        assert data.angle_x == 0.1
        assert data.angle_y == -0.05
        assert data.distance_m == 5.0
        assert data.frame == MAV_FRAME_BODY_NED

    def test_with_position(self) -> None:
        """Test construction with position data."""
        data = build_landing_target(
            angle_x=0.1,
            angle_y=-0.05,
            distance_m=5.0,
            x_m=1.0,
            y_m=2.0,
            z_m=5.0,
            position_valid=True,
        )

        assert data.x_m == 1.0
        assert data.y_m == 2.0
        assert data.z_m == 5.0
        assert data.position_valid is True

    def test_auto_timestamp(self) -> None:
        """Test automatic timestamp generation."""
        before = int(time.time() * 1_000_000)
        data = build_landing_target(angle_x=0.0, angle_y=0.0, distance_m=1.0)
        after = int(time.time() * 1_000_000)

        assert before <= data.timestamp_us <= after

    def test_explicit_timestamp(self) -> None:
        """Test explicit timestamp."""
        ts = 1234567890
        data = build_landing_target(
            angle_x=0.0,
            angle_y=0.0,
            distance_m=1.0,
            timestamp_us=ts,
        )

        assert data.timestamp_us == ts

    def test_different_frames(self) -> None:
        """Test different MAVLink frames."""
        data_body = build_landing_target(
            angle_x=0.0,
            angle_y=0.0,
            distance_m=1.0,
            frame=MAV_FRAME_BODY_NED,
        )

        data_local = build_landing_target(
            angle_x=0.0,
            angle_y=0.0,
            distance_m=1.0,
            frame=MAV_FRAME_LOCAL_NED,
        )

        assert data_body.frame == MAV_FRAME_BODY_NED
        assert data_local.frame == MAV_FRAME_LOCAL_NED


class TestLandingTargetData:
    """Tests for LandingTargetData dataclass."""

    def test_creation(self) -> None:
        """Test dataclass creation."""
        data = LandingTargetData(
            timestamp_us=1000000,
            angle_x=0.1,
            angle_y=-0.1,
            distance_m=3.0,
            x_m=0.5,
            y_m=-0.5,
            z_m=3.0,
            position_valid=True,
            frame=MAV_FRAME_BODY_NED,
        )

        assert data.timestamp_us == 1000000
        assert data.angle_x == 0.1
        assert data.position_valid is True

    def test_angle_bounds(self) -> None:
        """Test angle values are in expected range."""
        import math

        # Angles should be in radians (typically small values)
        data = build_landing_target(
            angle_x=math.radians(10),  # 10 degrees
            angle_y=math.radians(-5),  # -5 degrees
            distance_m=10.0,
        )

        assert -math.pi <= data.angle_x <= math.pi
        assert -math.pi <= data.angle_y <= math.pi
