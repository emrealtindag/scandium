"""Unit tests for pose filtering."""

import pytest
import numpy as np
from numpy.testing import assert_array_almost_equal

from scandium.perception.pose.filtering import ExpSmoother, FilteredPose, KalmanFilter3D


class TestExpSmoother:
    """Tests for ExpSmoother."""

    def test_initialization(self) -> None:
        """Test smoother initialization."""
        smoother = ExpSmoother(alpha=0.5)
        assert not smoother.is_initialized

    def test_first_measurement(self) -> None:
        """Test first measurement handling."""
        smoother = ExpSmoother(alpha=0.5)
        measurement = np.array([1.0, 2.0, 3.0])

        result = smoother.update(measurement, timestamp=0.0)

        assert smoother.is_initialized
        assert_array_almost_equal(result.position, measurement)

    def test_smoothing_effect(self) -> None:
        """Test that smoothing reduces noise."""
        smoother = ExpSmoother(alpha=0.3)

        # First measurement
        smoother.update(np.array([1.0, 1.0, 1.0]), timestamp=0.0)

        # Second measurement with jump
        result = smoother.update(np.array([2.0, 2.0, 2.0]), timestamp=0.1)

        # Should be smoothed (not equal to second measurement)
        assert result.position[0] < 2.0
        assert result.position[0] > 1.0

    def test_outlier_rejection(self) -> None:
        """Test outlier rejection."""
        smoother = ExpSmoother(alpha=0.3, outlier_threshold=2.0)

        # Initialize with normal position
        smoother.update(np.array([0.0, 0.0, 0.0]), timestamp=0.0)

        # Large jump (outlier)
        result = smoother.update(np.array([100.0, 100.0, 100.0]), timestamp=0.1)

        # Position should not jump to outlier
        assert result.position[0] < 50.0

    def test_low_alpha_more_smoothing(self) -> None:
        """Test that low alpha provides more smoothing."""
        smoother_low = ExpSmoother(alpha=0.1)
        smoother_high = ExpSmoother(alpha=0.9)

        m1 = np.array([0.0, 0.0, 0.0])
        m2 = np.array([10.0, 10.0, 10.0])

        smoother_low.update(m1, timestamp=0.0)
        smoother_high.update(m1, timestamp=0.0)

        result_low = smoother_low.update(m2, timestamp=0.1)
        result_high = smoother_high.update(m2, timestamp=0.1)

        # Low alpha should have position closer to first measurement
        assert result_low.position[0] < result_high.position[0]

    def test_reset(self) -> None:
        """Test smoother reset."""
        smoother = ExpSmoother(alpha=0.5)
        smoother.update(np.array([1.0, 2.0, 3.0]), timestamp=0.0)

        assert smoother.is_initialized

        smoother.reset()

        assert not smoother.is_initialized


class TestKalmanFilter3D:
    """Tests for KalmanFilter3D."""

    def test_initialization(self) -> None:
        """Test filter initialization."""
        kf = KalmanFilter3D()
        assert not kf.is_initialized

    def test_first_measurement(self) -> None:
        """Test first measurement handling."""
        kf = KalmanFilter3D()
        measurement = np.array([1.0, 2.0, 3.0])

        result = kf.update(measurement)

        assert kf.is_initialized
        assert_array_almost_equal(result.position, measurement)

    def test_velocity_estimation(self) -> None:
        """Test velocity estimation."""
        kf = KalmanFilter3D(dt=0.1)

        # Two measurements with movement
        kf.update(np.array([0.0, 0.0, 0.0]))
        result = kf.update(np.array([1.0, 0.0, 0.0]))

        # Should estimate positive X velocity
        assert result.velocity[0] > 0

    def test_prediction_smoothing(self) -> None:
        """Test that Kalman filter smooths noisy measurements."""
        kf = KalmanFilter3D(measurement_noise=0.5)

        # Add noisy measurements
        kf.update(np.array([0.0, 0.0, 0.0]))
        kf.update(np.array([0.1, 0.0, 0.0]))
        result = kf.update(np.array([5.0, 0.0, 0.0]))  # Outlier-ish

        # Position should be smoothed
        assert result.position[0] < 5.0

    def test_reset(self) -> None:
        """Test filter reset."""
        kf = KalmanFilter3D()
        kf.update(np.array([1.0, 2.0, 3.0]))

        assert kf.is_initialized

        kf.reset()

        assert not kf.is_initialized


class TestFilteredPose:
    """Tests for FilteredPose dataclass."""

    def test_creation(self) -> None:
        """Test FilteredPose creation."""
        pose = FilteredPose(
            position=np.array([1.0, 2.0, 3.0]),
            variance=np.array([0.1, 0.1, 0.1]),
        )

        assert pose.is_valid
        assert_array_almost_equal(pose.position, [1.0, 2.0, 3.0])
