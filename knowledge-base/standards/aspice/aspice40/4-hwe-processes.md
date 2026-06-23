# Automotive SPICE 4.0 - HWE Process Group Implementation Guide

## Overview

This document provides detailed implementation guidance for the Hardware Engineering (HWE) process group, which is new in ASPICE 4.0.

---

## HWE.1: Hardware Requirements Analysis

### Purpose

Derive hardware requirements from system requirements.

### Base Practices Implementation

#### BP1: Identify Hardware-Allocated Requirements

**Requirements Allocation Matrix**:
```markdown
| System Req | Allocation | HW Requirement | Notes |
|------------|------------|----------------|-------|
| SYS-001 | Hardware | HW-REQ-001 | Sensor interface |
| SYS-002 | Software | - | Processing algorithm |
| SYS-003 | Both | HW-REQ-002, SWE-REQ-003 | Safety mechanism |
```

#### BP2: Define Hardware Functional Requirements

**Hardware Functional Requirements Template**:
```markdown
## Hardware Functional Requirement: HW-REQ-[ID]

### Source System Requirement
- SYS-REQ-XXX

### Functional Description
[Description of what the hardware shall do]

### Input/Output Specification
| Signal | Type | Range | Frequency |
|--------|------|-------|-----------|
| INPUT_1 | Analog | 0-5V | DC-1kHz |

### Performance Requirements
| Parameter | Requirement |
|-----------|-------------|
| Response time | ≤ X ms |
| Accuracy | ± X % |

### Interface Requirements
- Connector type: [specification]
- Pin assignment: [table]
```

#### BP3: Define Hardware Non-Functional Requirements

**Non-Functional Requirements Categories**:
```yaml
Non-Functional Hardware Requirements:

1. Performance:
   - Processing throughput: X MIPS
   - Memory bandwidth: X MB/s
   - Interface speed: X Mbps

2. Power:
   - Operating voltage: 12V ± 2V
   - Power consumption: ≤ X W (normal), ≤ Y W (peak)
   - Sleep mode current: ≤ Z mA

3. Environmental:
   - Operating temperature: -40°C to +85°C
   - Storage temperature: -40°C to +125°C
   - Humidity: 0% to 95% RH (non-condensing)
   - Vibration: Per ISO 16750-3
   - EMC: Per CISPR 25 / ISO 11452

4. Reliability:
   - MTBF: ≥ X hours
   - Design life: ≥ Y years
   - Failure rate: ≤ Z FIT

5. Safety:
   - ASIL capability: [A/B/C/D]
   - Diagnostic coverage: ≥ X %
```

#### BP4: Define Hardware Interface Requirements

**Hardware Interface Specification Template**:
```markdown
## Hardware Interface Specification

### Interface: IF-HW-XXX

**Type**: [Connector/Bus/Wireless]

**Physical Layer**:
- Connector: TE 1-2271454-2
- Pin count: 48
- Mounting: PCB through-hole

**Signal Definition**:
| Pin | Signal | Type | Description |
|-----|--------|------|-------------|
| 1 | VCC | Power | +12V supply |
| 2 | GND | Power | Ground |
| 3 | CAN_H | Signal | CAN High |
| 4 | CAN_L | Signal | CAN Low |

**Electrical Characteristics**:
| Parameter | Min | Typ | Max | Unit |
|-----------|-----|-----|-----|------|
| VIH | 2.0 | - | 5.5 | V |
| VIL | -0.5 | - | 0.8 | V |

**Timing Requirements**:
- Setup time: ≥ 10 ns
- Hold time: ≥ 5 ns
```

---

## HWE.2: Hardware Design

### Purpose

Define hardware architecture and detailed design.

### Base Practices Implementation

#### BP1: Develop Hardware Architectural Design

**Hardware Architecture Document Template**:
```markdown
## Hardware Architecture Specification

### 1. System Overview

#### Block Diagram
```
┌─────────────────────────────────────────────────────┐
│                    ECU Main Board                     │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐       │
│  │ MCU       │  │ Power     │  │ Comm      │       │
│  │ (Core)    │  │ Supply    │  │ Interface │       │
│  │           │  │           │  │           │       │
│  │ - ARM     │  │ - DC/DC   │  │ - CAN     │       │
│  │   Cortex  │  │ - LDO     │  │ - LIN     │       │
│  │ - RAM     │  │ - Monitor │  │ - Ethernet│       │
│  │ - Flash   │  │           │  │           │       │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘       │
│        │              │              │              │
│        └──────────────┴──────────────┘              │
│                       │                              │
│  ┌────────────────────┴────────────────────┐       │
│  │             Peripheral Interface          │       │
│  │  - ADC  - PWM  - GPIO  - SPI  - I2C      │       │
│  └──────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────┘
```

### 2. Component Specification

| Component | Part Number | Supplier | ASIL |
|-----------|-------------|----------|------|
| MCU | S32G3xx | NXP | D |
| PMIC | TLF35584 | Infineon | D |
| CAN Transceiver | TJA1043 | NXP | B |

### 3. Power Architecture

```
12V Battery
     │
     ▼
