"""
Integration tests for Scandium perception pipeline.

Tests the complete perception pipeline from frame input to pose output
without requiring physical hardware.
"""

import pytest
import numpy as np
import cv2
from numpy.testing import assert_array_almost_equal

from scandium.perception.camera import Frame
from scandium.perception.calib import CameraIntrinsics, CameraExtrinsics
from scandium.perception.fiducials.aruco_detector import ArUcoDetector
from scandium.perception.fiducials.base import filter_by_id
from scandium.perception.pose.pnp import estimate_pose_from_corners, PoseEstimate
from scandium.perception.pose.filtering import ExpSmoother
from scandium.perception.pose.frames import cam_to_body, body_to_mavlink_fields


def generate_aruco_marker_image(
    marker_id: int = 1,
    marker_size_px: int = 200,
    image_size: tuple[int, int] = (1280, 720),
    marker_center: tuple[int, int] | None = None,
) -> np.ndarray:
    """
    Generate synthetic image containing an ArUco marker.

    Args:
        marker_id: ArUco marker ID.
        marker_size_px: Marker size in pixels.
        image_size: Output image size (width, height).
        marker_center: Marker center position (default: image center).

    Returns:
        BGR image containing the marker.
    """
    width, height = image_size

    if marker_center is None:
        marker_center = (width // 2, height // 2)

    # Create white background
    image = np.ones((height, width, 3), dtype=np.uint8) * 255

    # Generate ArUco marker
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100)
    marker_img = cv2.aruco.generateImageMarker(aruco_dict, marker_id, marker_size_px)
    marker_bgr = cv2.cvtColor(marker_img, cv2.COLOR_GRAY2BGR)

    # Place marker at center
    x_offset = marker_center[0] - marker_size_px // 2
    y_offset = marker_center[1] - marker_size_px // 2

    # Ensure marker fits within image
    x_offset = max(0, min(x_offset, width - marker_size_px))
    y_offset = max(0, min(y_offset, height - marker_size_px))

    image[
        y_offset : y_offset + marker_size_px, x_offset : x_offset + marker_size_px
    ] = marker_bgr

    return image


@pytest.fixture
def default_intrinsics() -> CameraIntrinsics:
    """Create default camera intrinsics for testing."""
    return CameraIntrinsics(
        fx=1280.0,
        fy=1280.0,
        cx=640.0,
        cy=360.0,
        dist_coeffs=np.zeros(5, dtype=np.float64),
    )


@pytest.fixture
def identity_extrinsics() -> CameraExtrinsics:
    """Create identity camera extrinsics."""
    return CameraExtrinsics.identity()


class TestDetectionPipeline:
    """Integration tests for fiducial detection."""

    def test_aruco_detection_synthetic(self) -> None:
        """Test ArUco detection on synthetic image."""
        image = generate_aruco_marker_image(marker_id=1, marker_size_px=200)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        detector = ArUcoDetector(dictionary="DICT_4X4_100")
        detections = detector.detect(gray)

        assert len(detections) == 1
        assert detections[0].marker_id == 1
        assert detections[0].corners.shape == (4, 2)

    def test_multiple_markers(self) -> None:
        """Test detection of multiple markers."""
        # Create image with two markers
        image = np.ones((720, 1280, 3), dtype=np.uint8) * 255
        aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100)

        # Marker 1 at left
        marker1 = cv2.aruco.generateImageMarker(aruco_dict, 1, 150)
        marker1_bgr = cv2.cvtColor(marker1, cv2.COLOR_GRAY2BGR)
        image[285:435, 200:350] = marker1_bgr

        # Marker 2 at right
        marker2 = cv2.aruco.generateImageMarker(aruco_dict, 2, 150)
        marker2_bgr = cv2.cvtColor(marker2, cv2.COLOR_GRAY2BGR)
        image[285:435, 930:1080] = marker2_bgr

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        detector = ArUcoDetector(dictionary="DICT_4X4_100")
        detections = detector.detect(gray)

        assert len(detections) == 2
        ids = {d.marker_id for d in detections}
        assert ids == {1, 2}

    def test_id_filtering(self) -> None:
        """Test marker ID filtering."""
        image = generate_aruco_marker_image(marker_id=5)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        detector = ArUcoDetector(dictionary="DICT_4X4_100")
        detections = detector.detect(gray)

        # Filter for ID 1 only (marker is ID 5)
        filtered = filter_by_id(detections, allowlist=[1])
        assert len(filtered) == 0

        # Filter for ID 5
        filtered = filter_by_id(detections, allowlist=[5])
        assert len(filtered) == 1


