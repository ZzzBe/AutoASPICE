# Automotive SPICE 4.0 - SYS Process Group Implementation Guide

## Overview

This document provides detailed implementation guidance for the System Engineering (SYS) process group in ASPICE 4.0.

> **Key Change from ASPICE 3.1**: SYS.4 and SYS.5 terminology updated from "Test" to "Verification".

---

## Terminology Changes

| ASPICE 3.1 | ASPICE 4.0 |
|------------|------------|
| SYS.4 System Integration and Integration Test | SYS.4 System Integration and Integration Verification |
| SYS.5 System Qualification Test | SYS.5 System Qualification Verification |

---

## SYS.1: Requirements Elicitation

### Purpose

Gather and analyze stakeholder requirements.

### Base Practices (ASPICE 4.0)

#### BP1: Obtain Customer Requirements and Requests

**Sources of Requirements**:
- Customer specifications
- Regulatory requirements
- Market analysis
- Legacy system constraints
- Safety requirements (from HARA)

**Requirements Collection Template**:
```markdown
## Stakeholder Requirement: SHR-XXX

### Source
- Customer: [OEM Name]
- Document: [Specification reference]
- Date: YYYY-MM-DD

### Requirement Text
The system shall [requirement text].

### Priority
- [Must have / Should have / Nice to have]

### Rationale
[Why this requirement exists]

### Acceptance Criteria
- [Measurable criteria]
```

#### BP2: Understand Stakeholder Needs

**Stakeholder Analysis**:
```yaml
Stakeholder Analysis:

Customer (OEM):
  needs:
    - Feature requirements
    - Cost targets
    - Timing constraints
  constraints:
    - Platform requirements
    - Supplier requirements

End Users:
  needs:
    - Usability
    - Performance
    - Safety

Regulators:
  requirements:
    - ISO 26262 (safety)
    - UNECE R155 (cybersecurity)
    - Local regulations
```

#### BP3: Define Functional and Non-Functional Requirements

**Requirements Categories**:
```markdown
## Functional Requirements
- What the system shall do
- Input/output relationships
- System behaviors

## Non-Functional Requirements
- Performance: timing, throughput
- Safety: ASIL requirements
- Security: cybersecurity requirements
- Reliability: MTBF, availability
- Environmental: temperature, vibration
```

### Work Products

| ID | Name | Description |
|----|------|-------------|
| 13-01 | Stakeholder Requirements Specification | Collected requirements |
| 13-02 | Customer Requirement Analysis | Analysis results |

---

## SYS.2: System Requirements Analysis

### Purpose

Transform stakeholder requirements into technical system requirements.

### Base Practices (ASPICE 4.0)

#### BP1: Specify System Requirements

**System Requirements Specification Template**:
```markdown
## System Requirement: SYS-REQ-XXX

### Traceability
- Source: SHR-XXX
- ASIL: [A/B/C/D/QM]

### Requirement Text
The system shall [requirement text].

### Classification
- Type: [Functional/Non-Functional]
- Category: [Performance/Safety/Interface/etc.]

### Verification Criteria
| Criterion | Value | Method |
|-----------|-------|--------|
| Response time | ≤ X ms | System verification |

### Allocation Candidate
- Software: [Y/N]
- Hardware: [Y/N]
- Mechanical: [Y/N]
```

#### BP2: Analyze System Requirements

**Analysis Checklist**:
```markdown
Completeness:
☐ All stakeholder requirements addressed
☐ All interfaces specified
☐ All operational modes covered
☐ Error handling specified

Correctness:
☐ Technical feasibility verified
☐ No conflicts with other requirements
☐ Domain expert review completed

Verifiability:
☐ Each requirement has verification criteria
☐ Quantitative values specified
☐ Verification method defined
```

#### BP3: Evaluate Impact on Operating Environment

**Impact Assessment**:
```yaml
Environmental Impact:

Vehicle Integration:
  - CAN bus load: [X% increase]
  - Power consumption: [X W]
  - Physical space: [X cm³]

System Interfaces:
  - New interfaces required: [list]
  - Modified interfaces: [list]
  - Bandwidth requirements: [X Mbps]
```

#### BP4: Develop Verification Criteria

**Verification Criteria Template**:
```yaml
Verification Criteria: VC-SYS-XXX
  requirement: SYS-REQ-XXX
  verification_methods:
    - Analysis: [description]
    - Inspection: [description]
    - Demonstration: [description]
    - Test: [description]

  acceptance_criteria:
    - criterion_1: [value]
    - criterion_2: [value]

  verification_level: System
```

#### BP5: Ensure Bidirectional Traceability

**Traceability Matrix**:
```markdown
| Stakeholder Req | System Req | Verification | Status |
|-----------------|------------|--------------|--------|
| SHR-001 | SYS-001, SYS-002 | VC-SYS-001 | Defined |
| SHR-002 | SYS-003 | VC-SYS-003 | Defined |
```

#### BP6: Communicate System Requirements

