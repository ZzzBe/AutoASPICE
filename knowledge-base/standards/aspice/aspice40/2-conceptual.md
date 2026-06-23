# Automotive SPICE 4.0 - Conceptual Architecture

## Process Reference Model (PRM)

ASPICE 4.0 PRM extends ASPICE 3.1 with new process groups for ML and hardware development.

```
Automotive SPICE 4.0 Process Landscape

Primary Processes (ACQ, SPL, SYS, SWE, MLE, HWE)
    ↓ Work products
Supporting Processes (SUP)
    ↓ Quality & control
Management Processes (MAN)
    ↓ Planning & oversight
Process Improvement (PIM)
    ↓ Continuous improvement
Validation (VAL)
    ↓ User acceptance
Reuse (REU)
    ↓ Asset management
```

## New Process Groups

### MLE - Machine Learning Engineering

Critical for projects developing AI/ML-based automotive functions.

#### MLE.1: Machine Learning Requirements Analysis

**Purpose**: Derive ML requirements from software requirements and define ODD.

**Base Practices**:
- BP1: Identify software requirements requiring ML implementation
- BP2: Define ML functional requirements (inputs, outputs, expected behavior)
- BP3: Define data requirements (data types, quantity, quality requirements)
- BP4: Define ODD (operational conditions, boundary conditions)
- BP5: Establish bidirectional traceability to software requirements
- BP6: Communicate and review ML requirements

**Work Products**:
- 19-01: ML requirements specification
- 19-02: Data requirements specification
- 19-03: ODD definition document
- 13-22: Traceability record

**ODD Definition Example**:
```yaml
Operational Design Domain:
  name: "Highway Lane Keeping Assist"

  Operational Conditions:
    road_types: [highway, expressway]
    speed_range: [60, 150] km/h
    weather: [clear, light_rain]
    visibility: [day, night_with_streetlights]
    lane_markings: [solid, dashed]

  Boundary Conditions:
    construction_zones: not_supported
    severe_weather: not_supported
    emergency_vehicles: require_driver_intervention

  Limitations:
    min_curve_radius: 250m
    max_lateral_acceleration: 3 m/s²
```

#### MLE.2: Machine Learning Architecture

**Purpose**: Define ML model architecture, preprocessing/postprocessing, and hyperparameter ranges.

**Base Practices**:
- BP1: Select appropriate ML model type
- BP2: Define model architecture (layers, nodes, activation functions, etc.)
- BP3: Define preprocessing pipeline (data cleaning, feature extraction, normalization)
- BP4: Define postprocessing pipeline (result interpretation, threshold decisions)
- BP5: Define hyperparameter ranges
- BP6: Establish traceability to ML requirements

**Work Products**:
- 04-51: ML architecture document
- 01-54: Hyperparameter definition
- 19-04: Preprocessing/postprocessing specification

**ML Architecture Example**:
```yaml
Model Architecture:
  type: "CNN-based Object Detection"

  Input:
    image_size: [640, 480, 3]
    data_type: "RGB uint8"

  Preprocessing:
    - resize: [640, 480]
    - normalize: mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
    - augmentation: [flip, rotation±5°, brightness±10%]

  Model:
    backbone: "ResNet-50"
    feature_pyramid: true
    detection_head: "YOLO-style"

  Postprocessing:
    confidence_threshold: 0.7
    nms_threshold: 0.5
    class_mapping: {0: vehicle, 1: pedestrian, 2: cyclist}

  Hyperparameter Ranges:
    learning_rate: [1e-5, 1e-3]
    batch_size: [8, 32]
    weight_decay: [1e-6, 1e-4]
```

#### MLE.3: Machine Learning Training

**Purpose**: Train ML model using training data and optimize hyperparameters.

**Base Practices**:
- BP1: Prepare training data (collection, labeling, augmentation)
- BP2: Split dataset (training set, validation set, test set)
- BP3: Execute model training
- BP4: Optimize hyperparameters
- BP5: Evaluate model performance
- BP6: Document training process and results

**Work Products**:
- 19-05: Training dataset
- 19-06: Training log
- 19-07: Model file
- 01-54: Final hyperparameter values

#### MLE.4: Machine Learning Model Verification

**Purpose**: Verify ML model conforms to ML requirements, including ODD boundary verification.

**Base Practices**:
- BP1: Develop ML verification strategy
- BP2: Define verification scenarios (covering ODD)
- BP3: Execute functional verification
- BP4: Execute ODD boundary verification
- BP5: Execute adversarial verification
- BP6: Document verification results and establish traceability

**Work Products**:
- 19-08: ML verification strategy
- 19-09: ML verification cases
- 19-10: ML verification report

### HWE - Hardware Engineering

Critical for projects with hardware-software co-development.

#### HWE.1: Hardware Requirements Analysis

**Purpose**: Derive hardware requirements from system requirements.

**Base Practices**:
- BP1: Identify system requirements allocated to hardware
- BP2: Define hardware functional requirements
- BP3: Define hardware non-functional requirements (performance, power, environment)
- BP4: Define hardware interface requirements
- BP5: Establish traceability to system requirements
- BP6: Communicate and review hardware requirements

**Work Products**:
- 18-01: Hardware requirements specification
- 18-02: Hardware interface specification
- 13-22: Traceability record

#### HWE.2: Hardware Design

**Purpose**: Define hardware architecture and detailed design.

**Base Practices**:
- BP1: Develop hardware architectural design
- BP2: Allocate requirements to hardware components
- BP3: Define hardware component interfaces
- BP4: Develop hardware detailed design (schematics, PCB layout)
- BP5: Evaluate hardware design
- BP6: Establish traceability to requirements

