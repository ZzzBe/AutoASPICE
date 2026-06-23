# Automotive SPICE 4.0 - SUP/MAN Process Groups Implementation Guide

## Overview

This document provides detailed implementation guidance for the Supporting (SUP) and Management (MAN) process groups in ASPICE 4.0.

> **Key Change from ASPICE 3.1**: Added SUP.11 (ML Data Management), MAN.5 (Risk Management), MAN.6 (Measurement), and PIM.3 (Process Improvement).

---

## SUP Process Group

### SUP.1: Quality Assurance

#### Purpose

Independently assure that work products and processes comply with predefined standards and procedures.

#### Base Practices (ASPICE 4.0)

##### BP1: Develop Quality Assurance Strategy

```yaml
Quality Assurance Strategy:

1. Scope:
   - Processes to be audited
   - Work products to be reviewed
   - Audit frequency

2. Standards:
   - ASPICE process requirements
   - ISO 26262 requirements (for safety items)
   - Company coding standards

3. Methods:
   - Process audits
   - Product audits
   - Peer reviews
```

##### BP2: Perform Process Quality Assurance

```markdown
## Process Audit Checklist

### Process: [Process ID]

| Practice | Evidence | Status | Findings |
|----------|----------|--------|----------|
| BP1 | [Document reference] | ✓/✗ | [Notes] |
| BP2 | [Document reference] | ✓/✗ | [Notes] |
```

##### BP3: Perform Product Quality Assurance

```markdown
## Work Product Review Record

**Work Product**: [WP ID]
**Version**: X.Y
**Review Date**: YYYY-MM-DD
**Reviewer**: [Name]

### Checklist Results
| Criterion | Status | Comments |
|-----------|--------|----------|
| Completeness | ✓/✗ | |
| Consistency | ✓/✗ | |
| Traceability | ✓/✗ | |

### Nonconformities
- [List of nonconformities]
```

#### Work Products

| ID | Name | Description |
|----|------|-------------|
| 07-01 | Quality assurance strategy | QA approach |
| 07-02 | Quality record | Audit and review records |

---

### SUP.8: Configuration Management

#### Purpose

Establish and maintain the integrity of work products.

#### Base Practices (ASPICE 4.0)

##### BP1: Develop Configuration Management Strategy

```yaml
Configuration Management Strategy:

1. Configuration Items:
   - Requirements documents
   - Design documents
   - Source code
   - Test cases
   - Calibration data

2. Version Control:
   - Repository: Git
   - Branching strategy: GitFlow
   - Merge requirements: Code review approval

3. Baselines:
   - Functional baseline
   - Development baseline
   - Product baseline

4. Change Control:
   - Change request process
   - Impact analysis requirements
   - Approval authorities
```

##### BP2: Identify Configuration Items

```markdown
## Configuration Item: CI-[ID]

**Name**: [Item name]
**Type**: [Document/Code/Data/...]
**Location**: [Repository path]
**Version**: X.Y.Z
**Owner**: [Name]
**Baseline**: [Baseline name]
```

##### BP3: Control Configuration Items

```markdown
## Change Request: CR-[ID]

**Configuration Item**: CI-XXX
**Requested By**: [Name]
**Date**: YYYY-MM-DD

### Description
[Change description]

### Impact Analysis
| Affected Item | Impact |
|---------------|--------|
| CI-XXX | [Impact description] |

### Approval
- Technical Lead: [Approved/Rejected]
- Configuration Manager: [Approved/Rejected]

### Implementation Status
- [ ] Changes implemented
- [ ] Review completed
- [ ] Baseline updated
```

##### BP4: Establish Configuration Management Records

```markdown
## Configuration Status Record

**Baseline**: [Baseline name]
**Date**: YYYY-MM-DD

| CI ID | Item Name | Version | Status |
|-------|-----------|---------|--------|
| CI-001 | Requirements | 2.1 | Baseline |
| CI-002 | Architecture | 1.5 | Baseline |
```

#### Work Products

