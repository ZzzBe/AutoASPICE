#!/usr/bin/env python3
"""
Build Manifest Pipeline for AutoDev Studio.

Reads the automotive-claude-code-agents reference project and generates:
  1. agent_skill_manifest.json  -- Flat catalog of agents, skills, workflows, commands
  2. ecosystem_graph.json       -- Cytoscape-compatible node/edge graph

Uses ONLY Python 3 standard library. YAML parsed with regex.
"""

import json, os, re, sys, argparse
from datetime import datetime, timezone
from pathlib import Path


# ── Configuration ────────────────────────────────────────────────────────────

# Default paths (override with --ref-main, --ref-v2 or AUTODEV_REF_MAIN, AUTODEV_REF_V2 env vars)
REFERENCE_ROOT = os.environ.get("AUTODEV_REF_MAIN",
    os.path.expanduser("~/Desktop/miniprogram/autoagent/参考项目/automotive-claude-code-agents-main"))
REFERENCE_ROOT_V2 = os.environ.get("AUTODEV_REF_V2",
    os.path.expanduser("~/Desktop/miniprogram/autoagent/参考项目/automotive-claude-code-agents"))
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

SOURCE_REPOS = {
    "automotive-claude-code-agents-main": {
        "author": "Thejeswara Reddy R",
        "github_url": "https://github.com/im-hashim/automotive-claude-code-agents",
        "github_raw_root": "https://raw.githubusercontent.com/im-hashim/automotive-claude-code-agents/main/",
    },
    "automotive-claude-code-agents": {
        "author": "Yuxin ZHANG",
        "github_url": "https://github.com/AutoZYX-Labs/automotive-claude-code-agents",
        "github_raw_root": "https://raw.githubusercontent.com/AutoZYX-Labs/automotive-claude-code-agents/main/",
    },
}

# Pre-installed agent names (V1: 5 domains x 9 agents)
PREINSTALL_AGENTS = [
    "perception-engineer", "control-engineer", "planning-engineer",
    "hara-specialist", "fmea-analyst", "safety-case-writer",
    "sotif-analyst", "autosar-architect", "diagnostic-engineer",
]

# Domain metadata
DOMAIN_META = {
    "adas": {"name": "ADAS/Autonomous Driving"},
    "functional-safety": {"name": "Functional Safety"},
    "sotif": {"name": "SOTIF / ISO 21448"},
    "autosar": {"name": "AUTOSAR"},
    "diagnostics": {"name": "Diagnostics"},
    "cybersecurity": {"name": "Cybersecurity / ISO 21434"},
    "battery": {"name": "Battery / EV Systems"},
    "cloud": {"name": "Cloud / Connected Services"},
    "cockpit": {"name": "Cockpit / HMI"},
    "ev-systems": {"name": "EV Systems"},
    "hpc-platform": {"name": "HPC Platform"},
    "mbd": {"name": "Model-Based Development"},
    "ml-analytics": {"name": "ML / Analytics"},
    "oem": {"name": "OEM"},
    "powertrain-chassis": {"name": "Powertrain & Chassis"},
    "security": {"name": "Security"},
    "testing": {"name": "Testing"},
    "v2x": {"name": "V2X"},
    "vehicle-systems": {"name": "Vehicle Systems"},
    "zonal-architecture": {"name": "Zonal Architecture"},
    "safety": {"name": "Safety"},
}

# Map agent domains to primary skill categories for domain-based matching.
# When an agent is in domain X, we strongly prefer skills with these categories.
AGENT_TO_SKILL_CATEGORIES = {
    "adas": ["adas"],
    "functional-safety": ["safety", "safety-analysis"],
    "sotif": ["sotif"],
    "autosar": ["autosar"],
    "diagnostics": ["diagnostics"],
    "battery": ["battery", "battery-lifecycle", "charging-infrastructure"],
    "cybersecurity": ["security", "security-systems"],
    "cloud": ["cloud", "cloud-native"],
    "cockpit": ["hmi", "cockpit-interior", "audio", "driver-monitoring"],
    "ev-systems": ["battery", "charging-infrastructure", "ev-tools"],
    "hpc-platform": ["embedded", "middleware", "kubernetes"],
    "mbd": ["mbd"],
    "ml-analytics": ["automotive-ml", "adas"],
    "oem": ["oem-decision-making", "regulatory-compliance"],
    "powertrain-chassis": ["powertrain", "chassis", "transmission"],
    "security": ["security", "security-systems", "access-control"],
    "testing": ["testing", "hil-sil"],
    "v2x": ["v2x", "network", "telematics"],
    "vehicle-systems": ["body", "hvac", "lighting", "comfort", "steering",
                         "braking", "suspension", "occupant-safety", "parking"],
    "zonal-architecture": ["network", "middleware", "embedded"],
    "calibration": ["calibration"],
    "orchestration": [],
    "automotive-workflow": [],
    "core": [],
}

# ── Simple YAML Parser (regex-based, no pyyaml) ─────────────────────────────

