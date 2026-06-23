# Automotive SPICE 4.0 - SWE Process Group Implementation Guide

## Overview

This document provides detailed implementation guidance for the Software Engineering (SWE) process group in ASPICE 4.0.

> **Key Change from ASPICE 3.1**: All "Testing" terminology has been changed to "Verification" in ASPICE 4.0.

---

## Terminology Changes

| ASPICE 3.1 | ASPICE 4.0 |
|------------|------------|
| SWE.4 Software Unit Test | SWE.4 Software Unit Verification |
| SWE.5 Software Integration Test | SWE.5 Software Integration and Integration Verification |
| SWE.6 Software Qualification Test | SWE.6 Software Qualification Verification |
| Test Strategy | Verification Strategy |
| Test Specification | Verification Specification |
| Test Report | Verification Report |

---

## SWE.1: Software Requirements Analysis

### Purpose

Establish software requirements from system requirements.

### Base Practices (ASPICE 4.0)

#### BP1: Specify Software Requirements

**Objective**: Define complete, consistent, verifiable software requirements.

**Key Changes from 3.1**:
- Increased emphasis on verification criteria
- Stronger traceability requirements to system requirements
- Safety requirements (ASIL) must be explicitly identified

**Implementation**:
```markdown
## Software Requirement: SWE-REQ-[ID]

### Traceability
- Source: SYS-REQ-XXX
- ASIL: [A/B/C/D/QM]

### Requirement Text
The software shall [requirement text with "shall" language].

### Verification Criteria
| Criterion | Value | Verification Method |
|-----------|-------|---------------------|
| Response time | ≤ X ms | Timing analysis |
| Accuracy | ± X% | Integration verification |

### Rationale
[Why this requirement exists]
```

#### BP2: Analyze Software Requirements

**Objective**: Ensure requirements are correct, testable, and complete.

**Analysis Checklist**:
```
Completeness:
☐ All system requirements allocated or justified
☐ All interfaces specified
☐ Error handling specified
☐ Initialization and shutdown specified

Consistency:
☐ No contradictory requirements
☐ Terminology used consistently
☐ Units specified and consistent

Verifiability:
☐ Each requirement has verification method
☐ Quantitative criteria specified
☐ Acceptance criteria measurable
```

#### BP3: Assess Impact on Operating Environment

**Objective**: Evaluate how software requirements affect the system environment.

**Assessment Areas**:
- Hardware resource requirements (memory, CPU)
- Interface impacts (CAN load, bandwidth)
- Integration dependencies
- Safety interactions

#### BP4: Develop Verification Criteria

**Objective**: Define how each requirement will be verified.

**Verification Criteria Template**:
```yaml
Verification Criteria: VC-SWE-XXX
  requirement: SWE-REQ-XXX
  verification_method: [Analysis/Review/Demonstration/Test]
  acceptance_criteria:
    - criterion_1: [measurable value]
    - criterion_2: [measurable value]
  verification_level: [Unit/Integration/Qualification]
```

#### BP5: Ensure Bidirectional Traceability

**Traceability Matrix**:
```markdown
| System Req | Software Req | Architecture | Verification | Status |
|------------|--------------|--------------|--------------|--------|
| SYS-042 | SWE-001, SWE-002 | COMP-SD | VC-SWE-001 | Verified |
```

### Work Products

| ID | Name | Description |
|----|------|-------------|
| 17-11 | Software Requirements Specification | Complete software requirements |
| 13-19 | Verification Criteria | How each requirement will be verified |
| 13-22 | Traceability Record | Bidirectional traceability |

---

## SWE.2: Software Architectural Design

### Purpose

Establish software architecture and allocate requirements to components.

### Base Practices (ASPICE 4.0)

#### BP1: Develop Software Architectural Design

**Architectural Views**:

**Component View**:
```
Software Architecture
├── Application Layer
│   ├── Component A (ASIL D)
│   └── Component B (ASIL B)
├── Service Layer
│   └── Common Services
└── Platform Layer
    └── AUTOSAR BSW
```