| ID | Name | Description |
|----|------|-------------|
| 08-01 | Configuration management strategy | CM approach |
| 08-02 | Configuration item record | CI identification |
| 08-03 | Version control record | Version history |
| 08-04 | Baseline record | Baseline contents |

---

### SUP.9: Problem Resolution Management

#### Purpose

Ensure that problems are identified, analyzed, and resolved.

#### Base Practices (ASPICE 4.0)

##### BP1: Develop Problem Resolution Strategy

```yaml
Problem Resolution Strategy:

1. Problem Categories:
   - Defects: Non-conformance to requirements
   - Change requests: Enhancement requests
   - Questions: Clarification requests

2. Priority Levels:
   - Critical: Safety issue, immediate action required
   - Major: Significant impact, resolve in current iteration
   - Minor: Low impact, schedule for future release

3. Resolution Process:
   - Problem identification and logging
   - Impact analysis
   - Resolution planning
   - Implementation and verification
   - Closure
```

##### BP2: Identify and Record Problems

```markdown
## Problem Report: PR-[ID]

**Date Identified**: YYYY-MM-DD
**Identified By**: [Name]
**Source**: [Development/Testing/Field]

### Problem Description
[Detailed description of the problem]

### Classification
- Category: [Defect/Change Request/Question]
- Priority: [Critical/Major/Minor]
- Severity: [Critical/Major/Minor]

### Affected Items
- Work Products: [List]
- Requirements: [List]

### Reproduction Steps
1. [Step 1]
2. [Step 2]
```

##### BP3: Analyze Problems

```markdown
## Problem Analysis: PR-[ID]

### Root Cause Analysis
- Method: [5 Whys / Fishbone / Fault Tree]
- Root Cause: [Identified root cause]

### Impact Assessment
| Impact Area | Effect |
|-------------|--------|
| Safety | [Impact on safety] |
| Schedule | [Schedule impact] |
| Cost | [Cost impact] |

### Proposed Solution
[Description of proposed resolution]
```

##### BP4: Track and Resolve Problems

```markdown
## Problem Resolution: PR-[ID]

### Resolution
**Action Taken**: [Description]
**Implemented By**: [Name]
**Implementation Date**: YYYY-MM-DD

### Verification
**Verification Method**: [Review/Test/Analysis]
**Verification Result**: PASS/FAIL
**Verified By**: [Name]

### Closure
**Status**: Closed
**Closure Date**: YYYY-MM-DD
**Closure Approved By**: [Name]
```

#### Work Products

| ID | Name | Description |
|----|------|-------------|
| 09-01 | Problem resolution strategy | Problem handling approach |
| 09-02 | Problem record | Problem tracking |
| 09-03 | Analysis report | Root cause analysis |

---

### SUP.10: Change Request Management

#### Purpose

Manage changes to work products systematically.

#### Base Practices (ASPICE 4.0)

##### BP1: Develop Change Request Management Strategy

```yaml
Change Request Management Strategy:

1. Change Types:
   - Requirement changes
   - Design changes
   - Implementation changes
   - Process changes

2. Impact Assessment:
   - Technical impact
   - Schedule impact
   - Cost impact
   - Safety impact

3. Approval Levels:
   - Level 1 (Minor): Project lead
   - Level 2 (Moderate): Change control board
   - Level 3 (Major): Customer and management
```

##### BP2: Process Change Requests

```markdown
## Change Request: CR-[ID]

**Date**: YYYY-MM-DD
**Requested By**: [Name]
**Type**: [Requirement/Design/Implementation/Process]

### Change Description
[Detailed description of requested change]

### Rationale
[Why this change is needed]

### Impact Analysis
| Impact Area | Assessment |
|-------------|------------|
| Technical | [Impact] |
| Schedule | [Impact] |
| Cost | [Impact] |
| Safety | [Impact] |
| Traceability | [Impact] |

### Affected Work Products
| Work Product | Impact |
|--------------|--------|
| [WP ID] | [Description] |

### Recommendation
- [ ] Approve
- [ ] Approve with conditions
- [ ] Reject
```

##### BP3: Track Change Requests

