# Automotive SPICE 4.0 - MLE Process Group Implementation Guide

## Overview

This document provides detailed implementation guidance for the Machine Learning Engineering (MLE) process group, which is new in ASPICE 4.0.

---

## MLE.1: Machine Learning Requirements Analysis

### Purpose

Derive ML requirements from software requirements and define the Operational Design Domain (ODD).

### Base Practices Implementation

#### BP1: Identify ML-Candidate Requirements

**Objective**: Determine which software requirements should be implemented using ML.

**Selection Criteria**:
```yaml
ML Implementation Considerations:
  Suitable for ML:
    - Pattern recognition from data (image classification, object detection)
    - Complex mappings without clear rules (natural language understanding)
    - Noisy sensor data interpretation (sensor fusion)
    - Learning from examples is feasible

  NOT Suitable for ML:
    - Safety-critical logic with deterministic requirements
    - Simple rule-based functions
    - Requirements with 100% coverage mandates
    - Functions requiring explainability at all times
```

**Example**:
```
Software Requirement SWE-REQ-ADAS-001:
"The system shall detect vehicles in the forward path within 100m range"

ML Suitability Analysis:
- Pattern recognition task: YES
- Large dataset available: YES
- Real-time requirement (100ms): YES
- Training data collection feasible: YES
- Conclusion: SUITABLE FOR ML IMPLEMENTATION
```

#### BP2: Define ML Functional Requirements

**Template**:
```markdown
## ML Functional Requirement: ML-REQ-[ID]

### Source Software Requirement
- SWE-REQ-XXX

### ML Function Description
[Brief description of the ML function]

### Input Specification
| Input | Type | Range | Frequency |
|-------|------|-------|-----------|
| Camera image | RGB uint8 | 640×480×3 | 30 Hz |

### Output Specification
| Output | Type | Range | Update Rate |
|--------|------|-------|-------------|
| Detected objects | List of BoundingBox | - | 30 Hz |

### Performance Requirements
| Metric | Requirement |
|--------|-------------|
| Detection accuracy | ≥ 95% (IoU ≥ 0.5) |
| Inference time | ≤ 50 ms |
| False positive rate | ≤ 1% |

### Safety Requirements (if applicable)
| ASIL | Requirement |
|------|-------------|
| B | Detection confidence threshold ≥ 0.7 |
```

#### BP3: Define Data Requirements

**Data Requirements Specification**:
```yaml
Data Requirements Document: DR-001

1. Data Types:
   - Training data: Labeled images with vehicle annotations
   - Validation data: Separate labeled dataset
   - Test data: Independent labeled dataset

2. Data Quantity:
   - Training: Minimum 50,000 images
   - Validation: Minimum 5,000 images
   - Test: Minimum 5,000 images

3. Data Quality:
   - Label accuracy: ≥ 99%
   - Image resolution: 640×480 minimum
   - Annotation format: COCO JSON

4. Data Diversity:
   - Weather: [clear, rain, fog, snow]
   - Lighting: [day, night, dawn/dusk]
   - Geographic: [highway, urban, rural]
   - Vehicle types: [car, truck, motorcycle, bus]

5. Data Sources:
   - Internal data collection: 60%
   - Public datasets (KITTI, COCO): 30%
   - Synthetic data: 10%

6. Data Labeling:
   - Labeling tool: CVAT
   - Labeler training required: Yes
   - Quality assurance: Double annotation + review
```

#### BP4: Define ODD (Operational Design Domain)

