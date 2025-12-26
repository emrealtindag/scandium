"""Unit tests for coordinate frame transformations."""

import pytest
import numpy as np
from numpy.testing import assert_array_almost_equal

from scandium.perception.pose.frames import (
    Transform3D,
    Pose3D,
    cam_to_body,
    body_to_mavlink_fields,
    compute_angles_from_camera,
)
from scandium.perception.calib import CameraExtrinsics


class TestTransform3D:
    """Tests for Transform3D."""

    def test_identity_transform(self) -> None:
        """Test identity transformation."""
        t = Transform3D(R=np.eye(3), t=np.zeros(3))
        point = np.array([1.0, 2.0, 3.0])
        result = t.apply(point)
        assert_array_almost_equal(result, point)

    def test_translation_only(self) -> None:
        """Test translation-only transform."""
        t = Transform3D(R=np.eye(3), t=np.array([1.0, 2.0, 3.0]))
        point = np.array([0.0, 0.0, 0.0])
        result = t.apply(point)
        assert_array_almost_equal(result, [1.0, 2.0, 3.0])

    def test_rotation_90_z(self) -> None:
        """Test 90 degree rotation about Z axis."""
        R = np.array(
            [
                [0, -1, 0],
                [1, 0, 0],
                [0, 0, 1],
            ],
            dtype=np.float64,
        )
        t = Transform3D(R=R, t=np.zeros(3))

        point = np.array([1.0, 0.0, 0.0])
        result = t.apply(point)
        assert_array_almost_equal(result, [0.0, 1.0, 0.0])

    def test_inverse(self) -> None:
        """Test inverse transformation."""
        R = np.array(
            [
                [0, -1, 0],
                [1, 0, 0],
                [0, 0, 1],
            ],
            dtype=np.float64,
        )
        t = Transform3D(R=R, t=np.array([1.0, 2.0, 3.0]))

        point = np.array([1.0, 1.0, 1.0])
        transformed = t.apply(point)
        inverse = t.inverse()
        restored = inverse.apply(transformed)

        assert_array_almost_equal(restored, point)

    def test_compose(self) -> None:
        """Test transform composition."""
        t1 = Transform3D(R=np.eye(3), t=np.array([1.0, 0.0, 0.0]))
        t2 = Transform3D(R=np.eye(3), t=np.array([0.0, 1.0, 0.0]))

        composed = t1.compose(t2)
        point = np.array([0.0, 0.0, 0.0])
        result = composed.apply(point)

        # Should translate by (1, 1, 0)
        assert_array_almost_equal(result, [1.0, 1.0, 0.0])


class TestCamToBody:
    """Tests for camera-to-body transformation."""

    def test_identity_extrinsics(self) -> None:
        """Test with identity extrinsics."""
        extrinsics = CameraExtrinsics.identity()
        p_cam = np.array([1.0, 2.0, 3.0])
        p_body = cam_to_body(p_cam, extrinsics)
        assert_array_almost_equal(p_body, p_cam)

    def test_downward_facing_camera(self) -> None:
        """Test with downward-facing camera extrinsics."""
        extrinsics = CameraExtrinsics.downward_facing()

        # Camera +Z (forward) -> Body -Z (down)
        p_cam = np.array([0.0, 0.0, 1.0])
        p_body = cam_to_body(p_cam, extrinsics)

        # Should map to -Z in body
        assert p_body[2] < 0


class TestBodyToMavlinkFields:
    """Tests for body-to-MAVLink conversion."""

    def test_target_below_centered(self) -> None:
        """Test target directly below vehicle."""
        p_body = np.array([0.0, 0.0, 5.0])  # 5m below
        x, y, z, angle_x, angle_y, valid = body_to_mavlink_fields(p_body)

        assert x == 0.0
        assert y == 0.0
        assert z == 5.0
        assert abs(angle_x) < 0.01
        assert abs(angle_y) < 0.01
        assert valid is True

    def test_target_offset_forward(self) -> None:
        """Test target offset forward."""
        p_body = np.array([2.0, 0.0, 5.0])  # 2m forward, 5m down
        x, y, z, angle_x, angle_y, valid = body_to_mavlink_fields(p_body)

        assert x == 2.0
        assert angle_x > 0  # Positive angle when target is forward


class TestComputeAnglesFromCamera:
    """Tests for camera angle computation."""

    def test_centered_target(self) -> None:
        """Test target centered in camera view."""
        tvec = np.array([0.0, 0.0, 5.0])  # 5m forward
        angle_x, angle_y = compute_angles_from_camera(tvec)

        assert abs(angle_x) < 0.01
        assert abs(angle_y) < 0.01

    def test_target_right(self) -> None:
        """Test target to the right in camera frame."""
        tvec = np.array([1.0, 0.0, 5.0])  # 1m right, 5m forward
        angle_x, angle_y = compute_angles_from_camera(tvec)

        assert angle_x > 0  # Positive angle for right
        assert abs(angle_y) < 0.01