```markdown
## Change Request Status: CR-[ID]

**Current Status**: [Submitted/Under Review/Approved/Implemented/Closed]

### Approval History
| Date | Approver | Decision | Comments |
|------|----------|----------|----------|
| YYYY-MM-DD | [Name] | [Decision] | [Comments] |

### Implementation Status
- [ ] Impact analysis completed
- [ ] Change implemented
- [ ] Review completed
- [ ] Documentation updated
- [ ] Verification completed
```

#### Work Products

| ID | Name | Description |
|----|------|-------------|
| 10-01 | Change request management strategy | Change handling approach |
| 10-02 | Change request record | Change tracking |

---

### SUP.11: Machine Learning Data Management (NEW in ASPICE 4.0)

#### Purpose

Ensure quality and traceability of ML data throughout the lifecycle.

#### Base Practices (ASPICE 4.0)

##### BP1: Develop ML Data Management Strategy

```yaml
ML Data Management Strategy:

1. Data Categories:
   - Training data
   - Validation data
   - Test data
   - Production data

2. Data Quality Criteria:
   - Completeness
   - Correctness
   - Consistency
   - Representativeness
   - Balance

3. Data Versioning:
   - Version control for datasets
   - Data lineage tracking
   - Change documentation

4. Data Security:
   - Access control
   - Encryption requirements
   - Privacy compliance
```

##### BP2: Identify and Collect Data

```markdown
## ML Dataset: DS-[ID]

**Name**: [Dataset name]
**Version**: X.Y
**Purpose**: [Training/Validation/Test]
**Date Created**: YYYY-MM-DD

### Data Sources
| Source | Description | Collection Method |
|--------|-------------|-------------------|
| [Source 1] | [Description] | [Method] |

### Data Statistics
- Total samples: X
- Features: [List]
- Labels: [List]

### Data Quality Metrics
| Metric | Value | Requirement |
|--------|-------|-------------|
| Completeness | X% | ≥ Y% |
| Correctness | X% | ≥ Y% |
| Balance | X:Y | [Ratio] |
```

##### BP3: Annotate and Label Data

```markdown
## Data Annotation Record

**Dataset**: DS-[ID]
**Annotation Guidelines**: [Document reference]

### Annotation Process
1. Annotation tool: [Tool name]
2. Annotation guidelines: [Reference]
3. Quality assurance: [Method]

### Inter-Annotator Agreement
- Agreement rate: X%
- Dispute resolution: [Method]

### Annotation Quality
| Metric | Value |
|--------|-------|
| Labeled samples | X |
| Validation accuracy | Y% |
```

##### BP4: Maintain Data Traceability

```markdown
## Data Lineage Record

**Dataset**: DS-[ID]
**Version**: X.Y

### Data Lineage
```
Raw Data (v1.0)
    │
    ├── Preprocessing (v1.1)
    │   └── Filter: [Description]
    │
    ├── Annotation (v1.2)
    │   └── Annotator: [Name]
    │
    └── Final Dataset (v2.0)
        └── Used for: Model training M-[ID]
```

### Related ML Models
| Model ID | Dataset Version | Purpose |
|----------|-----------------|---------|
| M-001 | v2.0 | Training |
| M-002 | v2.1 | Validation |
```

#### Work Products

| ID | Name | Description |
|----|------|-------------|
| 08-59 | ML dataset specification | Dataset description and statistics |
| 08-60 | Data annotation record | Annotation process documentation |
| 08-61 | Data lineage record | Data traceability |

---

## MAN Process Group

### MAN.3: Project Management

#### Purpose

Plan, monitor, and control the project.

#### Base Practices (ASPICE 4.0)

##### BP1: Define Project Scope

```yaml
Project Scope:

1. Project Objectives:
   - Technical objectives
   - Quality objectives
   - Schedule objectives
   - Cost objectives

2. Deliverables:
   - Work products
   - Milestones
   - Reviews

3. Boundaries:
   - In-scope items
   - Out-of-scope items
   - Interfaces to other projects
```

##### BP2: Develop Project Plan