**ODD Definition Template**:
```yaml
Operational Design Domain (ODD)

Document ID: ODD-ADAS-001
Version: 1.0
Date: 2026-03-25

1. Operational Conditions:

   1.1 Road Infrastructure:
   - Road types: Highway, expressway
   - Lane markings: Solid or dashed white/yellow lines
   - Number of lanes: 2 or more per direction

   1.2 Environmental Conditions:
   - Weather: Clear, light rain (< 5mm/h)
   - Visibility: ≥ 200m
   - Temperature: -20°C to +50°C
   - Lighting: Day, night with streetlights

   1.3 Traffic Conditions:
   - Traffic density: Low to medium
   - Speed range: 0 to 150 km/h
   - Surrounding vehicles: Normal traffic flow

   1.4 Operational Scenarios:
   - Lane keeping on highway
   - Adaptive cruise control
   - Emergency braking for obstacles

2. Boundary Conditions:

   2.1 Supported Conditions:
   - Highway driving with clear lane markings
   - Standard lane widths (3.5m ± 0.5m)
   - Curvature radius ≥ 250m

   2.2 Unsupported Conditions:
   - Construction zones
   - Severe weather (heavy rain, snow, fog)
   - Emergency vehicle encounters
   - Toll booths

   2.3 Degradation Conditions:
   - Sensor occlusion: Reduce speed, increase following distance
   - Uncertain detection: Issue warning to driver

3. System Limitations:

   3.1 Detection Limitations:
   - Minimum detection distance: 5m
   - Maximum detection distance: 100m
   - Minimum object size: 20×20 pixels

   3.2 Performance Limitations:
   - Maximum processing latency: 100ms
   - Maximum false positive rate: 1% per km
   - Minimum detection accuracy: 95%

4. Handover Conditions:

   4.1 Driver Takeover Requirements:
   - System degradation detected
   - ODD boundary approaching
   - Fault detected

   4.2 Takeover Time:
   - Warning time: ≥ 10 seconds before ODD exit
   - HMI indication: Visual + auditory
```

#### BP5: Establish Traceability

**Traceability Matrix**:
```markdown
| SW Req | ML Req | Data Req | ODD Reference |
|--------|--------|----------|---------------|
| SWE-001 | ML-001, ML-002 | DR-001 | ODD-ADAS-001 §1.1 |
| SWE-002 | ML-003 | DR-002 | ODD-ADAS-001 §2.1 |
```

---

## MLE.2: Machine Learning Architecture

### Purpose

Define ML model architecture, preprocessing/postprocessing, and hyperparameter ranges.

### Base Practices Implementation

#### BP1: Select Model Type

**Model Selection Decision Tree**:
```
Problem Type?
├─ Object Detection
│  ├─ Real-time required?
│  │  ├─ Yes → YOLO, SSD, RetinaNet
│  │  └─ No → Faster R-CNN, DETR
│  └─ Accuracy priority?
│     ├─ High → Two-stage detectors
│     └─ Balanced → One-stage detectors
├─ Semantic Segmentation
│  ├─ Real-time required?
│  │  ├─ Yes → BiSeNet, Fast-SCNN
│  │  └─ No → DeepLab, UNet
├─ Classification
│  ├─ Embedded deployment?
│  │  ├─ Yes → MobileNet, EfficientNet-Lite
│  │  └─ No → ResNet, EfficientNet
└─ Sequence Modeling
   ├─ Long sequences?
   │  ├─ Yes → Transformer
   │  └─ No → LSTM, GRU
```

#### BP2: Define Model Architecture

**Architecture Specification Template**:
```yaml
Model Architecture Specification

Model Name: VehicleDetector_v1
Model Type: CNN-based Object Detection
Framework: PyTorch 2.0

1. Model Structure:

   Backbone:
     type: ResNet-50
     pretrained: ImageNet
     freeze_first_n_layers: 2

   Feature Pyramid Network (FPN):
     input_levels: [C3, C4, C5]
     output_channels: 256
     num_levels: 5

   Detection Head:
     type: YOLOv8-style
     num_anchors_per_location: 3
     num_classes: 4

2. Input/Output Specification:

   Input:
     image:
       shape: [batch, 3, 640, 640]
       dtype: float32
       normalization: ImageNet mean/std
     metadata:
       camera_calibration: CameraMatrix
       timestamp: uint64

   Output:
     detections:
       shape: [batch, max_detections, 6]
       format: [x1, y1, x2, y2, confidence, class_id]
       max_detections: 100

3. Layer Details:

   Convolutional Layers:
   - Conv1: in=3, out=64, kernel=7×7, stride=2
   - Conv2_x: 3 blocks, out=256
   - Conv3_x: 4 blocks, out=512
   - Conv4_x: 6 blocks, out=1024
   - Conv5_x: 3 blocks, out=2048

   Detection Heads:
   - Classification head: 3 conv layers + 1 fc
   - Regression head: 3 conv layers + 1 fc

4. Model Size:
   - Total parameters: 25.6M
   - Model file size: 98 MB (FP32)
   - Model file size: 25 MB (INT8 quantized)
```