┌─────────┐    ┌─────────┐    ┌─────────┐
│ Reverse │    │  DC/DC  │    │   LDO   │
│ Polarity│───▶│ 5V/3A   │───▶│ 3.3V/1A │
│ Protect │    │         │    │         │
└─────────┘    └─────────┘    └─────────┘
                    │              │
                    ▼              ▼
              ┌─────────────────────┐
              │   MCU & Peripherals  │
              └─────────────────────┘
```
```

#### BP2: Allocate Requirements to Hardware Components

**Hardware Requirements Allocation Matrix**:
```markdown
| HW Requirement | Component | Verification Method |
|----------------|-----------|---------------------|
| HW-REQ-001 | MCU | Design review |
| HW-REQ-002 | PMIC | Simulation + Test |
| HW-REQ-003 | CAN Transceiver | Test |
```

#### BP3: Define Hardware Component Interfaces

**Component Interface Matrix**:
```markdown
| Component A | Interface | Component B | Signal Type |
|-------------|-----------|-------------|-------------|
| MCU | SPI_0 | External Flash | Digital |
| MCU | CAN_0 | CAN Transceiver | Digital |
| PMIC | PGOOD | MCU GPIO | Digital |
| PMIC | VOUT | MCU VDD | Power |
```

#### BP4: Develop Hardware Detailed Design

**Schematic Design Guidelines**:
```markdown
## Schematic Design Checklist

### Power Supply
☐ Input protection (reverse polarity, overvoltage)
☐ Decoupling capacitors placed near IC power pins
☐ Power sequencing correct
☐ Ground planes adequate

### Signal Integrity
☐ High-speed signals impedance controlled
☐ Termination resistors for transmission lines
☐ Differential pairs length matched
☐ Crosstalk mitigation

### EMC Design
☐ Ferrite beads on external interfaces
☐ Filter capacitors on I/O
☐ Grounded guard traces
☐ Crystal oscillator layout per datasheet

### Safety
☐ Current limiting on power paths
☐ Fusing on power input
☐ Diagnostic circuits for critical signals
☐ Watchdog connection verified
```

**PCB Design Guidelines**:
```markdown
## PCB Design Checklist

### Layer Stack-up
☐ Layer count adequate for signal integrity
☐ Ground planes continuous
☐ Power planes sized for current
☐ Impedance control layers identified

### Component Placement
☐ Components placed per signal flow
☐ High-speed components close together
☐ Thermal considerations addressed
☐ Test points accessible

### Routing
☐ Trace widths adequate for current
☐ Clearance meets safety requirements
☐ Differential pairs routed together
☐ Length matching where required

### Manufacturing
☐ DFM rules followed
☐ Solder mask defined
☐ Silkscreen readable
☐ Panelization specified
```

---

## HWE.3: Hardware Design Verification

### Purpose

Verify hardware design conforms to requirements (simulation and analysis).

### Base Practices Implementation

#### BP1: Develop Hardware Design Verification Strategy

**Design Verification Strategy**:
```yaml
Hardware Design Verification Strategy

1. Verification Methods:

   Simulation:
   - SPICE simulation for analog circuits
   - Signal integrity simulation
   - Power integrity simulation
   - Thermal simulation

   Analysis:
   - Derating analysis
   - MTBF prediction (MIL-HDBK-217)
   - FMEA for hardware
   - EMC pre-compliance analysis

   Review:
   - Schematic review
   - PCB layout review
   - BOM review

2. Verification Scope:
   - All circuits verified by simulation or analysis
   - All interfaces verified for signal integrity
   - All safety circuits verified by FMEA

3. Tools:
   - SPICE: LTspice, PSpice
   - SI/PI: Cadence Sigrity, HyperLynx
   - Thermal: ANSYS Icepak
   - Reliability: Relex, RAM Commander
```

#### BP2: Develop Verification Specification

**Simulation Test Cases**:
```markdown
## SIM-001: Power Supply Startup

**Objective**: Verify power supply startup sequence

**Simulation Setup**:
- Input: 12V step at t=0
- Load: 50% of rated load
- Temperature: 25°C

**Measurements**:
| Signal | Expected | Tolerance |
|--------|----------|-----------|
| VOUT_5V | 5.0V | ±2% |
| Rise time | 5ms | ±1ms |
| Overshoot | < 5% | - |

**Result**: PASS
- VOUT_5V: 4.98V (within spec)
- Rise time: 5.2ms
- Overshoot: 3.2%

---

## SIM-002: Signal Integrity Analysis

**Objective**: Verify signal integrity for high-speed interfaces

**Interface**: DDR4 Memory

**Measurements**:
| Parameter | Requirement | Result |
|-----------|-------------|--------|
| Setup time | ≥ 0.5ns | 0.8ns |
| Hold time | ≥ 0.5ns | 0.7ns |
| Eye height | ≥ 150mV | 180mV |
| Eye width | ≥ 0.4UI | 0.5UI |

**Result**: PASS
```

