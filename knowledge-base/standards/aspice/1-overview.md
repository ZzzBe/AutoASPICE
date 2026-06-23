# Automotive SPICE - Overview

## What is Automotive SPICE?

Automotive SPICE (Software Process Improvement and Capability Determination) is a framework for assessing and improving software development processes in the automotive industry. Based on ISO/IEC 33000 series, it defines process capability levels and best practices.

## Version Selection

This knowledge base supports both ASPICE versions:

| Version | Release Year | Use Case |
|---------|-------------|----------|
| **ASPICE 3.1** | 2017 | Traditional VDA Scope assessments, existing OEM requirements |
| **ASPICE 4.0** | 2023 | ML/HW projects, new OEM requirements with MLE/HWE processes |

**How to select version:**
- Use ASPICE 3.1 content by default (this document and files 2-5)
- Use ASPICE 4.0 content by referencing `aspice40/` directory
- See [VERSION_SELECTOR.md](VERSION_SELECTOR.md) for detailed guidance
- See [6-aspice40-changes.md](6-aspice40-changes.md) for version differences

> **This document (1-overview.md through 5-advanced.md) covers ASPICE 3.1 with VDA Scope.** For ASPICE 4.0 content, see the [aspice40/](aspice40/) directory.

## Key Characteristics

- **Process Reference Model (PRM)**: Defines what processes should exist
- **Process Assessment Model (PAM)**: Defines how to measure process capability
- **Capability levels**: 0 (Incomplete) through 5 (Optimizing)
- **Industry standard**: Required by most OEMs for supplier qualification

## Relationship to Other Standards

```
┌─────────────────────────────────────────┐
│   ISO/IEC 33000 Series                  │
│   - Process assessment framework        │
└─────────────────────────────────────────┘
           ↕ Based on
┌─────────────────────────────────────────┐
│   Automotive SPICE (VDA Scope)          │
│   - Automotive-specific interpretation  │
│   - VDA assessment guidelines           │
└─────────────────────────────────────────┘
           ↕ Interfaces
┌─────────────────────────────────────────┐
│   ISO 26262 (Functional Safety)         │
│   - Safety process requirements         │
│   - Work product evidence               │
└─────────────────────────────────────────┘
```

## Scope

Automotive SPICE applies to:
- Embedded automotive software development
- Software suppliers to OEMs
- OEM internal software development
- System engineering with software components
- Software maintenance and support

## Capability Levels

### Level 0: Incomplete
Process not implemented or fails to achieve its purpose.

**Characteristics**:
- No systematic approach
- Work products missing or inadequate
- Objectives not met

### Level 1: Performed
Process achieves its purpose and produces work products.

**Characteristics**:
- Base practices implemented
- Work products created
- Process objectives generally achieved
- Ad-hoc, reactive approach

### Level 2: Managed
Process is planned, monitored, and adjusted. Work products are controlled.

**Additional Requirements**:
- Performance management (GP 2.1)
- Work product management (GP 2.2)
- Resource and responsibility management (GP 2.3, GP 2.4)

### Level 3: Established
Process uses defined standard process adapted from organizational standards.

**Additional Requirements**:
- Process definition (GP 3.1)
- Process deployment (GP 3.2)
- Organizational process assets used

### Level 4: Predictable
Process operates within defined limits to achieve outcomes.

**Additional Requirements**:
- Process measurement (GP 4.1)
- Process control (GP 4.2)
- Statistical process control

### Level 5: Optimizing
Process continuously improved to meet business goals.

**Additional Requirements**:
- Process innovation (GP 5.1)
- Process optimization (GP 5.2)
- Data-driven improvement

## ASPICE 4.0 Assessment Scope

ASPICE 4.0 introduces a flexible assessment scope approach, replacing the traditional "VDA Scope" concept. The assessment scope is now determined based on project characteristics and product type.

### Scope Determination Approach

**Step 1: Product Type Identification**

- Pure software product → SYS + SWE process groups
- Software-hardware product → + HWE process group
- Contains ML functions → + MLE process group
- Standalone system → + VAL process

**Step 2: Development Role Identification**

- Supplier role → SPL process group
- Acquirer role → ACQ process group
- Both roles → SPL + ACQ

**Step 3: Organization Maturity Consideration**