```markdown
## Project Plan

### Project Organization
| Role | Responsibility | Person |
|------|----------------|--------|
| Project Manager | Overall management | [Name] |
| Technical Lead | Technical decisions | [Name] |
| Quality Manager | Quality assurance | [Name] |

### Project Schedule
| Phase | Start | End | Deliverables |
|-------|-------|-----|--------------|
| Requirements | YYYY-MM-DD | YYYY-MM-DD | SRS |
| Design | YYYY-MM-DD | YYYY-MM-DD | SAD |

### Resource Plan
| Resource | Allocation | Duration |
|----------|------------|----------|
| [Resource 1] | X% | Y months |

### Risk Management
| Risk | Mitigation | Owner |
|------|------------|-------|
| [Risk 1] | [Mitigation] | [Name] |

### Quality Plan
- Quality targets
- Review milestones
- Audit schedule
```

##### BP3: Monitor and Control Project

```markdown
## Project Status Report

**Reporting Period**: YYYY-MM-DD to YYYY-MM-DD
**Report Date**: YYYY-MM-DD

### Schedule Status
| Milestone | Planned | Actual | Status |
|-----------|---------|--------|--------|
| M1 | YYYY-MM-DD | YYYY-MM-DD | ✓/✗ |

### Effort Status
| Activity | Planned | Actual | Remaining |
|----------|---------|--------|-----------|
| Requirements | X h | Y h | Z h |

### Quality Status
| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Defects | ≤ X | Y | ✓/✗ |

### Risks and Issues
| Item | Status | Action |
|------|--------|--------|
| [Risk/Issue] | [Status] | [Action] |

### Next Steps
1. [Action 1]
2. [Action 2]
```

#### Work Products

| ID | Name | Description |
|----|------|-------------|
| 02-01 | Project plan | Overall project planning |
| 02-02 | Project status report | Progress tracking |

---

### MAN.5: Risk Management (NEW in ASPICE 4.0)

#### Purpose

Identify, analyze, and manage risks throughout the project.

#### Base Practices (ASPICE 4.0)

##### BP1: Develop Risk Management Strategy

```yaml
Risk Management Strategy:

1. Risk Categories:
   - Technical risks
   - Schedule risks
   - Resource risks
   - External risks
   - Safety risks

2. Risk Assessment Criteria:
   Probability:
   - 5: Almost certain (>90%)
   - 4: Likely (60-90%)
   - 3: Possible (30-60%)
   - 2: Unlikely (10-30%)
   - 1: Rare (<10%)

   Impact:
   - 5: Critical (project failure)
   - 4: Major (significant delay/cost)
   - 3: Moderate (manageable impact)
   - 2: Minor (small impact)
   - 1: Negligible (minimal impact)

3. Risk Tolerance:
   - High risk: Score ≥15 requires immediate action
   - Medium risk: Score 8-14 requires action plan
   - Low risk: Score ≤7 requires monitoring
```

##### BP2: Identify Risks

```markdown
## Risk Register

| Risk ID | Description | Category | Date Identified |
|---------|-------------|----------|-----------------|
| R-001 | [Risk description] | Technical | YYYY-MM-DD |
| R-002 | [Risk description] | Schedule | YYYY-MM-DD |
```

##### BP3: Analyze Risks

```markdown
## Risk Analysis: R-[ID]

### Risk Description
[Detailed description of the risk]

### Risk Assessment
| Factor | Score | Justification |
|--------|-------|---------------|
| Probability | X | [Reasoning] |
| Impact | Y | [Reasoning] |
| **Risk Score** | **X×Y = Z** | |

### Risk Level
- [ ] Low (Score ≤7)
- [ ] Medium (Score 8-14)
- [ ] High (Score ≥15)

### Affected Items
- Work Products: [List]
- Requirements: [List]
- Schedule: [Impact]
```

##### BP4: Develop Risk Mitigation

```markdown
## Risk Mitigation Plan: R-[ID]

### Mitigation Strategy
- [ ] Avoid: Eliminate the risk source
- [ ] Transfer: Transfer risk to another party
- [ ] Mitigate: Reduce probability or impact
- [ ] Accept: Accept risk with monitoring

### Mitigation Actions
| Action | Owner | Due Date | Status |
|--------|-------|----------|--------|
| [Action 1] | [Name] | YYYY-MM-DD | [Status] |

### Contingency Plan
[Plan if risk materializes]

### Residual Risk
- Probability after mitigation: X
- Impact after mitigation: Y
- Residual risk score: Z
```

