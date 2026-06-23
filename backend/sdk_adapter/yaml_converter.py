import yaml
from typing import Dict, Any, List, Optional
from pathlib import Path


class YAMLConverter:
    """
    Converts automotive agent YAML definitions into the internal format
    used by AgentNode workflow_steps.

    Parses agent capabilities, workflows, guidelines, and tools from YAML
    and maps them to the workflow step structure expected by AgentRuntime.
    """

    def parse_agent_yaml(self, yaml_path: str) -> Optional[Dict[str, Any]]:
        """
        Parse an agent YAML file and return structured agent configuration.
        Returns None if the file doesn't exist or can't be parsed.
        """
        path = Path(yaml_path)
        if not path.exists():
            return None

        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        if not raw:
            return None

        return self._normalize_agent_config(raw, yaml_path)

    def parse_skill_yaml(self, yaml_path: str) -> Optional[Dict[str, Any]]:
        """
        Parse a skill YAML file and return structured skill configuration.
        """
        path = Path(yaml_path)
        if not path.exists():
            return None

        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        if not raw:
            return None

        return self._normalize_skill_config(raw)

    def _normalize_agent_config(self, raw: Dict[str, Any], source_path: str) -> Dict[str, Any]:
        """Convert raw YAML agent config to internal agent format."""
        return {
            "name": raw.get("name", Path(source_path).stem),
            "domain": raw.get("domain", ""),
            "version": raw.get("version", "0.1.0"),
            "description": raw.get("description", ""),
            "capabilities": raw.get("capabilities", []),
            "workflow": raw.get("workflow", {}),
            "guidelines": raw.get("guidelines", []),
            "tools": raw.get("tools", []),
            "source_file": source_path,
        }

    def _normalize_skill_config(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Convert raw YAML skill config to internal skill format."""
        return {
            "name": raw.get("name", ""),
            "domain": raw.get("domain", ""),
            "category": raw.get("category", ""),
            "version": raw.get("version", "0.1.0"),
            "description": raw.get("description", ""),
            "capabilities": raw.get("capabilities", []),
            "workflow": raw.get("workflow", {}),
            "guidelines": raw.get("guidelines", []),
            "tools": raw.get("tools", []),
        }

    def agent_config_to_workflow_steps(self, agent_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert a normalized agent config's workflow into AgentNode workflow_steps format.
        Falls back to generating a default workflow if the agent config has none.
        """
        workflow = agent_config.get("workflow", {})
        steps = workflow.get("steps", [])

        if not steps:
            # Generate default workflow steps based on capabilities
            steps = self._generate_default_workflow(agent_config)

        normalized = []
        for i, step in enumerate(steps):
            normalized.append({
                "name": step.get("name", f"Step {i + 1}"),
                "type": step.get("type", "automatic"),
                "description": step.get("description", ""),
                "confirmation": step.get("confirmation", False),
                "safety_impact": step.get("safety_impact", "low"),
                "deliverable": step.get("deliverable", f"step_{i + 1}_output.md"),
                "order": i,
                "config": step.get("config", {}),
            })

        return normalized

    def skill_config_to_workflow_steps(self, skill_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert a skill config's workflow into workflow_steps format.
        """
        workflow = skill_config.get("workflow", {})
        steps = workflow.get("steps", [])

        if not steps:
            steps = self._generate_default_skill_workflow(skill_config)

        normalized = []
        for i, step in enumerate(steps):
            normalized.append({
                "name": step.get("name", f"Skill Step {i + 1}"),
                "type": step.get("type", "automatic"),
                "description": step.get("description", ""),
                "confirmation": step.get("confirmation", False),
                "safety_impact": step.get("safety_impact", "low"),
                "deliverable": f"skill_output_{i + 1}.md",
                "order": i,
                "config": step.get("config", {}),
            })

        return normalized

    def merge_agent_and_skill_workflows(
        self,
        agent_config: Dict[str, Any],
        skill_configs: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Merge agent workflow with skill workflows to produce the final execution plan.
        Agent workflow steps come first, followed by skill-specific steps.
        """
        all_steps = self.agent_config_to_workflow_steps(agent_config)

        for skill_cfg in skill_configs:
            skill_steps = self.skill_config_to_workflow_steps(skill_cfg)
            for ss in skill_steps:
                ss["name"] = f"[{skill_cfg.get('name', 'skill')}] {ss['name']}"
            all_steps.extend(skill_steps)

        # Re-index order
        for i, step in enumerate(all_steps):
            step["order"] = i

        return all_steps

    def _generate_default_workflow(self, agent_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate a sensible default workflow for an agent based on its domain and capabilities.
        """
        domain = agent_config.get("domain", "")
        capabilities = agent_config.get("capabilities", [])
        agent_name = agent_config.get("name", "")

        steps = [
            {
                "name": "Analyze Input & Requirements",
                "type": "automatic",
                "description": f"Parse input files and extract requirements for {agent_name} in {domain} domain.",
                "confirmation": False,
                "deliverable": "01_requirements_analysis.md",
            },
        ]

        # Domain-specific middle steps
        if "adas" in domain.lower():
            steps.append({
                "name": "Sensor Configuration Analysis",
                "type": "automatic",
                "description": "Analyze sensor setup and compute perception pipeline parameters.",
                "confirmation": False,
                "deliverable": "02_sensor_config.md",
            })
            steps.append({
                "name": "Algorithm Design & Validation",
                "type": "automatic",
                "description": "Design detection/tracking algorithms and validate against requirements.",
                "confirmation": False,
                "deliverable": "03_algorithm_design.md",
            })
        elif "functional safety" in domain.lower() or "safety" in domain.lower():
            steps.append({
                "name": "Hazard Analysis & Risk Assessment",
                "type": "automatic",
                "description": "Perform HARA - identify hazards, assess risks, determine ASIL levels.",
                "confirmation": True,
                "safety_impact": "critical",
                "deliverable": "02_hara_report.md",
            })
            steps.append({
                "name": "Safety Goals Derivation",
                "type": "automatic",
                "description": "Derive safety goals from hazard analysis results.",
                "confirmation": False,
                "safety_impact": "high",
                "deliverable": "03_safety_goals.md",
            })
        elif "autosar" in domain.lower():
            steps.append({
                "name": "Software Component Architecture",
                "type": "automatic",
                "description": "Design AUTOSAR software component architecture and interfaces.",
                "confirmation": False,
                "deliverable": "02_swc_architecture.md",
            })
            steps.append({
                "name": "Runnable Entity Mapping",
                "type": "automatic",
                "description": "Map runnable entities to OS tasks and define scheduling.",
                "confirmation": False,
                "deliverable": "03_runnable_mapping.md",
            })
        elif "diagnostics" in domain.lower():
            steps.append({
                "name": "Diagnostic Trouble Code Definition",
                "type": "automatic",
                "description": "Define DTCs, diagnostic services, and monitoring strategies.",
                "confirmation": False,
                "deliverable": "02_dtc_definition.md",
            })
            steps.append({
                "name": "Diagnostic Sequence Design",
                "type": "automatic",
                "description": "Design diagnostic service sequences and session handling.",
                "confirmation": False,
                "deliverable": "03_diag_sequences.md",
            })
        elif "sotif" in domain.lower():
            steps.append({
                "name": "SOTIF Hazard Identification",
                "type": "automatic",
                "description": "Identify potential hazardous scenarios from functional insufficiencies.",
                "confirmation": False,
                "safety_impact": "medium",
                "deliverable": "02_sotif_hazards.md",
            })
            steps.append({
                "name": "SOTIF Validation Strategy",
                "type": "automatic",
                "description": "Define validation and verification strategy for SOTIF compliance.",
                "confirmation": True,
                "safety_impact": "high",
                "deliverable": "03_sotif_validation.md",
            })
        else:
            # Generic middle steps
            for cap in capabilities[:2]:
                steps.append({
                    "name": f"Generate {cap.replace('-', ' ').title()}",
                    "type": "automatic",
                    "description": f"Execute capability: {cap}",
                    "confirmation": False,
                    "deliverable": f"output_{cap.replace('-', '_')}.md",
                })

        # Final review step (always a checkpoint)
        steps.append({
            "name": "Final Review & Deliverable Assembly",
            "type": "checkpoint",
            "description": "Review all generated outputs and assemble final deliverables.",
            "confirmation": True,
            "safety_impact": "medium",
            "deliverable": "final_deliverables.md",
        })

        return steps

    def _generate_default_skill_workflow(self, skill_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate a default workflow for a skill."""
        return [
            {
                "name": f"Execute {skill_config.get('name', 'skill')}",
                "type": "automatic",
                "description": skill_config.get("description", ""),
                "confirmation": False,
            },
        ]