**Safety Architecture**:
```yaml
ASIL Decomposition:
  Component A: ASIL D
  Component A_Fallback: ASIL B(D)
  Freedom from Interference:
    - Memory protection: MPU
    - Temporal protection: OS partitioning
```

#### BP2: Allocate Requirements to Components

**Allocation Matrix**:
```markdown
| Component | Allocated Requirements | ASIL | Resources |
|-----------|------------------------|------|-----------|
| COMP-A | SWE-001, SWE-002 | D | RAM: 128KB |
| COMP-B | SWE-003, SWE-004 | B | RAM: 64KB |
```

#### BP3: Define Interfaces

**Interface Specification Template**:
```c
/**
 * Interface: I_ComponentA
 * Provider: COMP-A
 * Consumer: COMP-B
 * ASIL: D
 */
typedef struct {
    float value;        // [Unit] Range: [min, max]
    uint8_t status;     // 0=OK, 1=Degraded, 2=Failed
} InterfaceData_t;

/**
 * Timing: Called every 10ms
 * Safety: Returns last valid on fault
 */
const InterfaceData_t* GetData(void);
```

#### BP4: Describe Dynamic Behavior

**State Machine**:
```
States:
  INIT → STANDBY → ACTIVE → DEGRADED → ERROR

Transitions:
  INIT → STANDBY: [Init complete]
  STANDBY → ACTIVE: [Enable command]
  ACTIVE → DEGRADED: [Sensor fault]
```

#### BP5: Define Evaluation Criteria

**Evaluation Criteria**:
```yaml
Architecture Evaluation:
  completeness:
    - All requirements allocated
    - All interfaces defined
  consistency:
    - No circular dependencies
    - ASIL segregation verified
  feasibility:
    - Resource budget verified
    - Timing analysis complete
```

### Work Products

| ID | Name | Description |
|----|------|-------------|
| 17-01 | Software Architectural Design | Architecture specification |
| 17-02 | Software Interface Specification | Interface definitions |
| 13-22 | Traceability Record | Requirement to component |

---

## SWE.3: Software Detailed Design and Unit Construction

### Purpose

Provide detailed design for units and implement them.

### Base Practices (ASPICE 4.0)

#### BP1: Develop Detailed Design

**Detailed Design Template**:
```c
/**
 * Module: [ModuleName]
 * Component: [ComponentName]
 * Requirement: SWE-REQ-XXX
 * ASIL: [A/B/C/D]
 *
 * Description:
 * [What this module does]
 *
 * Algorithm:
 * 1. [Step 1]
 * 2. [Step 2]
 *
 * Timing: X ms
 * Stack: X bytes
 * RAM: X bytes
 */

/* Constants */
#define CONSTANT_1 (value)

/* Types */
typedef struct {
    /* fields */
} ModuleData_t;

/* Functions */
ReturnValue_t Module_Function(Input_t input);
```

#### BP2: Define Unit Interfaces

**Interface Definition**:
```c
/**
 * Function: Module_Function
 * Description: [What it does]
 *
 * @param input: [Description] Range: [min, max]
 * @return: [Description] Possible values: [...]
 *
 * @pre [Preconditions]
 * @post [Postconditions]
 *
 * @sideeffects [Any side effects]
 */
ReturnValue_t Module_Function(Input_t input);
```

#### BP3: Describe Dynamic Behavior

**Sequence Diagram**:
```
Caller         Module         Hardware
   |             |               |
   | Function()  |               |
   |------------>|               |
   |             | ReadHW()      |
   |             |-------------->|
   |             |    Data       |
   |             |<--------------|
   |             | Process()     |
   |             |               |
   |   Result    |               |
   |<------------|               |
```

#### BP4: Evaluate Detailed Design