#### BP3: Define Preprocessing Pipeline

**Preprocessing Specification**:
```yaml
Preprocessing Pipeline

1. Data Loading:
   - Format: JPEG/PNG images
   - Decode: RGB channels
   - Initial size: Variable

2. Preprocessing Steps:

   Step 1: Resize
     target_size: [640, 640]
     method: bilinear interpolation
     preserve_aspect_ratio: true
     padding: gray (114, 114, 114)

   Step 2: Color Space Conversion
     source: RGB
     target: RGB (no conversion for this model)

   Step 3: Normalization
     mean: [0.485, 0.456, 0.406]
     std: [0.229, 0.224, 0.225]
     formula: (pixel / 255.0 - mean) / std

   Step 4: Tensor Conversion
     dtype: float32
     layout: NCHW

3. Data Augmentation (Training Only):

   Geometric:
   - Random horizontal flip: p=0.5
   - Random rotation: ±5 degrees
   - Random scaling: [0.8, 1.2]
   - Random crop: min_area=0.7

   Photometric:
   - Random brightness: ±10%
   - Random contrast: ±10%
   - Random saturation: ±10%
   - Color jitter: p=0.3
```

#### BP4: Define Postprocessing Pipeline

**Postprocessing Specification**:
```yaml
Postprocessing Pipeline

1. Raw Output Processing:

   Step 1: Confidence Filtering
     threshold: 0.5
     operation: Filter boxes with confidence < threshold

   Step 2: Class-wise Processing
     operation: Apply class-specific thresholds
     thresholds:
       vehicle: 0.7
       pedestrian: 0.6
       cyclist: 0.6
       motorcycle: 0.65

   Step 3: Non-Maximum Suppression (NMS)
     iou_threshold: 0.5
     operation: Remove overlapping boxes
     class_agnostic: false

   Step 4: Coordinate Transformation
     operation: Convert from normalized to pixel coordinates
     formula: box_pixel = box_norm × image_size

2. Output Formatting:

   Detection Result:
     timestamp: uint64
     num_detections: uint32
     detections:
       - class_id: uint8
         confidence: float32
         bbox: [x, y, w, h]  # pixel coordinates
         tracking_id: uint32 (optional)

3. Safety Checks:

   Validity Verification:
   - Check: confidence in [0, 1]
   - Check: bbox within image bounds
   - Check: bbox dimensions > 0

   Anomaly Detection:
   - Detection count threshold: max 100
   - Confidence variance check: not all same value
```

#### BP5: Define Hyperparameter Ranges

**Hyperparameter Definition**:
```yaml
Hyperparameter Configuration

1. Training Hyperparameters:

   Learning Rate:
     initial_value: 0.001
     search_range: [1e-5, 1e-2]
     schedule: cosine_annealing
     warmup_epochs: 5

   Batch Size:
     initial_value: 16
     search_range: [4, 32]
     constraint: GPU memory ≤ 8GB

   Optimizer:
     type: AdamW
     betas: [0.9, 0.999]
     weight_decay: 0.0001
     search_range: [1e-6, 1e-3]

2. Model Hyperparameters:

   Backbone:
     freeze_bn: true
     dropblock_prob: 0.1

   Detection Head:
     focal_loss_alpha: 0.25
     focal_loss_gamma: 2.0
     iou_loss_type: giou

3. Data Hyperparameters:

   Augmentation:
     mosaic_prob: 0.5
     mixup_prob: 0.1

4. Hyperparameter Search Strategy:

   Method: Bayesian Optimization
   Search Space: Combined ranges above
   Objective: mAP@0.5 on validation set
   Max Trials: 50
   Early Stopping: 10 trials without improvement
```

---

## MLE.3: Machine Learning Training

### Purpose

Train ML model using training data and optimize hyperparameters.

### Base Practices Implementation

#### BP1: Prepare Training Data

**Data Preparation Checklist**:
```markdown
☐ Data collection completed
  - Source data acquired
  - Legal/compliance review passed
  - Data ownership confirmed

☐ Data labeling completed
  - Labeling guidelines defined
  - Labelers trained
  - Quality control process defined

☐ Data annotation completed
  - Annotations in correct format (COCO JSON)
  - Annotation quality verified (≥ 99% accuracy)
  - Disagreement resolution process followed

☐ Data split performed
  - Training set: 80% (40,000 images)
  - Validation set: 10% (5,000 images)
  - Test set: 10% (5,000 images)
  - Stratified split by scenario type

☐ Data versioning established
  - Dataset version: v1.0.0
  - Version control system: DVC
  - Data lineage documented
```