**Communication Checklist**:
```markdown
☐ Requirements reviewed by stakeholders
☐ Requirements approved by customer
☐ Requirements distributed to teams
☐ Change notification process established
```

### Work Products

| ID | Name | Description |
|----|------|-------------|
| 13-04 | System Requirements Specification | Complete system requirements |
| 13-19 | Verification Criteria | Verification approach |
| 13-22 | Traceability Record | Bidirectional traceability |

---

## SYS.3: System Architectural Design

### Purpose

Define system architecture allocating requirements to elements.

### Base Practices (ASPICE 4.0)

#### BP1: Develop System Architectural Design

**System Architecture Document**:
```markdown
## System Architecture Specification

### System Overview
[High-level description]

### System Block Diagram
```
┌─────────────────────────────────────────────────────┐
│                    Vehicle System                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │   ECU-1     │  │   ECU-2     │  │   ECU-3     │ │
│  │ (Control)   │  │ (Sensing)   │  │ (Comm)      │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │
│         │                │                │         │
│         └────────────────┴────────────────┘         │
│                          │                           │
│                    CAN/Ethernet                      │
└─────────────────────────────────────────────────────┘
```

### Element Descriptions
| Element | Type | Function | ASIL |
|---------|------|----------|------|
| ECU-1 | HW+SW | Control function | D |
| ECU-2 | HW+SW | Sensing function | D |
```

#### BP2: Allocate System Requirements to Elements

**Allocation Matrix**:
```markdown
| System Req | Element | Element Type | Notes |
|------------|---------|--------------|-------|
| SYS-001 | ECU-1 SW | Software | Main control |
| SYS-002 | ECU-1 HW | Hardware | MCU selection |
| SYS-003 | ECU-2 SW | Software | Sensor fusion |
```

#### BP3: Define Interfaces

**Interface Specification**:
```markdown
## System Interface: IF-SYS-XXX

### Type
- [Internal/External]

### Elements Connected
- Provider: [Element A]
- Consumer: [Element B]

### Interface Details
| Signal | Type | Range | Protocol |
|--------|------|-------|----------|
| Signal_1 | CAN | [0, 255] | CAN 2.0B |

### Timing Requirements
- Period: X ms
- Latency: ≤ X ms
```

#### BP4: Describe Dynamic Behavior

**System Sequence Diagram**:
```
Actor    ECU-1    ECU-2    ECU-3
   |        |        |        |
   | Input  |        |        |
   |------->|        |        |
   |        | Request|        |
   |        |------->|        |
   |        |        | Data   |
   |        |        |------->|
   |        | Response        |
   |<-------|        |        |
```

#### BP5: Define Evaluation Criteria

**Architecture Evaluation**:
```yaml
Evaluation Criteria:

Completeness:
  - All requirements allocated: ✓
  - All interfaces defined: ✓

Consistency:
  - No circular dependencies: ✓
  - ASIL segregation verified: ✓

Feasibility:
  - Resource budget verified: ✓
  - Technical risks identified: ✓
```

#### BP6: Ensure Bidirectional Traceability

```markdown
| System Req | Architecture Element | Interface | Status |
|------------|---------------------|-----------|--------|
| SYS-001 | ECU-1 SW Component A | IF-001 | Allocated |
```

### Work Products

| ID | Name | Description |
|----|------|-------------|
| 13-01 | System Architectural Design Specification | Architecture document |
| 13-02 | Interface Specification | Interface definitions |
| 13-22 | Traceability Record | Requirement to element |

---

## SYS.4: System Integration and Integration Verification

### Purpose

Integrate system elements and demonstrate interface compliance.

> **Note**: ASPICE 4.0 uses "Integration Verification" instead of "Integration Test".

### Base Practices (ASPICE 4.0)

#### BP1: Develop System Integration Strategy

**Integration Strategy**:
```yaml
System Integration Strategy:

1. Integration Phases:
   Phase 1: ECU-level integration
   Phase 2: Subsystem integration
   Phase 3: Full system integration

2. Integration Sequence:
   - Integrate ECUs in isolation
   - Integrate related ECUs
   - Integrate full vehicle system

3. Verification Approach:
   - Interface verification
   - Communication verification
   - Timing verification
```

#### BP2: Develop System Integration Verification Specification

**Integration Verification Case**:
```markdown
## VC-SYS-INT-XXX: System Integration Verification

### Integration Step
- [Phase and step description]

### Elements Integrated
- ECU-1, ECU-2

### Interfaces Verified
- IF-001: CAN interface between ECU-1 and ECU-2

### Verification Environment
- HIL system
- Real ECUs with production software

### Input Conditions
| Condition | Value |
|-----------|-------|
| CAN load | 50% |

### Expected Results
| Measurement | Expected |
|-------------|----------|
| Message latency | ≤ 5ms |
| Message accuracy | 100% |

### Pass Criteria
- All interfaces functional
- Timing requirements met
- No communication errors
```

#### BP3: Integrate System Elements

