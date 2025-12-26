"""Unit tests for FSM control logic."""

import pytest
import time

from scandium.control.fsm import (
    LandingFSM,
    LandingState,
    SystemInputs,
    SystemOutputs,
)


class TestLandingFSM:
    """Tests for LandingFSM class."""

    def test_initial_state(self) -> None:
        """Test FSM starts in INIT state."""
        fsm = LandingFSM()
        assert fsm.state == LandingState.INIT

    def test_init_to_idle_transition(self) -> None:
        """Test transition from INIT to IDLE when connections established."""
        fsm = LandingFSM()

        inputs = SystemInputs(
            mavlink_connected=True,
            camera_connected=True,
        )

        output = fsm.tick(inputs)

        assert fsm.state == LandingState.IDLE

    def test_idle_to_search_on_arm(self) -> None:
        """Test transition from IDLE to SEARCH on arm command."""
        fsm = LandingFSM()

        # First get to IDLE
        inputs = SystemInputs(mavlink_connected=True, camera_connected=True)
        fsm.tick(inputs)
        assert fsm.state == LandingState.IDLE

        # Arm without target visible
        inputs.arm_command = True
        inputs.target_visible = False
        fsm.tick(inputs)

        assert fsm.state == LandingState.SEARCH

    def test_idle_to_acquire_with_target(self) -> None:
        """Test transition from IDLE to ACQUIRE when target visible."""
        fsm = LandingFSM()

        # Get to IDLE
        inputs = SystemInputs(mavlink_connected=True, camera_connected=True)
        fsm.tick(inputs)

        # Arm with target visible
        inputs.arm_command = True
        inputs.target_visible = True
        inputs.target_confidence = 0.8
        fsm.tick(inputs)

        assert fsm.state == LandingState.ACQUIRE

    def test_search_to_acquire_transition(self) -> None:
        """Test transition from SEARCH to ACQUIRE on target detection."""
        fsm = LandingFSM(consecutive_frames_for_acquire=3)

        # Get to SEARCH
        inputs = SystemInputs(mavlink_connected=True, camera_connected=True)
        fsm.tick(inputs)
        inputs.arm_command = True
        fsm.tick(inputs)
        assert fsm.state == LandingState.SEARCH

        # Simulate consecutive detections
        inputs.target_visible = True
        inputs.target_confidence = 0.8

        for _ in range(3):
            fsm.tick(inputs)

        assert fsm.state == LandingState.ACQUIRE

    def test_acquire_to_align_transition(self) -> None:
        """Test transition from ACQUIRE to ALIGN when filter stabilizes."""
        fsm = LandingFSM(max_variance=0.5)

        # Get to ACQUIRE
        inputs = SystemInputs(
            mavlink_connected=True,
            camera_connected=True,
            arm_command=True,
            target_visible=True,
            target_confidence=0.8,
        )
        fsm.tick(inputs)  # INIT -> IDLE
        fsm.tick(inputs)  # IDLE -> ACQUIRE
        assert fsm.state == LandingState.ACQUIRE

        # Low variance triggers transition
        inputs.variance = 0.3
        fsm.tick(inputs)

        assert fsm.state == LandingState.ALIGN

    def test_align_to_descend_transition(self) -> None:
        """Test transition from ALIGN to DESCEND on alignment."""
        fsm = LandingFSM(align_error_m=0.25)

        # Get to ALIGN state
        inputs = SystemInputs(
            mavlink_connected=True,
            camera_connected=True,
            arm_command=True,
            target_visible=True,
            target_confidence=0.8,
            variance=0.3,
        )
        fsm.tick(inputs)  # INIT -> IDLE
        fsm.tick(inputs)  # IDLE -> ACQUIRE
        fsm.tick(inputs)  # ACQUIRE -> ALIGN
        assert fsm.state == LandingState.ALIGN

        # Low lateral error triggers descent
        inputs.lateral_error_m = 0.2
        fsm.tick(inputs)

        assert fsm.state == LandingState.DESCEND

    def test_descend_to_touchdown(self) -> None:
        """Test transition from DESCEND to TOUCHDOWN on low altitude."""
        fsm = LandingFSM(touchdown_altitude_m=0.5)

        # Get to DESCEND state
        inputs = SystemInputs(
            mavlink_connected=True,
            camera_connected=True,
            arm_command=True,
            target_visible=True,
            target_confidence=0.8,
            variance=0.3,
            lateral_error_m=0.1,
            altitude_m=5.0,
        )

        # Progress through states
        for _ in range(4):
            fsm.tick(inputs)

        assert fsm.state == LandingState.DESCEND

        # Low altitude triggers touchdown
        inputs.altitude_m = 0.3
        fsm.tick(inputs)

        assert fsm.state == LandingState.TOUCHDOWN

    def test_human_detection_triggers_abort(self) -> None:
        """Test that human detection triggers ABORT."""
        fsm = LandingFSM()

        # Get to DESCEND state
        inputs = SystemInputs(
            mavlink_connected=True,
            camera_connected=True,
            arm_command=True,
            target_visible=True,
            target_confidence=0.8,
            variance=0.3,
            lateral_error_m=0.1,
        )

        for _ in range(4):
            fsm.tick(inputs)

        assert fsm.state == LandingState.DESCEND

        # Human detected
        inputs.human_present = True
        output = fsm.tick(inputs)

        assert fsm.state == LandingState.ABORT
        assert output.abort_reason == "human_present"

    def test_low_landability_triggers_abort(self) -> None:
        """Test that low landability score triggers ABORT."""
        fsm = LandingFSM(abort_landability=0.4)

        # Get to ACQUIRE state
        inputs = SystemInputs(
            mavlink_connected=True,
            camera_connected=True,
            arm_command=True,
            target_visible=True,
            target_confidence=0.8,
        )

        fsm.tick(inputs)
        fsm.tick(inputs)
        assert fsm.state == LandingState.ACQUIRE

        # Low landability
        inputs.landability_score = 0.2
        fsm.tick(inputs)

        assert fsm.state == LandingState.ABORT

    def test_connection_loss_triggers_failsafe(self) -> None:
        """Test that connection loss triggers FAILSAFE."""
        fsm = LandingFSM()

        # Get to SEARCH state
        inputs = SystemInputs(
            mavlink_connected=True,
            camera_connected=True,
            arm_command=True,
        )
        fsm.tick(inputs)
        fsm.tick(inputs)
        assert fsm.state == LandingState.SEARCH

        # Connection lost
        inputs.mavlink_connected = False
        fsm.tick(inputs)

        assert fsm.state == LandingState.FAILSAFE

    def test_external_abort_command(self) -> None:
        """Test that external abort command triggers ABORT."""
        fsm = LandingFSM()

        # Get to SEARCH state
        inputs = SystemInputs(
            mavlink_connected=True,
            camera_connected=True,
            arm_command=True,
        )
        fsm.tick(inputs)
        fsm.tick(inputs)

        # External abort
        inputs.abort_command = True
        output = fsm.tick(inputs)

        assert fsm.state == LandingState.ABORT
        assert output.abort_reason == "external_command"

    def test_output_publish_flag(self) -> None:
        """Test that publish flag is set in appropriate states."""
        fsm = LandingFSM()

        inputs = SystemInputs(
            mavlink_connected=True,
            camera_connected=True,
            arm_command=True,
            target_visible=True,
            target_confidence=0.8,
            variance=0.3,
        )

        # INIT/IDLE should not publish
        output = fsm.tick(inputs)
        assert not output.publish_landing_target or fsm.state == LandingState.IDLE

        # Get to ACQUIRE
        fsm.tick(inputs)
        output = fsm.tick(inputs)

        # ACQUIRE should publish
        if fsm.state in [
            LandingState.ACQUIRE,
            LandingState.ALIGN,
            LandingState.DESCEND,
        ]:
            assert output.publish_landing_target

    def test_reset(self) -> None:
        """Test FSM reset functionality."""
        fsm = LandingFSM()

        # Get to some state
        inputs = SystemInputs(mavlink_connected=True, camera_connected=True)
        fsm.tick(inputs)
        assert fsm.state == LandingState.IDLE

        # Reset
        fsm.reset()

        assert fsm.state == LandingState.INIT
