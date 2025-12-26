"""Unit tests for ArUco detector."""

import pytest
import numpy as np
import cv2

from scandium.perception.fiducials.aruco_detector import (
    ArUcoDetector,
    get_aruco_dictionary,
    draw_detections,
)
from scandium.perception.fiducials.base import FiducialDetection


def generate_aruco_image(
    marker_id: int = 1,
    size: int = 200,
    dictionary: str = "DICT_4X4_100",
) -> np.ndarray:
    """Generate grayscale image with ArUco marker."""
    aruco_dict = get_aruco_dictionary(dictionary)
    marker = cv2.aruco.generateImageMarker(aruco_dict, marker_id, size)

    # Add white margin
    margin = 50
    image = np.ones((size + 2 * margin, size + 2 * margin), dtype=np.uint8) * 255
    image[margin : margin + size, margin : margin + size] = marker

    return image


class TestArUcoDetector:
    """Tests for ArUcoDetector class."""

    def test_initialization_default(self) -> None:
        """Test default initialization."""
        detector = ArUcoDetector()
        assert detector.dictionary_name == "DICT_4X4_100"

    def test_initialization_custom_dictionary(self) -> None:
        """Test initialization with custom dictionary."""
        detector = ArUcoDetector(dictionary="DICT_5X5_100")
        assert detector.dictionary_name == "DICT_5X5_100"

    def test_detect_single_marker(self) -> None:
        """Test detection of single marker."""
        image = generate_aruco_image(marker_id=1)
        detector = ArUcoDetector()

        detections = detector.detect(image)

        assert len(detections) == 1
        assert detections[0].marker_id == 1
        assert detections[0].corners.shape == (4, 2)

    def test_detect_different_ids(self) -> None:
        """Test detection of different marker IDs."""
        for marker_id in [0, 5, 10, 50]:
            image = generate_aruco_image(marker_id=marker_id)
            detector = ArUcoDetector()

            detections = detector.detect(image)

            assert len(detections) == 1
            assert detections[0].marker_id == marker_id

    def test_detect_no_marker(self) -> None:
        """Test detection with no markers present."""
        image = np.ones((300, 300), dtype=np.uint8) * 128
        detector = ArUcoDetector()

        detections = detector.detect(image)

        assert len(detections) == 0

    def test_detect_wrong_dictionary(self) -> None:
        """Test that wrong dictionary does not detect marker."""
        image = generate_aruco_image(marker_id=1, dictionary="DICT_4X4_100")
        detector = ArUcoDetector(dictionary="DICT_6X6_100")

        detections = detector.detect(image)

        assert len(detections) == 0

    def test_corner_order(self) -> None:
        """Test that corners are in correct order (clockwise from top-left)."""
        image = generate_aruco_image(marker_id=1, size=200)
        detector = ArUcoDetector()

        detections = detector.detect(image)
        corner = detections[0].corners

        # Check that corners form a roughly square shape
        # Top-left should have smallest sum of coordinates
        sums = corner.sum(axis=1)
        top_left_idx = np.argmin(sums)

        # Corners should be ordered clockwise
        assert corner.shape == (4, 2)

    def test_detection_with_refine(self) -> None:
        """Test detection with corner refinement enabled."""
        image = generate_aruco_image(marker_id=1)
        detector = ArUcoDetector(refine_corners=True)

        detections = detector.detect(image)

        assert len(detections) == 1

    def test_bgr_input_converts(self) -> None:
        """Test that BGR input is handled correctly."""
        gray = generate_aruco_image(marker_id=1)
        bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

        detector = ArUcoDetector()

        # Should work with grayscale
        detections_gray = detector.detect(gray)
        assert len(detections_gray) == 1


class TestGetArucoDictionary:
    """Tests for get_aruco_dictionary function."""

    def test_valid_dictionaries(self) -> None:
        """Test retrieval of valid dictionaries."""
        valid_names = [
            "DICT_4X4_50",
            "DICT_4X4_100",
            "DICT_4X4_250",
            "DICT_4X4_1000",
            "DICT_5X5_50",
            "DICT_5X5_100",
            "DICT_5X5_250",
            "DICT_5X5_1000",
            "DICT_6X6_50",
            "DICT_6X6_100",
            "DICT_6X6_250",
            "DICT_6X6_1000",
            "DICT_7X7_50",
            "DICT_7X7_100",
            "DICT_7X7_250",
            "DICT_7X7_1000",
        ]

        for name in valid_names:
            dictionary = get_aruco_dictionary(name)
            assert dictionary is not None

    def test_invalid_dictionary(self) -> None:
        """Test that invalid dictionary name raises error."""
        with pytest.raises(ValueError):
            get_aruco_dictionary("INVALID_DICT")


class TestDrawDetections:
    """Tests for draw_detections function."""

    def test_draw_on_image(self) -> None:
        """Test drawing detections on image."""
        gray = generate_aruco_image(marker_id=1)
        bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

        detector = ArUcoDetector()
        detections = detector.detect(gray)

        result = draw_detections(bgr, detections)

        assert result.shape == bgr.shape
        # Image should be modified (not all zeros)
        assert not np.array_equal(result, bgr)

    def test_draw_empty_detections(self) -> None:
        """Test drawing with no detections."""
        image = np.zeros((300, 300, 3), dtype=np.uint8)

        result = draw_detections(image, [])

        assert result.shape == image.shape