def parse_yaml(text):
    """
    Parse a subset of YAML into a Python dict.
    Handles:
      - key: value
      - key: |  (literal block scalar)
      - key: >  (folded block scalar)
      - lists: - item
      - nested maps (via indentation)
      - quoted strings
    Returns a dict.
    """
    if not text or not text.strip():
        return {}

    # Strip YAML frontmatter (--- delimiters)
    text = re.sub(r'^---\s*\n', '', text)
    text = re.sub(r'\n---\s*$', '', text)
    text = re.sub(r'^\.\.\.\s*\n?', '', text)

    result = {}
    lines = text.split('\n')
    i = 0

    def get_indent(line):
        stripped = line.lstrip(' ')
        return len(line) - len(stripped)

    def parse_value(val_str):
        """Parse a scalar value."""
        val_str = val_str.strip()
        # Remove surrounding quotes
        if (val_str.startswith('"') and val_str.endswith('"')) or \
           (val_str.startswith("'") and val_str.endswith("'")):
            val_str = val_str[1:-1]
        return val_str

    def read_block_scalar(start_idx, key):
        """Read a | or > block scalar starting at start_idx+1."""
        lines_out = []
        j = start_idx + 1
        base_indent = None
        while j < len(lines):
            line = lines[j]
            if not line.strip():
                lines_out.append('')
                j += 1
                continue
            indent = get_indent(line)
            if base_indent is None:
                base_indent = indent
            if indent < base_indent and line.strip():
                break
            if indent >= base_indent:
                lines_out.append(line[base_indent:] if base_indent > 0 else line)
            else:
                lines_out.append(line)
            j += 1
        return '\n'.join(lines_out).strip(), j

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped or stripped.startswith('#'):
            i += 1
            continue

        indent = get_indent(line)

        kv_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*(.*)', stripped)
        if kv_match:
            key = kv_match.group(1)
            val_part = kv_match.group(2)

            if not val_part:
                j = i + 1
                if j >= len(lines):
                    result[key] = ''
                    i = j
                    continue

                next_stripped = lines[j].strip()

                if next_stripped in ('|', '>', '|-', '>-'):
                    val, next_i = read_block_scalar(j, key)
                    result[key] = val
                    i = next_i
                    continue

                if next_stripped.startswith('- '):
                    items = []
                    while j < len(lines):
                        sj = lines[j].strip()
                        if sj.startswith('- '):
                            items.append(parse_value(sj[2:]))
                            j += 1
                        elif not sj or sj.startswith('#'):
                            j += 1
                        else:
                            break
                    result[key] = items
                    i = j
                    continue

                child_indent = get_indent(lines[j])
                if child_indent > indent:
                    child_lines = []
                    while j < len(lines):
                        if not lines[j].strip():
                            child_lines.append(lines[j])
                            j += 1
                            continue
                        if get_indent(lines[j]) > indent:
                            child_lines.append(lines[j])
                            j += 1
                        else:
                            break
                    result[key] = parse_yaml('\n'.join(child_lines))
                    i = j
                    continue

                result[key] = ''
                i = j
            else:
                result[key] = parse_value(val_part)
                i += 1
        elif stripped.startswith('- '):
            i += 1
        else:
            i += 1

    return result


