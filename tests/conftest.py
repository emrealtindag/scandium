"""
Shared pytest fixtures for Scandium tests.
"""

import pytest
import numpy as np
import cv2

from scandium.perception.camera import Frame
from scandium.perception.calib import CameraIntrinsics, CameraExtrinsics


@pytest.fixture
def sample_bgr_frame() -> np.ndarray:
    """Create sample BGR image."""
    return np.zeros((720, 1280, 3), dtype=np.uint8)


@pytest.fixture
def sample_frame() -> Frame:
    """Create sample Frame object."""
    image = np.zeros((720, 1280, 3), dtype=np.uint8)
    return Frame(image_bgr=image, timestamp_s=0.0, frame_id=0)


@pytest.fixture
def default_intrinsics() -> CameraIntrinsics:
    """Create default camera intrinsics."""
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


@pytest.fixture
def downward_facing_extrinsics() -> CameraExtrinsics:
    """Create downward-facing camera extrinsics."""
    return CameraExtrinsics.downward_facing()


@pytest.fixture
def aruco_marker_image() -> np.ndarray:
    """Generate image with centered ArUco marker."""
    width, height = 1280, 720
    marker_size = 200

    image = np.ones((height, width, 3), dtype=np.uint8) * 255

    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100)
    marker = cv2.aruco.generateImageMarker(aruco_dict, 1, marker_size)
    marker_bgr = cv2.cvtColor(marker, cv2.COLOR_GRAY2BGR)

    x_offset = (width - marker_size) // 2
    y_offset = (height - marker_size) // 2

    image[y_offset : y_offset + marker_size, x_offset : x_offset + marker_size] = (
        marker_bgr
    )

    return image