**Integration Procedure**:
```markdown
## Integration Procedure: SYS-INT-XXX

### Prerequisites
- All element verifications passed
- Integration environment ready

### Steps
1. Connect elements per integration plan
2. Power on in sequence
3. Initialize communication
4. Execute verification cases
5. Document results
```

#### BP4: Verify Integrated System Elements

**Verification Results**:
```markdown
| Integration Step | Interface | Result | Issues |
|------------------|-----------|--------|--------|
| Phase 1-Step 1 | IF-001 | PASS | - |
| Phase 1-Step 2 | IF-002 | PASS | - |
```

#### BP5: Establish Bidirectional Traceability

```markdown
| Interface | Requirement | Verification Case | Status |
|-----------|-------------|-------------------|--------|
| IF-001 | SYS-001 | VC-SYS-INT-001 | Verified |
```

#### BP6: Ensure Consistency with System Design

```markdown
☐ Integration follows architecture
☐ All interfaces verified
☐ Element interactions correct
```

#### BP7: Summarize and Communicate Results

### Work Products

| ID | Name | Description |
|----|------|-------------|
| 13-12 | System Integration Strategy | Integration approach |
| 13-23 | System Integration Verification Specification | Verification cases |
| 13-24 | System Integration Verification Report | Verification results |

---

## SYS.5: System Qualification Verification

### Purpose

Ensure system meets requirements.

> **Note**: ASPICE 4.0 uses "Qualification Verification" instead of "Qualification Test".

### Base Practices (ASPICE 4.0)

#### BP1: Develop System Qualification Verification Strategy

**Qualification Verification Strategy**:
```yaml
System Qualification Verification Strategy:

1. Verification Scope:
   - All system requirements
   - All safety requirements (ASIL)
   - All interface requirements

2. Verification Environment:
   - HIL system (real-time verification)
   - Vehicle prototype (final validation)
   - Production configuration

3. Coverage Requirements:
   - 100% requirement coverage
   - All ASIL scenarios verified
```

#### BP2: Develop System Qualification Verification Specification

**Qualification Verification Case**:
```markdown
## VC-SYS-QUAL-XXX: System Qualification Verification

### Requirement
- SYS-REQ-XXX: [Requirement text]

### ASIL
- [A/B/C/D]

### Verification Method
- [Analysis/Demonstration/Test]

### Verification Environment
- HIL System: [Configuration]
- Software Version: X.Y.Z

### Test Scenarios
| Scenario | Input | Expected Output |
|----------|-------|-----------------|
| Normal | [input] | [output] |
| Boundary | [input] | [output] |
| Fault | [input] | [output] |

### Pass Criteria
- All scenarios pass
- Timing requirements met
- Safety behavior correct
```

#### BP3: Verify Integrated System

**Verification Execution**:
```markdown
## VC-SYS-QUAL-XXX Execution Record

**Date**: YYYY-MM-DD
**System Version**: X.Y.Z
**Environment**: HIL System [ID]
**Result**: PASS/FAIL

### Results
| Scenario | Result | Notes |
|----------|--------|-------|
| Normal | PASS | - |
| Boundary | PASS | - |
| Fault | PASS | Safe state entered |

### Measurements
| Parameter | Expected | Actual | Status |
|-----------|----------|--------|--------|
| Response time | ≤ 100ms | 85ms | PASS |
```

#### BP4: Establish Bidirectional Traceability

```markdown
| System Req | Verification Case | Result | Evidence |
|------------|-------------------|--------|----------|
| SYS-001 | VC-SYS-QUAL-001 | PASS | Report_XYZ |
```

#### BP5: Ensure Consistency with Requirements

```markdown
☐ All requirements covered
☐ Verification environment correct
☐ All scenarios executed
☐ Results documented
```

#### BP6: Summarize and Communicate Results

**Qualification Verification Summary**:
```markdown
## System Qualification Verification Summary

### Statistics
| Metric | Value |
|--------|-------|
| Total Requirements | X |
| Requirements Verified | X |
| Pass Rate | 100% |
| Open Issues | 0 |

### ASIL Coverage
| ASIL | Requirements | Verified | Status |
|------|--------------|----------|--------|
| D | 50 | 50 | ✓ |
| B | 30 | 30 | ✓ |
| QM | 20 | 20 | ✓ |

### Recommendation
- [Ready/Not ready for SOP]
```

### Work Products

| ID | Name | Description |
|----|------|-------------|
| 13-25 | System Qualification Verification Strategy | Qualification approach |
| 13-26 | System Qualification Verification Specification | Qualification cases |
| 13-27 | System Qualification Verification Report | Qualification results |

---

## References

- Automotive SPICE PAM v4.0 SYS Process Group
- ISO 26262 System safety requirements
- [../6-aspice40-changes.md](../6-aspice40-changes.md) - Complete change log

---

**Document Version**: 1.0
**Last Updated**: 2026-03-25
**Intended Audience**: Systems engineers, integration engineers, verification engineers