##### BP5: Monitor Risks

```markdown
## Risk Monitoring Report

**Reporting Period**: YYYY-MM-DD

| Risk ID | Risk Level | Status | Actions Completed | Residual Score |
|---------|------------|--------|-------------------|----------------|
| R-001 | High | Open | 2/3 | 12 |
| R-002 | Medium | Mitigating | 1/2 | 8 |
```

#### Work Products

| ID | Name | Description |
|----|------|-------------|
| 02-03 | Risk management strategy | Risk handling approach |
| 02-04 | Risk register | Risk tracking |
| 02-05 | Risk report | Risk status |

---

### MAN.6: Measurement (NEW in ASPICE 4.0)

#### Purpose

Collect and analyze measurement data to support project management and process improvement.

#### Base Practices (ASPICE 4.0)

##### BP1: Develop Measurement Strategy

```yaml
Measurement Strategy:

1. Information Needs:
   - Project progress tracking
   - Quality monitoring
   - Process performance
   - Product characteristics

2. Measures (Metrics):
   - Process measures:
     - Effort variance
     - Schedule variance
     - Defect detection rate
   - Product measures:
     - Requirements volatility
     - Code complexity
     - Test coverage

3. Data Collection:
   - Collection methods
   - Collection frequency
   - Responsible persons

4. Data Analysis:
   - Analysis methods
   - Reporting frequency
   - Decision criteria
```

##### BP2: Collect Measurement Data

```markdown
## Measurement Data Collection

**Collection Date**: YYYY-MM-DD
**Collector**: [Name]

### Process Measures
| Measure | Value | Target | Status |
|---------|-------|--------|--------|
| Effort variance | X% | ≤ 10% | ✓/✗ |
| Schedule variance | Y% | ≤ 5% | ✓/✗ |
| Defect density | Z/KLOC | ≤ W/KLOC | ✓/✗ |

### Product Measures
| Measure | Value | Target | Status |
|---------|-------|--------|--------|
| Requirements volatility | X% | ≤ 20% | ✓/✗ |
| Code coverage | Y% | ≥ 80% | ✓/✗ |
| Open defects | Z | ≤ N | ✓/✗ |
```

##### BP3: Analyze Measurement Data

```markdown
## Measurement Analysis Report

**Analysis Period**: YYYY-MM-DD to YYYY-MM-DD

### Trend Analysis
| Measure | Previous | Current | Trend |
|---------|----------|---------|-------|
| Effort variance | X% | Y% | ↑/↓/→ |

### Key Findings
1. [Finding 1]
2. [Finding 2]

### Recommendations
1. [Recommendation 1]
2. [Recommendation 2]

### Actions
| Action | Owner | Due Date |
|--------|-------|----------|
| [Action 1] | [Name] | YYYY-MM-DD |
```

#### Work Products

| ID | Name | Description |
|----|------|-------------|
| 02-06 | Measurement strategy | Measurement approach |
| 02-07 | Measurement data | Collected measures |
| 02-08 | Measurement report | Analysis results |

---

## PIM Process Group

### PIM.3: Process Improvement (NEW in ASPICE 4.0)

#### Purpose

Continuously improve processes based on lessons learned and measurement results.

#### Base Practices (ASPICE 4.0)

##### BP1: Identify Process Improvements

```markdown
## Process Improvement Proposal: PIP-[ID]

**Date**: YYYY-MM-DD
**Proposer**: [Name]
**Process Affected**: [Process ID]

### Current State
[Description of current process and its issues]

### Proposed Improvement
[Description of proposed improvement]

### Expected Benefits
| Benefit | Quantification |
|---------|----------------|
| [Benefit 1] | [Quantitative estimate] |

### Implementation Effort
- Effort estimate: X person-days
- Resources required: [List]
```

##### BP2: Evaluate Process Improvements