**Design Review Checklist**:
```markdown
☐ Requirements coverage complete
☐ Interface definitions correct
☐ Algorithm logic correct
☐ Error handling defined
☐ Resource usage within budget
☐ Coding standards applicable
☐ Safety annotations present
☐ Complexity within limits
```

#### BP5: Establish Traceability

**Traceability to Architecture**:
```markdown
| Architecture Component | Detailed Design Module | Implementation File |
|-----------------------|------------------------|---------------------|
| COMP-A | ModuleA_1, ModuleA_2 | module_a_1.c, module_a_2.c |
```

#### BP6: Construct Software Units

**Implementation Guidelines**:
```markdown
- Follow MISRA C:2012 guidelines
- Use meaningful naming conventions
- Add safety annotations for ASIL code
- Implement defensive programming
- Document all design decisions
```

#### BP7: Ensure Consistency with Design

**Consistency Verification**:
```markdown
☐ Function signatures match header
☐ Algorithm matches design description
☐ Constants match specification
☐ Resource usage within budget
☐ MISRA C compliance verified
☐ Safety annotations present
```

### Work Products

| ID | Name | Description |
|----|------|-------------|
| 17-03 | Software Detailed Design | Detailed design specification |
| 17-04 | Software Unit | Source code files |
| 13-22 | Traceability Record | Design to code |

---

## SWE.4: Software Unit Verification

### Purpose

Verify software units meet design requirements.

> **Note**: ASPICE 4.0 uses "Verification" instead of "Test".

### Base Practices (ASPICE 4.0)

#### BP1: Develop Unit Verification Strategy

**Verification Strategy Document**:
```yaml
Unit Verification Strategy:

1. Verification Methods:
   - Static analysis (MISRA C, complexity)
   - Code reviews
   - Unit verification (functional)
   - Coverage analysis

2. Coverage Requirements:
   ASIL A: Statement coverage ≥ 100%
   ASIL B: Branch coverage ≥ 100%
   ASIL C: Branch coverage ≥ 100%
   ASIL D: MC/DC coverage = 100%

3. Tools:
   - Static analyzer: PC-lint, Coverity
   - Unit verification framework: Google Test, Unity
   - Coverage: gcov, Bullseye, VectorCAST

4. Environment:
   - Host: x86_64 Linux
   - Cross-compiler: arm-none-eabi-gcc
```

#### BP2: Develop Unit Verification Specification

**Verification Case Template**:
```markdown
## VC-UNIT-XXX: [Verification Case Name]

### Requirement Coverage
- SWE-REQ-XXX

### Verification Level
- Unit Level

### Preconditions
- Module initialized
- Input data valid

### Input Data
| Parameter | Value | Valid Range |
|-----------|-------|-------------|
| param1 | X | [min, max] |

### Expected Output
| Output | Expected Value |
|--------|----------------|
| return | Y |
| status | OK |

### Verification Steps
1. Initialize module
2. Set input parameters
3. Call function under verification
4. Verify output matches expected
5. Verify no side effects

### Pass Criteria
- All outputs match expected
- Coverage target achieved
```

#### BP3: Verify Software Units

**Implementation Example (Google Test)**:
```cpp
TEST(ModuleTest, Function_NominalCase) {
    // Arrange
    Input_t input = { .param1 = 10.0f };
    ReturnValue_t expected = SUCCESS;

    // Act
    ReturnValue_t actual = Module_Function(&input);

    // Assert
    EXPECT_EQ(expected, actual);
    EXPECT_FLOAT_EQ(input.param1 * 2.0f, input.result);
}

TEST(ModuleTest, Function_BoundaryCase) {
    // Test at boundary values
    Input_t input = { .param1 = MAX_VALUE };
    ReturnValue_t actual = Module_Function(&input);
    EXPECT_EQ(SUCCESS, actual);
}

TEST(ModuleTest, Function_ErrorCase) {
    // Test error handling
    Input_t input = { .param1 = INVALID_VALUE };
    ReturnValue_t actual = Module_Function(&input);
    EXPECT_EQ(ERROR_INVALID_PARAM, actual);
}
```

