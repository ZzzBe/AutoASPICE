# ASPICE Version Selector

## Overview

This document provides guidance on selecting between ASPICE 3.1 and ASPICE 4.0 based on project requirements and use cases.

---

## Quick Selection Guide

### Use ASPICE 3.1 When:

- ✅ Existing OEM requirements specify VDA Scope
- ✅ Traditional ECU software development (no ML/hardware co-design)
- ✅ Established project with ASPICE 3.1 baseline
- ✅ Supplier qualification with legacy requirements
- ✅ No Machine Learning or Hardware Engineering processes needed

### Use ASPICE 4.0 When:

- ✅ Developing ADAS/AD functions with ML components
- ✅ Hardware-software co-development projects
- ✅ New OEM requirements specify ASPICE 4.0
- ✅ Projects requiring MLE or HWE process groups
- ✅ Need for VAL.1 (Validation) process
- ✅ MAN.5 (Risk Management) or MAN.6 (Measurement) required

---

## Version Comparison

| Feature | ASPICE 3.1 | ASPICE 4.0 |
|---------|-----------|------------|
| Release Year | 2017 | 2023 |
| ML Support | ❌ No | ✅ MLE.1-MLE.4 |
| HW Support | ❌ Limited | ✅ HWE.1-HWE.4 |
| Validation | ❌ No dedicated process | ✅ VAL.1 |
| Risk Management | ❌ No dedicated process | ✅ MAN.5 |
| Measurement | ❌ No dedicated process | ✅ MAN.6 |
| Terminology | Testing | Verification |
| Scope | VDA Scope | Dynamic selection |

---

## Content Location

### ASPICE 3.1 Content (Default)

Located in the main `aspice/` directory:

```
knowledge-base/standards/aspice/
├── 1-overview.md      # ASPICE 3.1 overview (with version selector)
├── 2-conceptual.md    # Conceptual architecture
├── 3-detailed.md      # Detailed implementation
├── 4-reference.md     # Quick reference
├── 5-advanced.md      # Advanced topics
└── 6-aspice40-changes.md  # Version comparison
```

### ASPICE 4.0 Content

Located in the `aspice40/` subdirectory:

```
knowledge-base/standards/aspice/aspice40/
├── 1-overview.md       # ASPICE 4.0 overview
├── 2-conceptual.md     # New process groups
├── 3-mle-processes.md  # MLE implementation guide
├── 4-hwe-processes.md  # HWE implementation guide
└── 5-new-processes.md  # VAL, MAN.5, MAN.6, etc.
```

---

## Keyword-Based Version Triggering

### ASPICE 3.1 Trigger Keywords

When user requests include these keywords, use ASPICE 3.1 content:

```
- "ASPICE 3.1"
- "VDA Scope"
- "传统 ECU 开发"
- "VDA 范围"
- "Level 2 capability" (for traditional processes)
- "SWE.4 测试" (using "测试" terminology)
- "SWE.5 集成测试"
- "SWE.6 资质测试"
```

### ASPICE 4.0 Trigger Keywords

When user requests include these keywords, use ASPICE 4.0 content:

```
- "ASPICE 4.0"
- "MLE" / "机器学习"
- "HWE" / "硬件工程"
- "ODD" / "运行设计域"
- "ML 模型训练"
- "ML 模型验证"
- "VAL.1" / "确认"
- "MAN.5" / "风险管理"
- "MAN.6" / "度量"
- "SWE.4 验证" (using "验证" terminology)
- "SWE.5 集成验证"
- "SWE.6 资质验证"
- "ADAS 开发"
- "自动驾驶"
- "软硬件协同"
```

---

## Example Prompts and Responses

### Example 1: ASPICE 3.1 Request

**User Prompt**:
```
请用 ASPICE 3.1 的规则对详细设计进行评审
```

**Response Strategy**:
1. Reference `aspice/3-detailed.md` (ASPICE 3.1 content)
2. Use "Testing" terminology (not "Verification")
3. Follow VDA Scope processes
4. No MLE/HWE processes

### Example 2: ASPICE 4.0 Request

**User Prompt**:
```
请用 ASPICE 4.0 的 MLE 流程对 ML 模型训练过程进行评审
```

**Response Strategy**:
1. Reference `aspice40/3-mle-processes.md`
2. Focus on MLE.3 (Machine Learning Training)
3. Include ODD considerations
4. Use "Verification" terminology

### Example 3: Default (No Version Specified)

**User Prompt**:
```
请对软件需求分析过程进行评审
```

