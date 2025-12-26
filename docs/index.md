# Scandium Documentation

Welcome to the Scandium precision landing system documentation. This documentation provides comprehensive technical reference, integration guides, and operational procedures for deploying and utilizing the Scandium system in unmanned aerial vehicle (UAV) applications.

## System Overview

Scandium is a production-grade precision landing system designed for UAV and multirotor platforms. The system enables autonomous precision landing on fiducial markers (ArUco/AprilTag) by publishing MAVLink LANDING_TARGET messages to compatible autopilot systems including PX4 and ArduPilot.

### Primary Capabilities

| Capability | Description |
|------------|-------------|
| Fiducial Detection | Multi-backend support for ArUco and AprilTag marker families |
| Pose Estimation | Camera-to-body frame transformation with temporal filtering |
| MAVLink Integration | Native LANDING_TARGET message publishing at configurable rates |
| Landability Analysis | Heuristic and ML-based landing zone safety assessment |
| State Machine Control | Deterministic FSM for complete landing sequence management |
| Simulation Support | AirSim and SITL integration for development and testing |

### Documentation Structure

- **[Architecture](architecture.md)**: System design, component interactions, and data flow
- **[MAVLink Integration](mavlink.md)**: Protocol implementation and message specifications
- **[PX4 Configuration](px4.md)**: PX4-specific setup and parameter tuning
- **[ArduPilot Configuration](ardupilot.md)**: ArduPilot-specific setup and parameter tuning
- **[Simulation](simulation.md)**: AirSim and SITL configuration for testing
- **[Landability](landability.md)**: Landing zone safety assessment algorithms
- **[Testing](testing.md)**: Unit, integration, and scenario testing procedures
- **[Deployment](deployment.md)**: Production deployment and operational guidelines

## Quick Start

### Prerequisites

- Python 3.11 or later
- Poetry package manager
- OpenCV 4.9.0 or later
- pymavlink 2.4.41 or later

### Installation

```bash
# Clone repository
git clone https://github.com/emrealtindag/scandium.git
cd scandium

# Install dependencies
poetry install

# Verify installation
poetry run scandium version
```

### Basic Execution

```bash
# Run with default configuration
poetry run scandium run --config configs/default.yaml

# Run AirSim simulation
poetry run scandium sim airsim --config configs/airsim_demo.yaml

# Execute diagnostics
poetry run scandium diagnostics --config configs/default.yaml
```

## Safety Considerations

Scandium is designed for safety-critical UAV operations. Before operational deployment, ensure:

1. **Complete calibration verification** of camera intrinsics and extrinsics
2. **Thorough SITL testing** of all operational scenarios
3. **Proper failsafe configuration** on the autopilot system
4. **Compliance with local aviation regulations** as applicable to UAV operations

Refer to the [Deployment](deployment.md) section for comprehensive safety checklists and operational procedures.

## License

Scandium is released under the Apache License 2.0. See the LICENSE file for details.
