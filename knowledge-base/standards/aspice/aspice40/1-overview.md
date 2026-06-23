# Automotive SPICE 4.0 - Overview

## What is Automotive SPICE 4.0?

Automotive SPICE 4.0 (2023) is the latest version of the Automotive SPICE framework for assessing and improving software development processes in the automotive industry. It introduces significant enhancements for ML-based functions and hardware-software co-development.

## Key Changes from ASPICE 3.1

| Aspect | ASPICE 3.1 | ASPICE 4.0 |
|--------|-----------|------------|
| Release Year | 2017 | 2023 |
| ML Support | No | Yes (MLE process group) |
| HW Support | Limited | Yes (HWE process group) |
| Terminology | Testing | Verification |
| Scope Definition | VDA Scope | Dynamic scope selection |

> **For ASPICE 3.1 content**: See parent directory files (1-overview.md through 5-advanced.md)
> **For detailed changes**: See [6-aspice40-changes.md](../6-aspice40-changes.md)

## New Process Groups in ASPICE 4.0

### MLE - Machine Learning Engineering

Critical for projects developing AI/ML-based automotive functions:

| Process | Purpose |
|---------|---------|
| MLE.1 | Machine Learning Requirements Analysis - Define ML requirements and ODD |
| MLE.2 | Machine Learning Architecture - Define model architecture and hyperparameters |
| MLE.3 | Machine Learning Training - Train and optimize ML model |
| MLE.4 | Machine Learning Model Verification - Verify model against requirements |

### HWE - Hardware Engineering

Critical for projects with hardware-software co-development:

| Process | Purpose |
|---------|---------|
| HWE.1 | Hardware Requirements Analysis - Derive hardware requirements |
| HWE.2 | Hardware Design - Define hardware architecture and detailed design |
| HWE.3 | Hardware Design Verification - Verify design against requirements |
| HWE.4 | Hardware Requirements Verification - Verify product against requirements |

## New Standalone Processes

| Process | Purpose |
|---------|---------|
| VAL.1 | Validation - Ensure system/software satisfies user needs |
| SUP.11 | ML Data Management - Manage ML data lifecycle |
| MAN.5 | Risk Management - Identify and control project risks |
| MAN.6 | Measurement - Establish measurement system |
| REU.2 | Reuse Product Management - Manage reusable products |
| PIM.3 | Process Improvement - Continuously improve processes |

## Terminology Changes

| ASPICE 3.1 | ASPICE 4.0 |
|------------|------------|
| Testing | **Verification** |
| - | Measure (activity to achieve intent) |
| - | Metric (quantifiable indicator) |
| - | ODD (Operational Design Domain) |
| - | Hyperparameter |

## Assessment Scope Selection

ASPICE 4.0 uses dynamic scope selection instead of fixed VDA Scope:

```
Step 1: Product Type Identification
├─ Pure software → SYS + SWE processes
├─ Software-hardware → + HWE processes
├─ Contains ML functions → + MLE processes
└─ Standalone system → + VAL process

Step 2: Development Role
├─ Supplier → SPL processes
├─ Acquirer → ACQ processes
└─ Both → SPL + ACQ

Step 3: Organization Maturity
├─ Initial → Core processes
├─ Advanced → + PIM, REU
└─ High maturity → + MAN.5, MAN.6
```

## Typical Assessment Scopes

### Traditional ECU Software Development
```
- SYS.2, SYS.3, SYS.4, SYS.5
- SWE.1, SWE.2, SWE.3, SWE.4, SWE.5, SWE.6
- SUP.1, SUP.8, SUP.9, SUP.10
- MAN.3, MAN.5
- SPL.2
```

### ADAS Development with ML Functions
```
- SYS.2, SYS.3, SYS.4, SYS.5
- SWE.1, SWE.2, SWE.3, SWE.4, SWE.5, SWE.6
- MLE.1, MLE.2, MLE.3, MLE.4
- SUP.1, SUP.8, SUP.9, SUP.10, SUP.11
- MAN.3, MAN.5, MAN.6
- VAL.1
```

### Software-Hardware Co-Development
```
- SYS.2, SYS.3, SYS.4, SYS.5
- SWE.1, SWE.2, SWE.3, SWE.4, SWE.5, SWE.6
- HWE.1, HWE.2, HWE.3, HWE.4
- SUP.1, SUP.8, SUP.9, SUP.10
- MAN.3, MAN.5
```

## Related Documents

- [2-conceptual.md](2-conceptual.md) - ASPICE 4.0 conceptual architecture
- [3-mle-processes.md](3-mle-processes.md) - MLE process group detailed guide
- [4-hwe-processes.md](4-hwe-processes.md) - HWE process group detailed guide
- [5-new-processes.md](5-new-processes.md) - VAL, MAN.5, MAN.6, etc.
- [../6-aspice40-changes.md](../6-aspice40-changes.md) - Complete change log

---

**Document Version**: 1.0
**Last Updated**: 2026-03-25
**Intended Audience**: All ASPICE stakeholders