**Response Strategy**:
1. Default to ASPICE 3.1 content
2. Reference `aspice/3-detailed.md` for SWE.1
3. Inform user that ASPICE 3.1 was used by default
4. Offer to switch to ASPICE 4.0 if needed

---

## Process Mapping

### Identical Processes (Both Versions)

| Process | Notes |
|---------|-------|
| SYS.1-SYS.5 | System Engineering processes unchanged |
| SWE.1-SWE.3 | Software Engineering processes unchanged |
| SUP.1, SUP.8-SUP.10 | Supporting processes unchanged |
| MAN.3 | Project Management unchanged |
| ACQ.3, ACQ.4 | Acquisition processes unchanged |
| SPL.2 | Product Release unchanged |

### Terminology Changed Processes

| ASPICE 3.1 | ASPICE 4.0 |
|------------|------------|
| SWE.4 Software Unit Test | SWE.4 Software Unit Verification |
| SWE.5 Software Integration Test | SWE.5 Software Integration and Integration Verification |
| SWE.6 Software Qualification Test | SWE.6 Software Qualification Verification |

### New ASPICE 4.0 Processes

| Process | Purpose |
|---------|---------|
| MLE.1-MLE.4 | Machine Learning Engineering |
| HWE.1-HWE.4 | Hardware Engineering |
| VAL.1 | Validation |
| SUP.11 | ML Data Management |
| MAN.5 | Risk Management |
| MAN.6 | Measurement |
| REU.2 | Reuse Product Management |
| PIM.3 | Process Improvement |

---

## Assessment Scope Selection

### ASPICE 3.1 VDA Scope

Fixed scope (typically 16 processes):
```
SYS.2, SYS.3, SYS.4, SYS.5
SWE.1, SWE.2, SWE.3, SWE.4, SWE.5, SWE.6
SUP.1, SUP.8, SUP.9, SUP.10
MAN.3
```

### ASPICE 4.0 Dynamic Scope

Determine scope based on project characteristics:

```yaml
Step 1: Product Type
  if ML_functionality:
    include: MLE.1, MLE.2, MLE.3, MLE.4, SUP.11

  if Hardware_co_development:
    include: HWE.1, HWE.2, HWE.3, HWE.4

  if Standalone_system:
    include: VAL.1

Step 2: Development Role
  if Supplier:
    include: SPL.2

  if Acquirer:
    include: ACQ.3, ACQ.4

Step 3: Organization Maturity
  if Advanced_maturity:
    include: MAN.5, MAN.6, PIM.3, REU.2
```

---

## File Reference Quick Guide

| Topic | ASPICE 3.1 File | ASPICE 4.0 File |
|-------|-----------------|-----------------|
| Overview | `aspice/1-overview.md` | `aspice40/1-overview.md` |
| Process Architecture | `aspice/2-conceptual.md` | `aspice40/2-conceptual.md` |
| SWE Implementation | `aspice/3-detailed.md` | - |
| MLE Implementation | - | `aspice40/3-mle-processes.md` |
| HWE Implementation | - | `aspice40/4-hwe-processes.md` |
| VAL, MAN.5, MAN.6 | - | `aspice40/5-new-processes.md` |
| Work Products | `aspice/4-reference.md` | `aspice40/2-conceptual.md` |
| Level 3+ Topics | `aspice/5-advanced.md` | - |
| Version Changes | `aspice/6-aspice40-changes.md` | - |

---

## Decision Flowchart

```
                    ┌─────────────────────┐
                    │ User Request        │
                    └─────────┬───────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │ Contains "ASPICE 4.0"?        │
              │ or MLE/HWE/ODD/VAL keywords?  │
              └───────────┬───────────────────┘
                          │
                    Yes   │   No
              ┌───────────┴───────────┐
              ▼                       ▼
    ┌─────────────────┐     ┌─────────────────┐
    │ Use ASPICE 4.0  │     │ Use ASPICE 3.1  │
    │ content from    │     │ content from    │
    │ aspice40/       │     │ main aspice/    │
    └─────────────────┘     └─────────────────┘
              │                       │
              └───────────┬───────────┘
                          │
                          ▼
              ┌─────────────────────────┐
              │ Apply version-specific  │
              │ terminology:            │
              │ 3.1: Testing           │
              │ 4.0: Verification      │
              └─────────────────────────┘
```

---

## References

- [ASPICE 3.1 Overview](1-overview.md)
- [ASPICE 4.0 Overview](aspice40/1-overview.md)
- [ASPICE 4.0 Changes](6-aspice40-changes.md)

---

**Document Version**: 1.0
**Last Updated**: 2026-03-25
**Intended Audience**: All ASPICE users