def parse_yaml_file(filepath):
    """Read and parse a YAML file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return parse_yaml(content)
    except Exception as e:
        print(f"  [WARN] Failed to parse {filepath}: {e}")
        return {}


# ── Data Collectors ──────────────────────────────────────────────────────────

def collect_agents(ref_root):
    """Walk agents/ directory and collect all agent definitions."""
    agents = {}
    agents_dir = os.path.join(ref_root, 'agents')
    if not os.path.isdir(agents_dir):
        print(f"  [WARN] agents/ directory not found at {agents_dir}")
        return agents

    yaml_count = 0
    for root, dirs, files in os.walk(agents_dir):
        rel_dir = os.path.relpath(root, agents_dir)
        domain = rel_dir.split(os.sep)[0] if rel_dir != '.' else 'unknown'

        for fname in files:
            if fname.endswith('.yaml') or fname.endswith('.yml'):
                yaml_count += 1
                filepath = os.path.join(root, fname)
                data = parse_yaml_file(filepath)

                agent_name = data.get('name', fname.rsplit('.', 1)[0])
                if isinstance(agent_name, str):
                    agent_name = agent_name.strip().lower().replace(' ', '-')

                # --- Capabilities ---
                raw_caps = data.get('capabilities', [])
                if isinstance(raw_caps, str):
                    caps_text = raw_caps.strip()
                    if '\n' in caps_text:
                        raw_caps = [
                            c.strip().lstrip('-').strip().strip('"').strip("'")
                            for c in caps_text.split('\n') if c.strip()
                        ]
                    else:
                        raw_caps = [caps_text]

                capabilities = []
                for c in raw_caps:
                    if isinstance(c, str):
                        c = c.strip().strip('"').strip("'")
                        if c:
                            capabilities.append(c)

                # --- Workflows from agent data ---
                agent_workflows = []
                wf_data = data.get('workflows', None)
                if isinstance(wf_data, dict):
                    for wf_name, wf_info in wf_data.items():
                        wf_entry = {
                            "name": wf_name,
                            "description": wf_info.get('description', '') if isinstance(wf_info, dict) else str(wf_info),
                            "steps": wf_info.get('steps', []) if isinstance(wf_info, dict) else []
                        }
                        agent_workflows.append(wf_entry)
                elif isinstance(wf_data, list):
                    for item in wf_data:
                        if isinstance(item, str):
                            agent_workflows.append({
                                "name": item.lower().replace(' ', '_')[:60],
                                "description": item,
                                "steps": []
                            })
                        elif isinstance(item, dict):
                            agent_workflows.append({
                                "name": item.get('name', ''),
                                "description": item.get('description', ''),
                                "steps": item.get('steps', [])
                            })

                # --- Expertise areas ---
                raw_exp = data.get('expertise_areas', data.get('expertise', []))
                if isinstance(raw_exp, str):
                    expertise_areas = [e.strip().strip('"').strip("'") for e in raw_exp.split('\n') if e.strip()]
                elif isinstance(raw_exp, list):
                    expertise_areas = [
                        e.strip().strip('"').strip("'") if isinstance(e, str) else str(e)
                        for e in raw_exp
                    ]
                else:
                    expertise_areas = []

                # --- Tools ---
                raw_tools = data.get('tools', data.get('tool_dependencies', []))
                if isinstance(raw_tools, str):
                    tools = [t.strip().strip('"').strip("'") for t in raw_tools.split('\n') if t.strip()]
                elif isinstance(raw_tools, list):
                    tools = [
                        t.strip().strip('"').strip("'") if isinstance(t, str) else str(t)
                        for t in raw_tools
                    ]
                elif isinstance(raw_tools, dict):
                    req = raw_tools.get('required', [])
                    opt = raw_tools.get('optional', [])
                    tools = (req if isinstance(req, list) else []) + (opt if isinstance(opt, list) else [])
                else:
                    tools = []

                # Clean tool names: extract identifier from descriptive text
                # "carla_adapter for simulation testing" -> "carla_adapter"
                cleaned_tools = []
                for t in tools:
                    if not isinstance(t, str):
                        cleaned_tools.append(str(t))
                        continue
                    # If it contains " for " or " to ", take the first part
                    for sep in [' for ', ' to ', ' - ', ' (', ': ']:
                        idx = t.find(sep)
                        if idx > 0:
                            t = t[:idx]
                    t = t.strip().strip('"').strip("'")
                    if t:
                        cleaned_tools.append(t)
                tools = cleaned_tools

                # --- Guidelines ---
                raw_guidelines = data.get('guidelines', [])
                if isinstance(raw_guidelines, str):
                    guidelines = [g.strip().strip('"').strip("'") for g in raw_guidelines.split('\n') if g.strip()]
                elif isinstance(raw_guidelines, list):
                    guidelines = [
                        g.strip().strip('"').strip("'") if isinstance(g, str) else str(g)
                        for g in raw_guidelines
                    ]
                else:
                    guidelines = []

                # --- Standards ---
                raw_standards = data.get('automotive_standards', data.get('standards', []))
                if isinstance(raw_standards, str):
                    standards = [s.strip().strip('"').strip("'") for s in raw_standards.split('\n') if s.strip()]
                elif isinstance(raw_standards, list):
                    standards = [
                        s.strip().strip('"').strip("'") if isinstance(s, str) else str(s)
                        for s in raw_standards
                    ]
                else:
                    standards = []

                # --- Description ---
                description = data.get('description', '')
                if isinstance(description, str):
                    description = description.strip()

                agents[agent_name] = {
                    "name": agent_name,
                    "domain": domain,
                    "description": description,
                    "agent_file": os.path.relpath(filepath, ref_root),
                    "capabilities": capabilities,
                    "required_skills": [],
                    "workflows": agent_workflows,
                    "tool_dependencies": tools,
                    "expertise_areas": expertise_areas,
                    "standards": standards,
                    "guidelines": guidelines,
                }

    print(f"  Collected {yaml_count} agent YAML files -> {len(agents)} unique agents")
    return agents


def collect_skills(ref_root):
    """Walk skills/ directory and collect all skill definitions."""
    skills = {}
    skills_dir = os.path.join(ref_root, 'skills')
    if not os.path.isdir(skills_dir):
        print(f"  [WARN] skills/ directory not found at {skills_dir}")
        return skills

    yaml_count = 0
    for root, dirs, files in os.walk(skills_dir):
        if '_templates' in root.split(os.sep):
            continue

        rel_dir = os.path.relpath(root, skills_dir)
        category = rel_dir.split(os.sep)[0] if rel_dir != '.' else 'unknown'

        # Also capture subcategory (e.g., "adas/perception" -> subcategory "perception")
        subcategory = ''
        parts = rel_dir.split(os.sep)
        if len(parts) >= 2:
            subcategory = parts[1]

        for fname in files:
            if fname.endswith('.yaml') or fname.endswith('.yml'):
                yaml_count += 1
                filepath = os.path.join(root, fname)
                data = parse_yaml_file(filepath)

                skill_name = data.get('name', fname.rsplit('.', 1)[0])
                if isinstance(skill_name, str):
                    skill_name = skill_name.strip()

                description = data.get('description', '')
                if isinstance(description, str):
                    description = description.strip()

                raw_use = data.get('use_cases', [])
                if isinstance(raw_use, str):
                    use_cases = [u.strip() for u in raw_use.split('\n') if u.strip()]
                elif isinstance(raw_use, list):
                    use_cases = [u.strip() if isinstance(u, str) else str(u) for u in raw_use]
                else:
                    use_cases = []

                raw_standards = data.get('automotive_standards', [])
                if isinstance(raw_standards, str):
                    automotive_standards = [s.strip() for s in raw_standards.split('\n') if s.strip()]
                elif isinstance(raw_standards, list):
                    automotive_standards = [s.strip() if isinstance(s, str) else str(s) for s in raw_standards]
                else:
                    automotive_standards = []

                raw_tools = data.get('tools_required', data.get('tools', []))
                if isinstance(raw_tools, str):
                    tools_required = [t.strip() for t in raw_tools.split('\n') if t.strip()]
                elif isinstance(raw_tools, list):
                    tools_required = [t.strip() if isinstance(t, str) else str(t) for t in raw_tools]
                else:
                    tools_required = []

                raw_tags = data.get('tags', [])
                if isinstance(raw_tags, str):
                    tags = [t.strip() for t in raw_tags.split('\n') if t.strip()]
                elif isinstance(raw_tags, list):
                    tags = [t.strip() if isinstance(t, str) else str(t) for t in raw_tags]
                else:
                    tags = []

                version = data.get('version', '1.0.0')
                file_subcat = data.get('subcategory', subcategory)

                skills[skill_name] = {
                    "name": skill_name,
                    "path": os.path.relpath(filepath, ref_root),
                    "category": category,
                    "subcategory": file_subcat,
                    "domain": data.get('domain', 'automotive'),
                    "description": description,
                    "use_cases": use_cases,
                    "automotive_standards": automotive_standards,
                    "tools_required": tools_required,
                    "tags": tags,
                    "version": version,
                    "used_by": [],
                }

    print(f"  Collected {yaml_count} skill YAML files -> {len(skills)} unique skills")
    return skills


def collect_workflows(ref_root):
    """Walk workflows/ directory and collect all workflow definitions."""
    workflows = {}
    workflows_dir = os.path.join(ref_root, 'workflows')
    if not os.path.isdir(workflows_dir):
        print(f"  [WARN] workflows/ directory not found at {workflows_dir}")
        return workflows

    yaml_count = 0
    for root, dirs, files in os.walk(workflows_dir):
        rel_dir = os.path.relpath(root, workflows_dir)
        domain = rel_dir.split(os.sep)[0] if rel_dir != '.' else 'unknown'

        for fname in files:
            if fname.endswith('.yaml') or fname.endswith('.yml'):
                yaml_count += 1
                filepath = os.path.join(root, fname)
                data = parse_yaml_file(filepath)

                wf_name = data.get('name', fname.rsplit('.', 1)[0])
                if isinstance(wf_name, str):
                    wf_name = wf_name.strip()

                description = data.get('description', '')
                if isinstance(description, str):
                    description = description.strip()

                steps = []
                phases = data.get('phases', [])
                if isinstance(phases, list):
                    for phase in phases:
                        if isinstance(phase, dict):
                            phase_steps = phase.get('steps', [])
                            if isinstance(phase_steps, list):
                                steps.extend([s.strip() if isinstance(s, str) else str(s) for s in phase_steps])
                elif isinstance(phases, str):
                    steps = [s.strip() for s in phases.split('\n') if s.strip()]

                direct_steps = data.get('steps', [])
                if isinstance(direct_steps, list):
                    steps.extend([s.strip() if isinstance(s, str) else str(s) for s in direct_steps])
                elif isinstance(direct_steps, str):
                    steps.extend([s.strip() for s in direct_steps.split('\n') if s.strip()])

                # Extract agents_involved if present (Convention B workflows)
                agents_involved = []
                for phase in (phases if isinstance(phases, list) else []):
                    if isinstance(phase, dict):
                        ai = phase.get('agents_involved', [])
                        if isinstance(ai, list):
                            agents_involved.extend([a.strip() if isinstance(a, str) else str(a) for a in ai])

                # Extract skills_used if present
                skills_used = []
                for phase in (phases if isinstance(phases, list) else []):
                    if isinstance(phase, dict):
                        su = phase.get('skills_used', [])
                        if isinstance(su, list):
                            skills_used.extend([s.strip() if isinstance(s, str) else str(s) for s in su])

                workflows[wf_name] = {
                    "name": wf_name,
                    "path": os.path.relpath(filepath, ref_root),
                    "domain": domain,
                    "description": description,
                    "steps": steps,
                    "step_count": len(steps),
                    "safety_level": data.get('safety_level', ''),
                    "trigger": data.get('trigger', ''),
                    "agents_involved": agents_involved,
                    "skills_used": skills_used,
                }

    print(f"  Collected {yaml_count} workflow YAML files -> {len(workflows)} unique workflows")
    return workflows


def collect_commands(ref_root):
    """Walk commands/ directory and list all shell scripts."""
    commands = {}
    commands_dir = os.path.join(ref_root, 'commands')
    if not os.path.isdir(commands_dir):
        print(f"  [WARN] commands/ directory not found at {commands_dir}")
        return commands

    sh_count = 0
    for root, dirs, files in os.walk(commands_dir):
        rel_dir = os.path.relpath(root, commands_dir)
        domain = rel_dir.split(os.sep)[0] if rel_dir != '.' else 'unknown'

        for fname in files:
            if fname.endswith('.sh'):
                sh_count += 1
                filepath = os.path.join(root, fname)
                cmd_name = fname.rsplit('.', 1)[0]
                label = f"{domain}/{cmd_name}"

                commands[label] = {
                    "name": cmd_name,
                    "label": label,
                    "domain": domain,
                    "path": os.path.relpath(filepath, ref_root),
                    "filename": fname,
                }

    print(f"  Collected {sh_count} command shell scripts -> {len(commands)} unique commands")
    return commands


# ── Capability-to-Skill Matching (Improved) ──────────────────────────────────

# Generic/short words that shouldn't drive matching
STOP_WORDS = {
    'and', 'or', 'the', 'a', 'an', 'for', 'of', 'in', 'to', 'with', 'is', 'at',
    'on', 'by', 'be', 'as', 'no', 'not', 'all', 'any', 'it', 'its', 'this', 'that',
    'from', 'into', 'use', 'used', 'using', 'can', 'has', 'have', 'will', 'may',
    'data', 'system', 'systems', 'design', 'analysis', 'based', 'development',
    'process', 'model', 'models', 'test', 'testing', 'control', 'management',
}


def tokenize(text):
    """Normalize and tokenize text into a set of meaningful keywords."""
    text = text.lower()
    # Normalize separators to spaces
    text = text.replace('-', ' ').replace('_', ' ').replace('/', ' ')
    # Strip punctuation from individual words
    import string as _string
    words = set()
    for w in text.split():
        w = w.strip(_string.punctuation)
        if w:
            words.add(w)
    return words - STOP_WORDS


def match_capability_to_skills(capability, agent_domain, skill_index):
    """
    Match a capability string to actual skill files.
    Multi-stage matching:
      1. Exact name match (highest confidence)
      2. Capability tokens are subset of skill tokens (or vice versa)
      3. Domain-prioritized keyword overlap (>= 1 in-domain, >= 2 cross-domain)
    Returns list of skill info dicts (top 5).
    """
    cap_tokens = tokenize(capability)
    if not cap_tokens:
        return []

    # Get preferred skill categories for this agent domain
    preferred_categories = set(
        AGENT_TO_SKILL_CATEGORIES.get(agent_domain, [agent_domain])
    )

    # Normalize capability as a single string
    cap_normalized = capability.lower().replace('-', ' ').replace('_', ' ').strip()

    candidates = []

    for skill_name, skill_info in skill_index.items():
        skill_normalized = skill_name.lower().replace('-', ' ').replace('_', ' ').strip()
        skill_tokens = tokenize(skill_name)
        skill_category = skill_info.get('category', '')
        in_domain = skill_category in preferred_categories

        # Tier 1: Exact name match (after normalization)
        if cap_normalized == skill_normalized:
            candidates.append((skill_info, 100.0, 'exact'))
            continue

        # Tier 2a: All capability tokens contained in skill name
        # (e.g., capability "camera object detection" matches skill "camera-object-detection-001")
        if cap_tokens.issubset(skill_tokens):
            score = 50.0 if in_domain else 20.0
            candidates.append((skill_info, score, 'subset' if in_domain else 'subset_xdomain'))
            continue

        # Tier 2b: All skill tokens contained in capability tokens
        # (e.g., capability sentence "... FMEA ..." matches skill "fmea-016")
        if skill_tokens and skill_tokens.issubset(cap_tokens):
            score = 45.0 if in_domain else 15.0
            candidates.append((skill_info, score, 'skill_in_cap' if in_domain else 'skill_in_cap_xd'))
            continue

        # Tier 3: Keyword overlap
        overlap = len(cap_tokens & skill_tokens)

        # In-domain: accept single keyword match with bonus
        # Cross-domain: require >= 2 overlapping keywords
        min_overlap = 1 if in_domain else 2
        if overlap >= min_overlap:
            total_tokens = len(cap_tokens | skill_tokens)
            jaccard = overlap / max(total_tokens, 1)

            base_score = overlap * 5.0 + jaccard * 10.0
            domain_bonus = 10.0 if in_domain else 0.0
            score = base_score + domain_bonus

            if score >= 3.0:
                candidates.append((skill_info, score, 'overlap_domain' if in_domain else 'overlap_xdomain'))

    # Sort by score descending
    candidates.sort(key=lambda x: -x[1])

    # Return top 5, but only include cross-domain if results are sparse
    result = []
    in_domain_results = [c for c in candidates if c[2] in ('exact', 'subset', 'skill_in_cap', 'overlap_domain')]
    xdomain_results = [c for c in candidates if c[2] in ('subset_xdomain', 'skill_in_cap_xd', 'overlap_xdomain')]

    result.extend(in_domain_results[:5])
    if len(result) < 3:
        result.extend(xdomain_results[: (5 - len(result))])

    return [c[0] for c in result[:5]]


def link_capabilities_to_skills(agents, skill_index):
    """
    For each agent, match its capabilities to skills and populate required_skills.
    Also populate used_by on each skill.
    """
    for agent_name, agent in agents.items():
        agent_domain = agent.get('domain', '')
        capabilities = agent.get('capabilities', [])
        matched_skills = []
        seen_skill_names = set()

        for cap in capabilities:
            matches = match_capability_to_skills(cap, agent_domain, skill_index)
            for skill_info in matches:
                skill_name = skill_info['name']
                if skill_name not in seen_skill_names:
                    seen_skill_names.add(skill_name)
                    entry = {
                        "name": skill_name,
                        "path": skill_info['path'],
                        "category": skill_info['category'],
                    }
                    matched_skills.append(entry)

                    # Populate skill_index used_by
                    if skill_name in skill_index:
                        skill_index[skill_name].setdefault('used_by', []).append(agent_name)

        agent['required_skills'] = matched_skills


# ── Synthetic Agent for Missing V1 Targets ───────────────────────────────────

def ensure_v1_targets(agents, ref_root):
    """Ensure all preinstall target agents exist. Try local YAMLs first, then create synthetic entries."""
    created = []
    # Path to local agents directory (autodev-studio/agents/)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_agents_root = os.path.join(script_dir, '..', 'agents')

    for agent_name in PREINSTALL_AGENTS:
        if agent_name in agents:
            continue

        # Derive domain from agent name pattern
        if "control" in agent_name or "perception" in agent_name or "planning" in agent_name:
            dom = "adas"
        elif "hara" in agent_name or "fmea" in agent_name or "safety-case" in agent_name:
            dom = "functional-safety"
        elif "sotif" in agent_name: dom = "sotif"
        elif "autosar" in agent_name or "architect" in agent_name: dom = "autosar"
        elif "diagnostic" in agent_name: dom = "diagnostics"
        else: dom = "unknown"

        synthetic = True
        capabilities = []
        expertise_areas = []
        workflows = {}
        tool_dependencies = []
        standards = []
        guidelines = []
        description = f"{agent_name} (synthetic - not found in ref)"
        agent_file_path = f"agents/{dom}/{agent_name}.yaml"

        # Try to read actual YAML from local agents directory
        local_yaml_path = os.path.join(local_agents_root, dom, f"{agent_name}.yaml")
        if os.path.isfile(local_yaml_path):
            data = parse_yaml_file(local_yaml_path)
            if data:
                synthetic = False
                description = data.get('description', description)
                capabilities = data.get('capabilities', [])
                expertise_areas = data.get('expertise_areas', [])
                tool_dependencies = data.get('tools', [])
                guidelines = data.get('guidelines', [])
                standards_list = data.get('standards', [])
                if isinstance(standards_list, list):
                    standards = standards_list
                # Parse workflows map
                wf_data = data.get('workflows', {})
                if isinstance(wf_data, dict):
                    for wf_name, wf in wf_data.items():
                        if isinstance(wf, dict):
                            workflows[wf_name] = {
                                "description": wf.get("description", ""),
                                "step_count": len(wf.get("steps", [])),
                                "steps": wf.get("steps", []),
                                "domain": dom,
                            }
                agent_file_path = f"agents/{dom}/{agent_name}.yaml"

        # Also try to find the YAML anywhere in local_agents_root (deep search)
        if synthetic:
            for root, _, files in os.walk(local_agents_root):
                fname = f"{agent_name}.yaml"
                if fname in files:
                    found_path = os.path.join(root, fname)
                    data = parse_yaml_file(found_path)
                    if data:
                        synthetic = False
                        found_dom = os.path.relpath(root, local_agents_root)
                        dom = found_dom if found_dom != '.' else dom
                        description = data.get('description', description)
                        capabilities = data.get('capabilities', [])
                        expertise_areas = data.get('expertise_areas', [])
                        tool_dependencies = data.get('tools', [])
                        guidelines = data.get('guidelines', [])
                        standards_list = data.get('standards', [])
                        if isinstance(standards_list, list):
                            standards = standards_list
                        wf_data = data.get('workflows', {})
                        if isinstance(wf_data, dict):
                            for wf_name, wf in wf_data.items():
                                if isinstance(wf, dict):
                                    workflows[wf_name] = {
                                        "description": wf.get("description", ""),
                                        "step_count": len(wf.get("steps", [])),
                                        "steps": wf.get("steps", []),
                                        "domain": dom,
                                    }
                        agent_file_path = f"agents/{dom}/{agent_name}.yaml"
                    break

        agents[agent_name] = {
            "name": agent_name, "domain": dom,
            "description": description,
            "agent_file": agent_file_path,
            "capabilities": capabilities,
            "required_skills": [],
            "workflows": workflows,
            "tool_dependencies": tool_dependencies,
            "expertise_areas": expertise_areas,
            "standards": standards,
            "guidelines": guidelines,
            "synthetic": synthetic,
        }
        created.append(f"{dom}/{agent_name}")
    return created


# ── Domain Aggregation ────────────────────────────────────────────────────────

def build_domains(agents, skills, workflows):
    """Aggregate domain statistics."""
    domains = {}

    for agent_name, agent in agents.items():
        domain = agent.get('domain', 'unknown')
        if domain not in domains:
            domains[domain] = {
                "name": DOMAIN_META.get(domain, {}).get("name", domain.replace('-', ' ').title()),
                "agent_count": 0,
                "skill_count": 0,
                "workflow_count": 0,
            }
        domains[domain]["agent_count"] += 1

    for skill_name, skill in skills.items():
        category = skill.get('category', 'unknown')
        if category not in domains:
            domains[category] = {
                "name": DOMAIN_META.get(category, {}).get("name", category.replace('-', ' ').title()),
                "agent_count": 0,
                "skill_count": 0,
                "workflow_count": 0,
            }
        domains[category]["skill_count"] += 1

    for wf_name, wf in workflows.items():
        domain = wf.get('domain', 'unknown')
        if domain not in domains:
            domains[domain] = {
                "name": DOMAIN_META.get(domain, {}).get("name", domain.replace('-', ' ').title()),
                "agent_count": 0,
                "skill_count": 0,
                "workflow_count": 0,
            }
        domains[domain]["workflow_count"] += 1

    return domains


# ── Ecosystem Graph Builder ───────────────────────────────────────────────────

def build_ecosystem_graph(agents, skill_index, workflows, commands):
    """Build the nodes and edges for the ecosystem graph."""
    nodes = []
    edges = []
    edge_counter = 1

    # Agent nodes
    for agent_name, agent in agents.items():
        nodes.append({
            "data": {
                "id": f"agent-{agent_name}",
                "label": agent_name,
                "type": "agent",
                "domain": agent.get('domain', 'unknown'),
                "description": agent.get('description', ''),
                "capability_count": len(agent.get('capabilities', [])),
                "skill_count": len(agent.get('required_skills', [])),
                "status": "inactive",
            }
        })

    # Skill nodes
    for skill_name, skill in skill_index.items():
        nodes.append({
            "data": {
                "id": f"skill-{skill_name}",
                "label": skill_name,
                "type": "skill",
                "domain": skill.get('category', 'unknown'),
                "category": skill.get('category', 'unknown'),
                "used_by_count": len(skill.get('used_by', [])),
            }
        })

    # Workflow nodes
    for wf_name, wf in workflows.items():
        orchestrates = []
        for agent_name, agent in agents.items():
            agent_domain = agent.get('domain', '')
            wf_domain = wf.get('domain', '')
            if wf_domain == agent_domain or wf_domain in agent_domain or agent_domain in wf_domain:
                orchestrates.append(agent_name)
        nodes.append({
            "data": {
                "id": f"workflow-{wf_name}",
                "label": wf_name,
                "type": "workflow",
                "domain": wf.get('domain', 'unknown'),
                "step_count": wf.get('step_count', 0),
                "orchestrates": orchestrates,
            }
        })

    # Command nodes
    for cmd_label, cmd in commands.items():
        safe_id = cmd_label.replace('/', '-').replace(' ', '-')
        nodes.append({
            "data": {
                "id": f"command-{safe_id}",
                "label": cmd_label,
                "type": "command",
                "domain": cmd.get('domain', 'unknown'),
            }
        })

    # Edges: agent calls skill
    for agent_name, agent in agents.items():
        for skill_entry in agent.get('required_skills', []):
            skill_name = skill_entry['name']
            edges.append({
                "data": {
                    "id": f"edge-agent-skill-{edge_counter}",
                    "source": f"agent-{agent_name}",
                    "target": f"skill-{skill_name}",
                    "type": "calls",
                    "label": "calls",
                }
            })
            edge_counter += 1

    # Edges: workflow orchestrates agent (same domain only)
    for wf_name, wf in workflows.items():
        wf_domain = wf.get('domain', '')
        for agent_name, agent in agents.items():
            agent_domain = agent.get('domain', '')
            if wf_domain == agent_domain:
                edges.append({
                    "data": {
                        "id": f"edge-workflow-agent-{edge_counter}",
                        "source": f"workflow-{wf_name}",
                        "target": f"agent-{agent_name}",
                        "type": "orchestrates",
                        "label": "orchestrates",
                    }
                })
                edge_counter += 1

        # Edges: workflow uses skills (same domain)
        for skill_name, skill in skill_index.items():
            if skill.get('category', '') == wf_domain:
                edges.append({
                    "data": {
                        "id": f"edge-workflow-skill-{edge_counter}",
                        "source": f"workflow-{wf_name}",
                        "target": f"skill-{skill_name}",
                        "type": "uses",
                        "label": "uses",
                    }
                })
                edge_counter += 1

    # Edges: command -> agent (same domain)
    for cmd_label, cmd in commands.items():
        cmd_domain = cmd.get('domain', '')
        for agent_name, agent in agents.items():
            if agent.get('domain', '') == cmd_domain:
                safe_cmd_id = cmd_label.replace('/', '-').replace(' ', '-')
                edges.append({
                    "data": {
                        "id": f"edge-command-agent-{edge_counter}",
                        "source": f"command-{safe_cmd_id}",
                        "target": f"agent-{agent_name}",
                        "type": "triggers",
                        "label": "triggers",
                    }
                })
                edge_counter += 1

    return {
        "elements": {
            "nodes": nodes,
            "edges": edges,
        }
    }


# ── Validate V1 Target Agents ─────────────────────────────────────────────────

def validate_v1_targets(agents):
    """Check which preinstall agents are present/missing."""
    missing = []
    present = []
    for agent_name in PREINSTALL_AGENTS:
        if agent_name in agents:
            a = agents[agent_name]
            sfx = " [SYNTHETIC]" if a.get("synthetic") else ""
            present.append(f"{a.get('domain','?')}/{agent_name}{sfx}")
        else:
            missing.append(agent_name)

    if missing:
        print(f"  [INFO] {len(missing)} preinstall agents NOT FOUND:")
        for m in missing: print(f"         - {m}")
    print(f"  [INFO] {len(present)} V1 target agents accounted for")

    return present, missing


# ── Main Pipeline ─────────────────────────────────────────────────────────────

def _tag_items(items, repo_key):
    """Tag each item with source_repo, author, source_url, github_url."""
    cfg = SOURCE_REPOS[repo_key]
    raw_root = cfg["github_raw_root"]
    for name, info in items.items():
        info["source_repo"] = repo_key
        info["author"] = cfg["author"]
        info["source_url"] = cfg["github_url"]
        # Derive github_raw_url from file path
        fpath = info.get("agent_file") or info.get("path") or info.get("node") or ""
        if fpath:
            info["github_url"] = raw_root + fpath
        else:
            info["github_url"] = ""

def _merge_items(v1_items, v2_items):
    """Merge v1+v2, with v1 winning for duplicates."""
    merged = dict(v1_items)
    only_v2 = 0
    for name, info in v2_items.items():
        if name not in merged:
            merged[name] = info
            only_v2 += 1
    return merged, only_v2

def main():
    parser = argparse.ArgumentParser(description="Build AutoDev Studio manifests")
    parser.add_argument("--ref-main", default=REFERENCE_ROOT, help="Path to automotive-claude-code-agents-main")
    parser.add_argument("--ref-v2", default=REFERENCE_ROOT_V2, help="Path to automotive-claude-code-agents")
    parser.add_argument("--preinstall", default=None, help="Comma-separated preinstall agent names (default: V1 9 agents)")
    args = parser.parse_args()

    ref_main = args.ref_main
    ref_v2 = args.ref_v2
    preinstall_list = args.preinstall.split(",") if args.preinstall else PREINSTALL_AGENTS

    print("=" * 72)
    print("AutoDev Studio Manifest Compilation Pipeline")
    print("=" * 72)
    print(f"  Ref main: {ref_main}")
    print(f"  Ref v2:   {ref_v2}")
    print(f"  Output:   {OUTPUT_DIR}")
    print(f"  Preinstall: {len(preinstall_list)} agents")
    print()

    # Step 1: Collect agents
    print("[1/4] Collecting agents...")
    agents_v1 = collect_agents(ref_main)
    _tag_items(agents_v1, "automotive-claude-code-agents-main")
    print(f"  Repo 1 (Thejeswara Reddy R): {len(agents_v1)} agents")

    agents_v2 = collect_agents(ref_v2)
    _tag_items(agents_v2, "automotive-claude-code-agents")
    print(f"  Repo 2 (Yuxin ZHANG):        {len(agents_v2)} agents")

    agents, v2_only_a = _merge_items(agents_v1, agents_v2)
    print(f"  Merged: {len(agents)} agents ({v2_only_a} v2-only)")
    print()

    # Step 2: Collect skills
    print("[2/4] Collecting skills...")
    skills_v1 = collect_skills(ref_main)
    _tag_items(skills_v1, "automotive-claude-code-agents-main")
    print(f"  Repo 1: {len(skills_v1)} skills")

    skills_v2 = collect_skills(ref_v2)
    _tag_items(skills_v2, "automotive-claude-code-agents")
    print(f"  Repo 2: {len(skills_v2)} skills")

    skills, v2_only_s = _merge_items(skills_v1, skills_v2)
    print(f"  Merged: {len(skills)} skills ({v2_only_s} v2-only)")
    print()

    # Step 3: Collect workflows
    print("[3/4] Collecting workflows...")
    wf_v1 = collect_workflows(ref_main)
    _tag_items(wf_v1, "automotive-claude-code-agents-main")
    print(f"  Repo 1: {len(wf_v1)} workflows")

    wf_v2 = collect_workflows(ref_v2)
    _tag_items(wf_v2, "automotive-claude-code-agents")
    print(f"  Repo 2: {len(wf_v2)} workflows")

    workflows, v2_only_w = _merge_items(wf_v1, wf_v2)
    print(f"  Merged: {len(workflows)} workflows ({v2_only_w} v2-only)")
    print()

    # Build skill index + link capabilities
    print("[4/4] Building index + linking...")
    commands = collect_commands(ref_main)
    skill_index = {}
    for skill_name, skill_info in skills.items():
        skill_index[skill_name] = skill_info
    ensure_v1_targets(agents, ref_main)
    link_capabilities_to_skills(agents, skill_index)
    validate_v1_targets(agents)

    domains = build_domains(agents, skills, workflows)
    timestamp = datetime.now(timezone.utc).isoformat()
    print()

    # ══ Output 1: catalog.json (full metadata) ══
    catalog = {"version":"1.0.0","generated_at":timestamp,
               "agents":agents,"skill_index":skill_index,"domains":domains,
               "workflows":workflows,"commands":commands}
    cat_path = os.path.join(OUTPUT_DIR,"catalog.json")
    with open(cat_path,"w",encoding="utf-8") as f:
        json.dump(catalog,f,indent=2,ensure_ascii=False)
    print(f"  Wrote catalog.json ({os.path.getsize(cat_path):,} bytes)")

    # ══ Output 2: preinstall.json (slim) ══
    pre = {"agents":[],"skills":[],"workflows":[]}
    for aname in preinstall_list:
        agent = agents.get(aname)
        if not agent: continue
        pre["agents"].append(aname)
        for sk in (agent.get("required_skills") or []):
            sp = sk.get("path","") if isinstance(sk,dict) else str(sk)
            if sp and sp not in pre["skills"]: pre["skills"].append(sp)
        dom = agent.get("domain","")
        for wfn, wfi in workflows.items():
            if isinstance(wfi,dict) and wfi.get("domain","")==dom:
                wp = wfi.get("path","")
                if wp and wp not in pre["workflows"]: pre["workflows"].append(wp)
    pre_path = os.path.join(OUTPUT_DIR,"preinstall.json")
    with open(pre_path,"w",encoding="utf-8") as f:
        json.dump(pre,f,indent=2,ensure_ascii=False)
    print(f"  Wrote preinstall.json ({os.path.getsize(pre_path):,} bytes)")
    print(f"    - {len(pre['agents'])} agents, {len(pre['skills'])} skills, {len(pre['workflows'])} workflows")

    # ══ Output 3: ecosystem_graph.json ══
    graph = build_ecosystem_graph(agents, skill_index, workflows, commands)
    graph["version"] = "1.0.0"; graph["generated_at"] = timestamp
    graph_path = os.path.join(OUTPUT_DIR,"ecosystem_graph.json")
    with open(graph_path,"w",encoding="utf-8") as f:
        json.dump(graph,f,indent=2,ensure_ascii=False)
    print(f"\n  Wrote ecosystem_graph.json ({os.path.getsize(graph_path):,} bytes)")

    # Summary
    print()
    print("=" * 72)
    print("SUMMARY")
    print("=" * 72)
    print(f"  Agents:    {len(agents)}")
    print(f"  Skills:    {len(skills)}")
    print(f"  Workflows: {len(workflows)}")
    print(f"  Commands:  {len(commands)}")
    print(f"  Domains:   {len(domains)}")
    print(f"  Graph: {len(graph['elements']['nodes']):,} nodes, {len(graph['elements']['edges']):,} edges")
    print()

    # Domain breakdown (top 10)
    print("  Top domains:")
    top_doms = sorted(domains.items(), key=lambda x: -x[1]['agent_count'])[:10]
    for dn, di in top_doms:
        if di['agent_count'] > 0:
            print(f"    {dn:25s}  {di['agent_count']:3d} agents, {di['skill_count']:4d} skills, {di['workflow_count']:3d} wfs")

    # Preinstall agent stats
    print(f"\n  Preinstall agents ({len(preinstall_list)}):")
    for an in preinstall_list[:12]:
        a = agents.get(an, {})
        sk = len(a.get("required_skills", []))
        print(f"    {an}: {sk} skills" + (f" (author: {a.get('author','')[:20]})" if a else " [NOT FOUND]"))
    print()

    # Skill usage stats
    linked = sum(1 for s in skill_index.values() if s.get('used_by'))
    print(f"  Skills linked: {linked}/{len(skills)}")
    print()
    print("Done.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