#### BP4: Establish Bidirectional Traceability

**Traceability Matrix**:
```markdown
| Requirement | Verification Case | Result | Coverage |
|-------------|-------------------|--------|----------|
| SWE-001 | VC-UNIT-001, VC-UNIT-002 | PASS | 100% |
| SWE-002 | VC-UNIT-003 | PASS | 100% |
```

#### BP5: Ensure Consistency

**Consistency Checks**:
```markdown
☐ Verification cases cover all requirements
☐ Verification environment matches target
☐ Coverage requirements met
☐ All verification cases executed
☐ Results documented
```

#### BP6: Summarize and Communicate Results

**Verification Summary Report**:
```markdown
## Unit Verification Summary

### Overall Results
| Metric | Value |
|--------|-------|
| Total Cases | X |
| Passed | Y |
| Failed | Z |
| Coverage (MC/DC) | 100% |

### Per-Module Results
| Module | Cases | Pass | Fail | Coverage |
|--------|-------|------|------|----------|
| ModuleA | 50 | 50 | 0 | 100% |
| ModuleB | 30 | 29 | 1 | 98% |

### Open Issues
- [List of open issues]
```

### Work Products

| ID | Name | Description |
|----|------|-------------|
| 17-12 | Software Unit Verification Strategy | Verification approach |
| 17-13 | Software Unit Verification Specification | Verification cases |
| 17-14 | Software Unit Verification Report | Verification results |

---

## SWE.5: Software Integration and Integration Verification

### Purpose

Integrate units and verify interfaces.

### Base Practices (ASPICE 4.0)

#### BP1: Develop Integration Strategy

**Integration Strategy**:
```yaml
Software Integration Strategy:

1. Integration Order:
   Phase 1: Module integration within components
   Phase 2: Component integration
   Phase 3: Full software integration

2. Integration Steps:
   Step 1: Integrate Module A + Module B
   Step 2: Verify interface I_AB
   Step 3: Integrate Component A
   Step 4: Verify component interfaces

3. Verification Approach:
   - Interface verification
   - Timing verification
   - Resource verification
```

#### BP2: Develop Integration Verification Specification

**Integration Verification Case**:
```markdown
## VC-INT-XXX: [Integration Verification Case]

### Integration Step
- Step X: [Description]

### Interfaces Verified
- I_Interface1: Module A → Module B

### Verification Environment
- Host PC with target simulator
- AUTOSAR BSW stubs

### Verification Data
| Input | Expected Output |
|-------|-----------------|
| Data at I_Interface1 | Processed data at I_Interface2 |

### Pass Criteria
- Data correctly transmitted
- Timing requirements met
- No data corruption
```

#### BP3: Integrate Software Units

**Integration Procedure**:
```markdown
## Integration Procedure: INT-PROC-XXX

### Prerequisites
- All unit verification passed
- Integration environment ready

### Steps
1. Build integration configuration
2. Deploy to target/simulator
3. Initialize all modules
4. Execute integration verification
5. Document results
```

#### BP4: Verify Integrated Units

**Verification Results**:
```markdown
| Interface | Verification Case | Result | Notes |
|-----------|-------------------|--------|-------|
| I_AB | VC-INT-001 | PASS | - |
| I_BC | VC-INT-002 | PASS | - |
| I_CAN | VC-INT-003 | PASS | CAN message timing verified |
```

#### BP5: Establish Bidirectional Traceability

```markdown
| Interface | Requirement | Verification Case | Status |
|-----------|-------------|-------------------|--------|
| I_AB | SWE-001 | VC-INT-001 | Verified |
```

#### BP6: Ensure Consistency

```markdown
☐ Integration order followed
☐ All interfaces verified
☐ Timing requirements verified
☐ Resource usage verified
```

#### BP7: Summarize and Communicate Results