#### BP2: Execute Model Training

**Training Configuration**:
```yaml
Training Configuration

Experiment ID: EXP-2026-03-25-001
Model: VehicleDetector_v1
Dataset: Dataset_v1.0.0

Training Parameters:
  epochs: 100
  batch_size: 16
  learning_rate: 0.001
  optimizer: AdamW
  weight_decay: 0.0001

Hardware:
  gpu: NVIDIA A100 80GB
  num_gpus: 4
  distributed: true

Checkpointing:
  save_every: 5 epochs
  keep_last_n: 3
  save_best: true
  metric_for_best: mAP@0.5

Logging:
  log_every: 100 iterations
  tensorboard: true
  wandb: true
  project: vehicle-detection

Early Stopping:
  monitor: val_mAP
  patience: 10 epochs
  min_delta: 0.001
```

#### BP3: Optimize Hyperparameters

**Hyperparameter Optimization Log**:
```markdown
## Hyperparameter Search Log

### Trial 1 (Baseline)
- learning_rate: 0.001
- batch_size: 16
- weight_decay: 0.0001
- Result: mAP@0.5 = 0.912

### Trial 15 (Best)
- learning_rate: 0.0008
- batch_size: 24
- weight_decay: 0.00005
- Result: mAP@0.5 = 0.934

### Final Configuration
- Selected hyperparameters from Trial 15
- Validation performance: mAP@0.5 = 0.934
- Test performance: mAP@0.5 = 0.928
```

#### BP4: Document Training Results

**Training Report Template**:
```markdown
# Training Report

## Experiment Summary
- Experiment ID: EXP-2026-03-25-001
- Model: VehicleDetector_v1
- Dataset: Dataset_v1.0.0 (50,000 images)

## Training Configuration
- Framework: PyTorch 2.0
- Hardware: 4× NVIDIA A100 80GB
- Training time: 12 hours 34 minutes

## Final Model Performance

### Validation Set
| Metric | Value |
|--------|-------|
| mAP@0.5 | 0.934 |
| mAP@0.5:0.95 | 0.712 |
| Precision | 0.921 |
| Recall | 0.945 |

### Test Set
| Metric | Value |
|--------|-------|
| mAP@0.5 | 0.928 |
| mAP@0.5:0.95 | 0.698 |
| Precision | 0.915 |
| Recall | 0.938 |

### Per-Class Performance
| Class | mAP@0.5 | Precision | Recall |
|-------|---------|-----------|--------|
| Vehicle | 0.952 | 0.941 | 0.963 |
| Pedestrian | 0.891 | 0.878 | 0.902 |
| Cyclist | 0.885 | 0.865 | 0.895 |
| Motorcycle | 0.883 | 0.872 | 0.891 |

## Artifacts
- Model weights: model_v1.0.pt
- Training logs: logs/exp-001/
- TensorBoard: tensorboard --logdir logs/exp-001/
```

---

## MLE.4: Machine Learning Model Verification

### Purpose

Verify ML model conforms to ML requirements, including ODD boundary verification.

### Base Practices Implementation

#### BP1: Develop ML Verification Strategy

**Verification Strategy Document**:
```yaml
ML Verification Strategy

1. Verification Levels:

   Level 1: Functional Verification
   - Verify model outputs for typical inputs
   - Test all specified input types
   - Verify output format compliance

   Level 2: Performance Verification
   - Accuracy metrics on test set
   - Latency measurement on target hardware
   - Memory footprint verification

   Level 3: ODD Boundary Verification
   - Test at ODD boundaries
   - Test outside ODD conditions
   - Degradation behavior verification

   Level 4: Adversarial Verification
   - Adversarial input testing
   - Corner case testing
   - Robustness verification

2. Test Environment:
   - Hardware: Target ECU (NVIDIA Orin)
   - Software: Production inference engine
   - Configuration: Production settings

3. Pass/Fail Criteria:
   - All functional tests: 100% pass
   - Performance metrics: Meet requirements
   - ODD boundary: Documented behavior
   - No safety-critical failures
```