```markdown
## Process Improvement Evaluation: PIP-[ID]

### Feasibility Assessment
| Criterion | Assessment |
|-----------|------------|
| Technical feasibility | ✓/✗ |
| Resource availability | ✓/✗ |
| Cost-benefit ratio | [Value] |

### Risk Assessment
| Risk | Impact | Mitigation |
|------|--------|------------|
| [Risk 1] | [Impact] | [Mitigation] |

### Recommendation
- [ ] Approve for implementation
- [ ] Approve with modifications
- [ ] Reject
```

##### BP3: Implement Process Improvements

```markdown
## Process Improvement Implementation: PIP-[ID]

**Implementation Date**: YYYY-MM-DD
**Implemented By**: [Name]

### Implementation Steps
1. [Step 1]
2. [Step 2]

### Updated Process Assets
| Asset | Update |
|-------|--------|
| Process description | [Changes] |
| Templates | [Changes] |
| Checklists | [Changes] |

### Training Provided
- Training session: [Date]
- Attendees: [List]
```

##### BP4: Evaluate Implementation

```markdown
## Process Improvement Evaluation Report: PIP-[ID]

**Evaluation Date**: YYYY-MM-DD

### Before/After Comparison
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| [Metric 1] | X | Y | Z% |

### Lessons Learned
1. [Lesson 1]
2. [Lesson 2]

### Status
- [ ] Fully successful
- [ ] Partially successful
- [ ] Needs further improvement
```

#### Work Products

| ID | Name | Description |
|----|------|-------------|
| 02-09 | Process improvement plan | Improvement planning |
| 02-10 | Process improvement record | Improvement tracking |

---

## REU Process Group

### REU.2: Reuse Product Management (NEW in ASPICE 4.0)

#### Purpose

Manage reusable assets across projects.

#### Base Practices (ASPICE 4.0)

##### BP1: Develop Reuse Strategy

```yaml
Reuse Strategy:

1. Reuse Categories:
   - Reuse without modification
   - Reuse with adaptation
   - Reuse of concept/design

2. Reuse Asset Types:
   - Requirements patterns
   - Architecture patterns
   - Source code components
   - Test cases
   - Documentation templates

3. Reuse Process:
   - Asset identification
   - Asset certification
   - Asset maintenance
   - Asset retirement
```

##### BP2: Identify Reusable Assets

```markdown
## Reuse Asset: RA-[ID]

**Name**: [Asset name]
**Type**: [Code/Design/Documentation/Test]
**Version**: X.Y
**Status**: [Active/Deprecated/Under Review]

### Asset Description
[Description of the asset]

### Applicability
- Domain: [Domain]
- ASIL: [A/B/C/D/QM]
- Environment: [Target environment]

### Dependencies
| Dependency | Version | Source |
|------------|---------|--------|
| [Dependency 1] | X.Y | [Source] |

### Quality Attributes
| Attribute | Value | Evidence |
|-----------|-------|----------|
| Code coverage | X% | [Report] |
| Static analysis | Clean | [Report] |
```

##### BP3: Maintain Reuse Assets

```markdown
## Reuse Asset Maintenance: RA-[ID]

### Change History
| Version | Date | Changes | Author |
|---------|------|---------|--------|
| X.Y | YYYY-MM-DD | [Changes] | [Name] |

### Known Issues
| Issue | Impact | Workaround |
|-------|--------|------------|
| [Issue 1] | [Impact] | [Workaround] |

### Usage Statistics
- Projects using this asset: X
- Success rate: Y%
```

#### Work Products

| ID | Name | Description |
|----|------|-------------|
| 02-11 | Reuse management strategy | Reuse approach |
| 02-12 | Reuse asset catalog | Asset inventory |

---

## References

- Automotive SPICE PAM v4.0 SUP/MAN/PIM/REU Process Groups
- ISO 26262 Functional safety requirements
- [6-aspice40-changes.md](6-aspice40-changes.md) - Complete change log

---

**Document Version**: 1.0
**Last Updated**: 2026-03-25
**Intended Audience**: Quality managers, project managers, process engineers