### Work Products

| ID | Name | Description |
|----|------|-------------|
| 17-06 | Software Integration Strategy | Integration approach |
| 17-07 | Software Integration Verification Specification | Integration verification cases |
| 17-08 | Software Integration Verification Report | Integration verification results |

---

## SWE.6: Software Qualification Verification

### Purpose

Verify software meets requirements.

### Base Practices (ASPICE 4.0)

#### BP1: Develop Qualification Verification Strategy

**Qualification Verification Strategy**:
```yaml
Software Qualification Verification Strategy:

1. Verification Scope:
   - All software requirements
   - All ASIL requirements
   - All interface requirements

2. Verification Environment:
   - Target ECU
   - HIL system (for real-time verification)
   - Production configuration

3. Coverage Requirements:
   - 100% requirement coverage
   - All verification methods applied
```

#### BP2: Develop Qualification Verification Specification

**Qualification Verification Case**:
```markdown
## VC-QUAL-XXX: [Qualification Verification Case]

### Requirement
- SWE-REQ-XXX: [Requirement text]

### ASIL
- [A/B/C/D]

### Verification Method
- [Analysis/Demonstration/Test/Review]

### Verification Environment
- Target ECU: [Part Number]
- Software Version: X.Y.Z

### Input Conditions
| Condition | Value |
|-----------|-------|
| Input signal | X |

### Expected Results
| Output | Expected Value | Tolerance |
|--------|----------------|-----------|
| Output signal | Y | ±Z |

### Pass Criteria
- Output within tolerance
- Timing requirements met
- No unintended behavior
```

#### BP3: Verify Integrated Software

**Verification Execution Record**:
```markdown
## VC-QUAL-XXX Execution Record

**Date**: YYYY-MM-DD
**Software Version**: X.Y.Z
**ECU**: [Serial Number]
**Result**: PASS/FAIL

### Actual Results
| Measurement | Expected | Actual | Status |
|-------------|----------|--------|--------|
| Response time | ≤ 10ms | 8.2ms | PASS |
| Output value | 100 ± 5 | 102 | PASS |

### Deviations
- [List any deviations]
```

#### BP4: Establish Bidirectional Traceability

```markdown
| Requirement | Verification Case | Result | Evidence |
|-------------|-------------------|--------|----------|
| SWE-001 | VC-QUAL-001 | PASS | Report_XYZ |
| SWE-002 | VC-QUAL-002 | PASS | Report_ABC |
```

#### BP5: Ensure Consistency

```markdown
☐ All requirements covered
☐ Verification environment correct
☐ All verification cases executed
☐ Results documented
☐ Traceability complete
```

#### BP6: Summarize and Communicate Results

**Qualification Verification Summary**:
```markdown
## Software Qualification Verification Summary

### Statistics
| Metric | Value |
|--------|-------|
| Total Requirements | X |
| Requirements Verified | X |
| Pass Rate | 100% |
| Open Nonconformances | 0 |

### ASIL Summary
| ASIL | Requirements | Verified | Status |
|------|--------------|----------|--------|
| D | 50 | 50 | ✓ |
| B | 30 | 30 | ✓ |
| QM | 20 | 20 | ✓ |

### Recommendation
- [Ready/Not ready for release]
```

### Work Products

| ID | Name | Description |
|----|------|-------------|
| 17-09 | Software Qualification Verification Strategy | Qualification approach |
| 17-10 | Software Qualification Verification Specification | Qualification verification cases |
| 17-15 | Software Qualification Verification Report | Qualification results |

---

## References

- Automotive SPICE PAM v4.0 SWE Process Group
- ISO 26262-6: Software safety requirements
- MISRA C:2012 Guidelines
- [../6-aspice40-changes.md](../6-aspice40-changes.md) - Complete change log

---

**Document Version**: 1.0
**Last Updated**: 2026-03-25
**Intended Audience**: Software engineers, verification engineers, technical leads
