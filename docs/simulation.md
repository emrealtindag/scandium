# Simulation Guide

This document provides comprehensive guidance for using simulation environments with the Scandium precision landing system.

## Supported Platforms

Scandium supports multiple simulation platforms for development, testing, and validation:

| Platform | Fidelity | Camera | Physics | Best For |
|----------|----------|--------|---------|----------|
| AirSim | High | Native | Unreal Engine | Full integration testing |
| ArduPilot SITL | Medium | External | JSBSim | Algorithm development |
| PX4 SITL + Gazebo | High | Gazebo | ODE/Bullet | PX4-specific testing |

## AirSim Integration

### Prerequisites

1. Microsoft AirSim installed and configured
2. Unreal Engine 4.27 or 5.x
3. AirSim Python client (`pip install airsim`)

### AirSim Settings

Configure AirSim settings file (`~/Documents/AirSim/settings.json`):

```json
{
  "SettingsVersion": 1.2,
  "SimMode": "Multirotor",
  "ClockSpeed": 1.0,
  "Vehicles": {
    "Drone1": {
      "VehicleType": "SimpleFlight",
      "AutoCreate": true,
      "X": 0, "Y": 0, "Z": 0,
      "Cameras": {
        "0": {
          "CaptureSettings": [
            {
              "ImageType": 0,
              "Width": 1280,
              "Height": 720,
              "FOV_Degrees": 90
            }
          ],
          "X": 0, "Y": 0, "Z": 0.3,
          "Pitch": -90, "Roll": 0, "Yaw": 0
        }
      }
    }
  }
}
```

### Camera Configuration

The downward-facing camera is configured with:

- **Position**: (0, 0, 0.3) meters below vehicle center
- **Orientation**: Pitch -90 degrees (facing down)
- **Resolution**: 1280x720 pixels
- **FOV**: 90 degrees

### Launch Procedure

```bash
# 1. Start AirSim (Blocks or custom environment)
./AirSimNH.sh  # Linux
# or
AirSimNH.exe  # Windows

# 2. Launch Scandium
poetry run scandium sim airsim --config configs/airsim_demo.yaml
```

### Marker Placement

Place ArUco markers in the AirSim environment:

1. Create a plane mesh with marker texture
2. Position at ground level
3. Ensure marker ID matches target_id_allowlist

## ArduPilot SITL

### Prerequisites

1. ArduPilot repository cloned
2. SITL build completed
3. MAVProxy (optional)

### Launch SITL

```bash
# Using Scandium script
./scripts/run_sitl_ardupilot.sh --speedup 1

# Manual launch
cd ~/ardupilot
python3 Tools/autotest/sim_vehicle.py \
    --vehicle=copter \
    --frame=quad \
    --home=40.072842,32.866287,584,0 \
    --no-mavproxy \
    -w
```

### Connect Scandium

```bash
poetry run scandium run --config configs/ardupilot_sitl.yaml
```

### Mission Commands

Use MAVProxy or MAVSDK to command precision landing:

```python
# Python example with MAVSDK
from mavsdk import System

async def precision_land():
    drone = System()
    await drone.connect(system_address="udp://:14550")
    await drone.action.land()
```

## PX4 SITL

### Prerequisites

1. PX4-Autopilot repository cloned
2. Gazebo Classic or Gazebo Garden installed
3. ROS 2 (optional, for advanced integration)

### Launch SITL

```bash
# Using Scandium script
./scripts/run_sitl_px4.sh --airframe iris --headless

# Manual launch
cd ~/PX4-Autopilot
make px4_sitl_default gazebo-classic
```

### Connect Scandium

```bash
poetry run scandium run --config configs/px4_sitl.yaml
```

### Gazebo Marker Setup

Add landing pad to Gazebo world:

```xml
<model name="landing_pad">
  <static>true</static>
  <link name="link">
    <visual name="visual">
      <geometry>
        <plane>
          <normal>0 0 1</normal>
          <size>1 1</size>
        </plane>
      </geometry>
      <material>
        <script>
          <uri>model://landing_pad/materials/scripts/landing_pad.material</uri>
          <name>LandingPad/ArUco</name>
        </script>
      </material>
    </visual>
  </link>
</model>
```

## Scenario Testing

### Scenario Structure

Scenarios are defined in YAML format:

```yaml
id: wind_disturbance
name: Wind Disturbance Test
description: Landing under wind conditions

setup:
  initial_altitude_m: 15.0
  marker_position: [0.0, 0.0, 0.0]
  wind_speed_mps: 5.0
  wind_direction_deg: 90

steps:
  - name: Initialize
    action: initialize
    timeout_s: 10
    
  - name: Detect Target
    action: wait_detection
    params:
      max_wait_s: 30
    expected:
      marker_detected: true

  - name: Execute Landing
    action: land
    timeout_s: 60
    expected:
      touchdown: true
      error_m: 0.3

pass_criteria:
  landing_error_max_m: 0.5
  detection_rate_min: 0.9
```

### Running Scenarios

```bash
# Run specific scenario
poetry run scandium scenario run --id smoke

# Run all scenarios
poetry run scandium scenario run --all

# Generate report
poetry run scandium scenario report --output results/
```

## Performance Benchmarking

### Latency Measurement

```bash
python scripts/benchmark_latency.py --iterations 1000
```

Metrics collected:

| Metric | Target | Description |
|--------|--------|-------------|
| Detection latency | <10 ms | ArUco detection time |
| Pose estimation | <5 ms | solvePnP execution |
| Total pipeline | <20 ms | End-to-end latency |
| Throughput | >30 Hz | Sustainable frame rate |

### System Resource Usage

Monitor during simulation:

```bash
# CPU and memory
htop

# GPU (if using CUDA)
nvidia-smi

# Network throughput
iftop
```

## Troubleshooting

### AirSim Connection Failed

1. Verify AirSim is running and accessible
2. Check IP address configuration
3. Ensure firewall allows connection
4. Confirm vehicle name matches configuration

### SITL Not Starting

1. Verify ArduPilot/PX4 is properly built
2. Check for port conflicts (14550, 14540)
3. Review SITL output for errors
4. Ensure all dependencies are installed

### Camera Feed Issues

1. Verify camera configuration in settings
2. Check camera orientation and position
3. Confirm image type matches expectations
4. Test with direct API call