#### BP3: Verify Hardware Design

**Design Analysis Report**:
```markdown
## Thermal Analysis Report

### Analysis Conditions:
- Ambient temperature: 85°C
- Airflow: 0.5 m/s
- PCB: 4-layer, 1.6mm

### Results:

| Component | Power (W) | Junction Temp (°C) | Limit (°C) | Margin |
|-----------|-----------|-------------------|------------|--------|
| MCU | 2.5 | 105 | 125 | 20°C |
| PMIC | 1.8 | 95 | 150 | 55°C |
| CAN XCVR | 0.3 | 88 | 150 | 62°C |

### Conclusion:
All components within thermal limits with adequate margin.
```

---

## HWE.4: Hardware Requirements Verification

### Purpose

Verify hardware product conforms to requirements (physical testing).

### Base Practices Implementation

#### BP1: Develop Hardware Requirements Verification Strategy

**Test Strategy Document**:
```yaml
Hardware Requirements Verification Strategy

1. Test Levels:

   Component Testing:
   - Individual component verification
   - Supplier test data review
   - Incoming inspection

   Board-Level Testing:
   - Power-on tests
   - Functional tests
   - Interface tests

   Environmental Testing:
   - Temperature cycling
   - Humidity testing
   - Vibration testing
   - EMC testing

2. Test Sample Size:
   - Prototype: 3 units
   - Pre-production: 10 units
   - Production validation: 30 units

3. Test Sequence:
   1. Visual inspection
   2. Electrical continuity
   3. Power-on test
   4. Functional test
   5. Environmental stress
   6. EMC testing
   7. Reliability testing
```

#### BP2: Develop Verification Specification

**Test Case Template**:
```markdown
## HW-TEST-001: Power Supply Functional Test

**Requirement**: HW-REQ-002 (Power Supply Output)

**Test Setup**:
- Equipment: Programmable power supply, digital multimeter
- Sample: HW-PROTOTYPE-001

**Test Conditions**:
| Parameter | Value |
|-----------|-------|
| Input voltage | 12.0V ± 0.1V |
| Load | No load, 50%, 100% |
| Temperature | 25°C |

**Test Steps**:
1. Connect power supply to DUT
2. Set input voltage to 12.0V
3. Enable power supply
4. Measure VOUT_5V with multimeter
5. Repeat for all load conditions

**Acceptance Criteria**:
| Condition | Measurement | Requirement | Pass/Fail |
|-----------|-------------|-------------|-----------|
| No load | 5.02V | 5.0V ± 2% | PASS |
| 50% load | 4.99V | 5.0V ± 2% | PASS |
| 100% load | 4.95V | 5.0V ± 2% | PASS |
```

#### BP3: Verify Hardware Product

**Environmental Test Summary**:
```markdown
## Environmental Test Report

### Temperature Cycling (per ISO 16750-4)
- Test: -40°C to +85°C, 100 cycles
- Duration: 8 hours/cycle
- Result: PASS - No failures observed

### Humidity Testing (per ISO 16750-4)
- Test: 85°C, 85% RH, 1000 hours
- Result: PASS - No degradation observed

### Vibration Testing (per ISO 16750-3)
- Test: Random vibration, 10-2000 Hz, 8 hours/axis
- Result: PASS - No mechanical failures

### EMC Testing (per CISPR 25 / ISO 11452)
| Test | Standard | Result |
|------|----------|--------|
| Emissions | CISPR 25 Class 5 | PASS |
| Radiated Immunity | ISO 11452-2, 200 V/m | PASS |
| Bulk Current Injection | ISO 11452-4, 200 mA | PASS |
```

---

## Work Products Summary

| Work Product | ID | Description |
|--------------|----|----|
| Hardware Requirements Specification | 18-01 | HW requirements document |
| Hardware Interface Specification | 18-02 | Interface definitions |
| Hardware Architectural Design | 18-03 | Architecture document |
| Hardware Detailed Design | 18-04 | Schematics and PCB design |
| Schematics | 18-05 | Circuit diagrams |
| PCB Design Files | 18-06 | Layout files |
| HW Design Verification Strategy | 18-07 | Design verification plan |
| HW Design Verification Specification | 18-08 | Simulation and analysis specs |
| HW Design Verification Report | 18-09 | Design verification results |
| HW Requirements Verification Strategy | 18-10 | Product test plan |
| HW Requirements Verification Specification | 18-11 | Test case specifications |
| HW Requirements Verification Report | 18-12 | Test results |

---

## References

- Automotive SPICE PAM v4.0 HWE Process Group
- ISO 16750 - Road vehicles environmental conditions
- CISPR 25 - Automotive EMC requirements
- AEC-Q100/Q200 - Automotive component qualification
- [6-aspice40-changes.md](../6-aspice40-changes.md) - Complete change log

---

**Document Version**: 1.0
**Last Updated**: 2026-03-25
**Intended Audience**: Hardware engineers, PCB designers, verification engineers