- Initial assessment → Core processes (SYS, SWE, SUP, MAN)
- Advanced assessment → + PIM, REU
- High maturity assessment → + MAN.5, MAN.6

### Typical Assessment Scopes

**Scenario 1: Traditional ECU Software Development (Tier 1 Supplier)**

Core processes:

- SYS.2, SYS.3, SYS.4, SYS.5
- SWE.1, SWE.2, SWE.3, SWE.4, SWE.5, SWE.6
- SUP.1, SUP.8, SUP.9, SUP.10
- MAN.3, MAN.5
- SPL.2

**Scenario 2: ADAS Development with ML Functions**

Core processes + MLE:

- SYS.2, SYS.3, SYS.4, SYS.5
- SWE.1, SWE.2, SWE.3, SWE.4, SWE.5, SWE.6
- MLE.1, MLE.2, MLE.3, MLE.4
- SUP.1, SUP.8, SUP.9, SUP.10, SUP.11
- MAN.3, MAN.5, MAN.6
- VAL.1

**Scenario 3: Software-Hardware Co-Development**

Core processes + HWE:

- SYS.2, SYS.3, SYS.4, SYS.5
- SWE.1, SWE.2, SWE.3, SWE.4, SWE.5, SWE.6
- HWE.1, HWE.2, HWE.3, HWE.4
- SUP.1, SUP.8, SUP.9, SUP.10
- MAN.3, MAN.5

### Legacy VDA Scope Reference

The traditional VDA Scope (ASPICE 3.1) is provided for reference:

**Primary Processes** (always assessed):

- SYS.2: System Requirements Analysis
- SYS.3: System Architectural Design
- SYS.4: System Integration and Integration Verification
- SYS.5: System Qualification Verification
- SWE.1: Software Requirements Analysis
- SWE.2: Software Architectural Design
- SWE.3: Software Detailed Design and Unit Construction
- SWE.4: Software Unit Verification
- SWE.5: Software Integration and Integration Verification
- SWE.6: Software Qualification Verification

**Supporting Processes** (typically assessed):

- SUP.1: Quality Assurance
- SUP.8: Configuration Management
- SUP.9: Problem Resolution Management
- SUP.10: Change Request Management
- MAN.3: Project Management

**Target Capability**:

- Most OEMs require Level 2 (Managed) for supplier qualification
- Some require Level 3 (Established) for strategic suppliers

## ASPICE 4.0 Process Categories

### Primary Processes (Development)

**System Engineering (SYS)**:

- Define system requirements
- Design system architecture
- Integrate and verify system

**Software Engineering (SWE)**:

- Define software requirements
- Design software architecture and detailed design
- Implement and verify software units
- Integrate and verify software

**Machine Learning Engineering (MLE)** *(New in ASPICE 4.0)*:

- Define ML requirements and ODD
- Design ML architecture
- Train ML models
- Verify ML models

**Hardware Engineering (HWE)** *(New in ASPICE 4.0)*:

- Define hardware requirements
- Design hardware architecture
- Verify hardware design

### Supporting Processes (SUP)

**Quality Assurance (SUP.1)**:

- Ensure processes and work products meet requirements
- Independent verification

**Configuration Management (SUP.8)**:

- Identify and control configuration items
- Establish baselines
- Control changes

**Problem Resolution (SUP.9)**:

- Record and track problems
- Analyze and resolve problems

**Change Request Management (SUP.10)**:

- Record and track change requests
- Analyze impact
- Implement and verify changes

**ML Data Management (SUP.11)** *(New in ASPICE 4.0)*:

- Manage ML data collection, labeling, and versioning
- Ensure data quality for ML training

### Management Processes (MAN)

**Project Management (MAN.3)**:

- Define project scope and objectives
- Establish estimates
- Define project activities and resources
- Monitor and control project

**Risk Management (MAN.5)** *(New in ASPICE 4.0)*:

- Identify and analyze project risks
- Define and implement risk mitigation measures
- Monitor and control risks

**Measurement (MAN.6)** *(New in ASPICE 4.0)*:

- Establish measurement objectives
- Define and collect metrics
- Analyze and report measurement results

### Validation Process (VAL)

**Validation (VAL.1)** *(New in ASPICE 4.0)*:

- Ensure system/software satisfies user needs and intended use
- Conduct user acceptance validation

### Process Improvement (PIM)