#### BP2: Define Verification Scenarios

**Test Scenario Coverage Matrix**:
```markdown
| Scenario Category | ODD Reference | Test Cases | Coverage |
|-------------------|---------------|------------|----------|
| Daylight highway | §1.1, §1.2 | TC-ODD-001~020 | 100% |
| Night highway | §1.2 | TC-ODD-021~040 | 100% |
| Rain conditions | §1.2 | TC-ODD-041~060 | 100% |
| ODD boundary | §2 | TC-ODD-061~080 | 100% |
| ODD exit | §2.2 | TC-ODD-081~100 | 100% |
```

#### BP3: Execute Functional Verification

**Functional Test Cases**:
```markdown
## TC-FUNC-001: Vehicle Detection Accuracy

**Objective**: Verify vehicle detection meets accuracy requirement

**Preconditions**:
- Model loaded and initialized
- Test dataset prepared (5,000 images)

**Test Steps**:
1. Run inference on all test images
2. Calculate mAP@0.5
3. Compare with requirement (≥ 95%)

**Expected Result**: mAP@0.5 ≥ 0.95

**Actual Result**: PASS (mAP@0.5 = 0.928)

**Notes**: Slightly below target, accepted with waiver
```

#### BP4: Execute ODD Boundary Verification

**ODD Boundary Test Cases**:
```markdown
## TC-ODD-061: Heavy Rain (Outside ODD)

**ODD Reference**: §2.2 - Unsupported Conditions

**Objective**: Verify model behavior in heavy rain

**Test Conditions**:
- Rain intensity: 20 mm/h
- Visibility: 50m

**Expected Behavior**:
- Detection confidence should decrease
- System should indicate degradation
- No false high-confidence detections

**Test Result**: PASS
- Average confidence dropped from 0.85 to 0.62
- Degradation flag correctly set
- No false positives above threshold 0.7

---

## TC-ODD-065: Construction Zone (Outside ODD)

**ODD Reference**: §2.2 - Unsupported Conditions

**Objective**: Verify model behavior in construction zone

**Test Conditions**:
- Construction zone with lane closures
- Temporary lane markings

**Expected Behavior**:
- Detection rate may decrease
- No false lane assignments
- Driver takeover prompt

**Test Result**: PASS
- Vehicle detection still functional
- Lane detection correctly flagged uncertain
- System prompted driver takeover
```

#### BP5: Execute Adversarial Verification

**Adversarial Test Cases**:
```markdown
## TC-ADV-001: Adversarial Patch Attack

**Objective**: Verify robustness to adversarial patches

**Test Method**:
- Apply adversarial patch to test images
- Measure detection performance degradation

**Test Configuration**:
- Patch type: White-box adversarial
- Patch size: 10% of image

**Acceptance Criteria**:
- No more than 20% drop in detection rate
- No false detections caused by patch

**Test Result**: PASS
- Detection rate drop: 12%
- No false detections introduced
```

---

## Work Products Summary

| Work Product | ID | Description |
|--------------|----|----|
| ML Requirements Specification | 19-01 | Detailed ML requirements |
| Data Requirements Specification | 19-02 | Data quantity and quality requirements |
| ODD Definition Document | 19-03 | Operational Design Domain definition |
| ML Architecture Document | 04-51 | Model architecture specification |
| Hyperparameter Definition | 01-54 | Hyperparameter ranges and final values |
| Preprocessing/Postprocessing Spec | 19-04 | Data pipeline specification |
| Training Dataset | 19-05 | Versioned training data |
| Training Log | 19-06 | Training process documentation |
| Model File | 19-07 | Trained model weights |
| ML Verification Strategy | 19-08 | Verification approach |
| ML Verification Cases | 19-09 | Test case specifications |
| ML Verification Report | 19-10 | Verification results |

---

## References

- Automotive SPICE PAM v4.0 MLE Process Group
- ISO/SAE 21434 (Cybersecurity) for ML adversarial testing
- [6-aspice40-changes.md](../6-aspice40-changes.md) - Complete change log

---

**Document Version**: 1.0
**Last Updated**: 2026-03-25
**Intended Audience**: ML engineers, data scientists, verification engineers