**Work Products**:
- 18-03: Hardware architectural design document
- 18-04: Hardware detailed design document
- 18-05: Schematics
- 18-06: PCB design files

#### HWE.3: Hardware Design Verification

**Purpose**: Verify hardware design conforms to requirements.

**Base Practices**:
- BP1: Develop hardware design verification strategy
- BP2: Develop verification specification
- BP3: Verify hardware design (simulation, analysis)
- BP4: Establish traceability
- BP5: Ensure consistency
- BP6: Summarize and communicate results

**Work Products**:
- 18-07: Hardware design verification strategy
- 18-08: Hardware design verification specification
- 18-09: Hardware design verification report

#### HWE.4: Hardware Requirements Verification

**Purpose**: Verify hardware product conforms to requirements.

**Base Practices**:
- BP1: Develop hardware requirements verification strategy
- BP2: Develop verification specification
- BP3: Verify hardware product (physical testing)
- BP4: Establish traceability
- BP5: Ensure consistency
- BP6: Summarize and communicate results

**Work Products**:
- 18-10: Hardware requirements verification strategy
- 18-11: Hardware requirements verification specification
- 18-12: Hardware requirements verification report

## New Standalone Processes

### VAL.1: Validation

**Purpose**: Ensure system/software satisfies user needs and intended use.

**Base Practices**:
- BP1: Develop validation strategy
- BP2: Define validation measures (use scenarios, user acceptance tests)
- BP3: Select validation measures
- BP4: Execute validation
- BP5: Record validation results
- BP6: Establish traceability to user requirements

**Work Products**:
- 08-58: Validation strategy
- 08-59: Validation measures
- 08-57: Validation measure selection
- 13-24: Validation results

### SUP.11: ML Data Management

**Purpose**: Manage ML data collection, labeling, and versioning.

**Base Practices**:
- BP1: Develop ML data management strategy
- BP2: Define data collection requirements
- BP3: Define data labeling process
- BP4: Establish data versioning
- BP5: Ensure data quality
- BP6: Manage data storage and access

**Work Products**:
- 19-11: ML data management strategy
- 19-12: Data collection plan
- 19-13: Labeled dataset
- 19-14: Data quality report

### MAN.5: Risk Management

**Purpose**: Identify, analyze, and control project risks.

**Base Practices**:
- BP1: Develop risk management strategy
- BP2: Identify risks
- BP3: Analyze risks (probability, impact)
- BP4: Define mitigation measures
- BP5: Monitor and control risks
- BP6: Communicate risk status

**Work Products**:
- 15-31: Risk management strategy
- 15-32: Risk register
- 15-33: Risk mitigation plan

### MAN.6: Measurement

**Purpose**: Establish and maintain measurement system for management decisions.

**Base Practices**:
- BP1: Establish measurement objectives
- BP2: Define metrics
- BP3: Collect measurement data
- BP4: Analyze measurement results
- BP5: Report measurement results
- BP6: Use measurements for decisions

**Work Products**:
- 15-34: Measurement strategy
- 15-35: Metric definitions
- 15-36: Measurement reports

### REU.2: Reuse Product Management

**Purpose**: Identify, evaluate, and manage reusable products.

**Base Practices**:
- BP1: Develop reuse strategy
- BP2: Identify candidate reuse products
- BP3: Evaluate reuse products
- BP4: Qualify reuse products
- BP5: Maintain reuse product library
- BP6: Support reuse product integration

**Work Products**:
- 15-37: Reuse strategy
- 15-38: Reuse product catalog
- 15-39: Reuse product evaluation records

### PIM.3: Process Improvement

**Purpose**: Continuously improve organizational process capability.

**Base Practices**:
- BP1: Develop process improvement strategy
- BP2: Identify improvement opportunities
- BP3: Analyze improvement potential
- BP4: Implement improvements
- BP5: Evaluate improvement effectiveness
- BP6: Standardize successful improvements

**Work Products**:
- 15-40: Process improvement strategy
- 15-41: Improvement proposals
- 15-42: Improvement records

## Terminology Changes

### Testing → Verification

All testing-related processes now use "Verification" terminology:

| ASPICE 3.1 | ASPICE 4.0 |
|------------|------------|
| SYS.4 System Integration Test | SYS.4 System Integration and Integration Verification |
| SYS.5 System Qualification Test | SYS.5 System Qualification Verification |
| SWE.4 Software Unit Test | SWE.4 Software Unit Verification |
| SWE.5 Software Integration Test | SWE.5 Software Integration and Integration Verification |
| SWE.6 Software Qualification Test | SWE.6 Software Qualification Verification |

### New Key Terms

| Term | Definition |
|------|------------|
| Measure | Activity to achieve a specific intent |
| Metric | Quantifiable indicator matching an information need |
| ODD | Operational Design Domain - operating conditions for a function |
| Hyperparameter | Parameters controlling ML model training |

## Next Steps

- [3-mle-processes.md](3-mle-processes.md) - MLE detailed implementation
- [4-hwe-processes.md](4-hwe-processes.md) - HWE detailed implementation
- [5-new-processes.md](5-new-processes.md) - New processes detailed guide
- [../6-aspice40-changes.md](../6-aspice40-changes.md) - Complete change log

## References

- Automotive SPICE PAM v4.0 Process Reference Model
- Automotive SPICE PAM v4.0 Process Assessment Model
- ISO/IEC 33020:2015 Process measurement framework

---

**Document Version**: 1.0
**Last Updated**: 2026-03-25
**Intended Audience**: Process engineers, project managers, ASPICE coordinators
