#!/usr/bin/env python3
"""
Read preinstall.json and copy agent/skill/workflow YAMLs from reference repos
to the local autodev-studio cache directories.

Usage:
  python3 scripts/sync_agents.py [--force]

Local cache structure:
  agents/<domain>/<name>.yaml
  skills/<category>/<name>.yaml
  workflows/<domain>/<name>.yaml
"""
import json, os, sys, shutil, argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
MANIFEST_DIR = os.path.join(PROJECT_ROOT, "manifest")
LOCAL_AGENTS = os.path.join(PROJECT_ROOT, "agents")
LOCAL_SKILLS = os.path.join(PROJECT_ROOT, "skills")
LOCAL_WORKFLOWS = os.path.join(PROJECT_ROOT, "workflows")

# Reference repo paths (can be overridden via env vars)
REF_MAIN = os.environ.get("AUTODEV_REF_MAIN",
    os.path.expanduser("~/Desktop/miniprogram/autoagent/参考项目/automotive-claude-code-agents-main"))
REF_V2 = os.environ.get("AUTODEV_REF_V2",
    os.path.expanduser("~/Desktop/miniprogram/autoagent/参考项目/automotive-claude-code-agents"))


def _copy_file(src_path: str, dst: str, force: bool) -> bool:
    """Copy src to dst. Returns True if copied."""
    if not os.path.isfile(src_path):
        return False
    if os.path.exists(dst) and not force:
        return False  # already exists, skip
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src_path, dst)
    return True


def main():
    parser = argparse.ArgumentParser(description="Sync preinstall agents from ref repos")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    preinstall_path = os.path.join(MANIFEST_DIR, "preinstall.json")
    if not os.path.isfile(preinstall_path):
        print(f"ERROR: preinstall.json not found at {preinstall_path}")
        print("Run 'python3 manifest/build_manifest.py' first to generate it.")
        sys.exit(1)

    with open(preinstall_path) as f:
        pre = json.load(f)

    print("=" * 60)
    print("  AutoDev Studio — Preinstall Agent/Skill/Workflow Sync")
    print("=" * 60)
    print(f"  Agents:    {len(pre.get('agents', []))}")
    print(f"  Skills:    {len(pre.get('skills', []))}")
    print(f"  Workflows: {len(pre.get('workflows', []))}")
    print()

    refs = ["ref_main", "ref_v2"]
    ref_paths = {"ref_main": REF_MAIN, "ref_v2": REF_V2}
    stats = {"agents": 0, "skills": 0, "workflows": 0}

    for ref_name in refs:
        ref_root = ref_paths[ref_name]
        if not os.path.isdir(ref_root):
            print(f"  [SKIP] Ref repo not found: {ref_root}")
            continue
        print(f"  Scanning: {ref_name} ({ref_root})")

        for agent_name in pre.get("agents", []):
            for domain_dir in os.listdir(os.path.join(ref_root, "agents")):
                domain_path = os.path.join(ref_root, "agents", domain_dir)
                if not os.path.isdir(domain_path):
                    continue
                for fname in os.listdir(domain_path):
                    if not fname.endswith(".yaml") and not fname.endswith(".md"):
                        continue
                    with open(os.path.join(domain_path, fname)) as fh:
                        content = fh.read()
                    import re
                    m = re.search(r'^name:\s*(.+)$', content, re.MULTILINE)
                    if m and m.group(1).strip().lower().replace(" ", "-") == agent_name:
                        src = os.path.join(domain_path, fname)
                        dst = os.path.join(LOCAL_AGENTS, domain_dir, fname)
                        if _copy_file(src, dst, args.force):
                            stats["agents"] += 1
                            print(f"    ✅ Agent: {agent_name} → agents/{domain_dir}/{fname}")

        for skill_path in pre.get("skills", []):
            src = os.path.join(ref_root, skill_path)
            if not os.path.isfile(src):
                continue
            # Map skills/<category>/.../<name>.yaml → local skills/<category>/.../<name>.yaml
            rel = skill_path.replace("skills/", "", 1)
            dst = os.path.join(LOCAL_SKILLS, rel)
            if _copy_file(src, dst, args.force):
                stats["skills"] += 1

        for wf_path in pre.get("workflows", []):
            src = os.path.join(ref_root, wf_path)
            if not os.path.isfile(src):
                continue
            rel = wf_path.replace("workflows/", "", 1)
            dst = os.path.join(LOCAL_WORKFLOWS, rel)
            if _copy_file(src, dst, args.force):
                stats["workflows"] += 1

    print()
    print(f"  Done. Copied: {stats['agents']} agents, {stats['skills']} skills, {stats['workflows']} workflows")

    # Show local cache stats
    ag_count = sum(1 for _,_,fs in os.walk(LOCAL_AGENTS) for f in fs if f.endswith(('.yaml','.md')))
    sk_count = sum(1 for _,_,fs in os.walk(LOCAL_SKILLS) for f in fs if f.endswith('.yaml'))
    wf_count = sum(1 for _,_,fs in os.walk(LOCAL_WORKFLOWS) for f in fs if f.endswith('.yaml'))
    print(f"  Local cache: {ag_count} agents, {sk_count} skills, {wf_count} workflows")
    print("Done.")


if __name__ == "__main__":
    main()