class TestPoseEstimationPipeline:
    """Integration tests for pose estimation pipeline."""

    def test_detection_to_pose(self, default_intrinsics: CameraIntrinsics) -> None:
        """Test complete detection to pose pipeline."""
        image = generate_aruco_marker_image(marker_id=1, marker_size_px=200)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Detect marker
        detector = ArUcoDetector(dictionary="DICT_4X4_100")
        detections = detector.detect(gray)

        assert len(detections) == 1

        # Estimate pose
        pose = estimate_pose_from_corners(
            detections[0].corners,
            marker_size_m=0.2,
            intrinsics=default_intrinsics,
        )

        assert pose.success
        assert pose.distance_m > 0
        assert pose.reproj_error_px < 5.0

    def test_pose_with_filter(self, default_intrinsics: CameraIntrinsics) -> None:
        """Test pose estimation with temporal filtering."""
        smoother = ExpSmoother(alpha=0.5)

        # Generate multiple frames
        for i in range(5):
            image = generate_aruco_marker_image(marker_id=1, marker_size_px=200)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            detector = ArUcoDetector(dictionary="DICT_4X4_100")
            detections = detector.detect(gray)

            if detections:
                pose = estimate_pose_from_corners(
                    detections[0].corners,
                    marker_size_m=0.2,
                    intrinsics=default_intrinsics,
                )

                if pose.success:
                    filtered = smoother.update(pose.tvec, timestamp=float(i) * 0.05)
                    assert filtered.is_valid


class TestFrameTransformPipeline:
    """Integration tests for frame transformation pipeline."""

    def test_camera_to_mavlink(
        self,
        default_intrinsics: CameraIntrinsics,
        identity_extrinsics: CameraExtrinsics,
    ) -> None:
        """Test camera frame to MAVLink field conversion."""
        image = generate_aruco_marker_image(marker_id=1, marker_size_px=200)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Detect and estimate pose
        detector = ArUcoDetector(dictionary="DICT_4X4_100")
        detections = detector.detect(gray)

        pose = estimate_pose_from_corners(
            detections[0].corners,
            marker_size_m=0.2,
            intrinsics=default_intrinsics,
        )

        assert pose.success

        # Transform to body frame
        p_body = cam_to_body(pose.tvec, identity_extrinsics)

        # Convert to MAVLink fields
        x, y, z, angle_x, angle_y, valid = body_to_mavlink_fields(p_body)

        assert valid is True
        assert z > 0  # Target should be below (positive Z down)


class TestEndToEndPipeline:
    """End-to-end integration tests."""

    def test_full_perception_pipeline(
        self,
        default_intrinsics: CameraIntrinsics,
    ) -> None:
        """Test complete perception pipeline."""
        # Generate test frame
        image = generate_aruco_marker_image(
            marker_id=1,
            marker_size_px=200,
            marker_center=(640, 360),
        )

        frame = Frame(
            image_bgr=image,
            timestamp_s=0.0,
            frame_id=0,
        )

        # Run detection
        detector = ArUcoDetector(dictionary="DICT_4X4_100")
        detections = detector.detect(frame.to_gray())

        assert len(detections) > 0, "No markers detected"

        # Filter by ID
        target_detections = filter_by_id(detections, allowlist=[1])
        assert len(target_detections) == 1, "Target marker not found"

        # Estimate pose
        pose = estimate_pose_from_corners(
            target_detections[0].corners,
            marker_size_m=0.2,
            intrinsics=default_intrinsics,
        )

        assert pose.success, "Pose estimation failed"
        assert pose.reproj_error_px < 5.0, "High reprojection error"

        # Apply filter
        smoother = ExpSmoother(alpha=0.35)
        filtered = smoother.update(pose.tvec, timestamp=frame.timestamp_s)

        assert filtered.is_valid

        # Generate MAVLink fields
        extrinsics = CameraExtrinsics.identity()
        p_body = cam_to_body(filtered.position, extrinsics)
        x, y, z, angle_x, angle_y, valid = body_to_mavlink_fields(p_body)

        assert valid is True

        # Verify reasonable values
        distance = np.sqrt(x**2 + y**2 + z**2)
        assert distance > 0, "Invalid distance"
        assert abs(angle_x) < np.pi, "Invalid angle_x"
        assert abs(angle_y) < np.pi, "Invalid angle_y"