**Process Improvement (PIM.3)** *(New in ASPICE 4.0)*:

- Identify process improvement opportunities
- Implement process changes
- Monitor improvement effectiveness

### Reuse Process (REU)

**Reuse Product Management (REU.2)** *(New in ASPICE 4.0)*:

- Identify and evaluate reusable products
- Manage reuse product lifecycle

## Assessment Process

### Phases of Assessment

**Phase 1: Planning**
- Define scope (processes, organizational units)
- Select assessment team
- Schedule assessment

**Phase 2: Data Collection**
- Review documentation
- Conduct interviews
- Observe work practices

**Phase 3: Rating**
- Evaluate base practices (Performed level)
- Evaluate generic practices (Managed+ levels)
- Assign ratings (N/P/L/F)

**Phase 4: Reporting**
- Present findings
- Identify strengths and weaknesses
- Recommend improvements

### Rating Scale

| Rating | Meaning | Percentage Achieved |
|--------|---------|---------------------|
| N | Not achieved | 0-15% |
| P | Partially achieved | >15-50% |
| L | Largely achieved | >50-85% |
| F | Fully achieved | >85-100% |

**Level Achievement**:
- Level 1: All base practices rated L or F
- Level 2: Level 1 + all GP 2.x rated L or F
- Level 3: Level 2 + all GP 3.x rated L or F

## Common Assessment Findings

### Typical Weaknesses at Level 1

- Incomplete requirements specifications
- Missing traceability between levels
- Inadequate test coverage
- Missing verification records

### Typical Weaknesses Preventing Level 2

- No project planning or monitoring
- Work products not under configuration management
- No systematic quality assurance
- Missing evidence of reviews

### Typical Weaknesses Preventing Level 3

- No organizational standard process defined
- Project processes not tailored from standard
- No process assets repository
- Inconsistency across projects

## Comparison: ASPICE vs CMMI

| Aspect | Automotive SPICE | CMMI |
|--------|------------------|------|
| Origin | ISO/IEC 33000 | Software Engineering Institute |
| Industry | Automotive | General software |
| Scope | Process-specific | Organization-wide |
| Levels | 0-5 (per process) | 1-5 (maturity levels) |
| Assessment | Process capability | Organizational maturity |
| Granularity | Fine (individual processes) | Coarse (process areas) |

## Benefits of ASPICE Compliance

**For Suppliers**:
- Qualification with OEMs
- Improved process quality
- Reduced defect rates
- Better project predictability

**For OEMs**:
- Supplier quality assurance
- Reduced integration costs
- Lower warranty costs
- Risk mitigation

**Measurable Improvements**:
- 30-50% reduction in defect density
- 20-40% improvement in schedule predictability
- 15-30% reduction in rework

## Getting Started with ASPICE

### For Organizations New to ASPICE

1. **Awareness**: Train management and teams on ASPICE concepts
2. **Gap Analysis**: Perform informal self-assessment
3. **Improvement Plan**: Prioritize processes for improvement
4. **Implementation**: Deploy improved processes on pilot projects
5. **Assessment**: Conduct formal capability assessment
6. **Continuous Improvement**: Iterate based on findings

### Quick Wins for Level 2

- Implement traceability tool (requirements to tests)
- Establish configuration management (Git + policies)
- Define review process (checklists, sign-offs)
- Implement project monitoring (Gantt charts, burn-down)

## Use Cases

ASPICE is essential for:
- Tier 1 suppliers developing ECU software
- Software development for safety-critical systems
- OEM internal software development teams
- Offshore development with quality concerns

## Next Steps

- **Level 2**: Conceptual understanding of process groups and generic practices
- **Level 3**: Detailed base practice implementation guides
- **Level 4**: Work product templates and assessment checklists
- **Level 5**: Achieving Level 3+ and continuous improvement

## References

- Automotive SPICE PAM v4.0 (Process Assessment Model)
- Automotive SPICE PRM v4.0 (Process Reference Model)
- ISO/IEC 33001:2015 Concepts and terminology
- ISO/IEC 33002:2015 Requirements for process assessment
- [ASPICE 4.0 Changes](6-aspice40-changes.md) - Detailed change log from 3.1 to 4.0

---

**Document Version**: 2.0
**Last Updated**: 2026-03-24
**Intended Audience**: Project managers, quality managers, software development teams
