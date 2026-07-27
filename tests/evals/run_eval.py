#!/usr/bin/env python3
"""Skill prompt evaluation harness.

Each skill declares its own eval spec at skills/<name>/evals/eval_cases.json
(schema_version 2):

{
  "schema_version": 2,
  "trigger_keywords": ["audit", "hygiene"],
  "cases": [
    {
      "id": "tc_01",
      "query": "...",
      "expected_trigger": true,
      "mock_tools": ["get_ad_hygiene_flags"],
      "mock_response": "# Account Audit Report ...",
      "assertions": {
        "contains": [],
        "not_contains": [],
        "tools_called": []
      }
    }
  ]
}

Trigger detection and the simulated agent response are fully data-driven so
any skill can ship deterministic evals without touching this harness.
"""
import os
import sys
import json

NO_TRIGGER_RESPONSE = "I am sorry, but as an Ad agent, I do not know about that topic."


def load_skill_content(skills_dir, skill_name):
    skill_md_path = os.path.join(skills_dir, skill_name, "SKILL.md")
    if not os.path.exists(skill_md_path):
        return None
    with open(skill_md_path, "r", encoding="utf-8") as f:
        return f.read()


def load_eval_spec(eval_cases_path):
    """Loads and validates a v2 eval spec. Returns (spec, error_message)."""
    try:
        with open(eval_cases_path, "r", encoding="utf-8") as f:
            spec = json.load(f)
    except Exception as e:
        return None, f"Failed to parse eval_cases.json: {e}"

    if isinstance(spec, list):
        return None, (
            "Legacy list-format eval_cases.json detected. Migrate to schema_version 2 "
            "(object with trigger_keywords and cases)."
        )
    if spec.get("schema_version") != 2:
        return None, "eval_cases.json must declare \"schema_version\": 2."
    if not isinstance(spec.get("trigger_keywords"), list) or not spec["trigger_keywords"]:
        return None, "eval_cases.json must declare a non-empty \"trigger_keywords\" list."
    if not isinstance(spec.get("cases"), list):
        return None, "eval_cases.json must declare a \"cases\" list."
    return spec, None


def is_triggered(query, trigger_keywords):
    q = query.lower()
    return any(keyword.lower() in q for keyword in trigger_keywords)


def simulate_agent_response(case):
    """
    Simulates the agent's prompt execution and tool calls for a triggered case.
    Returns the case-declared mock response content and list of invoked tools.
    """
    return case.get("mock_response", ""), case.get("mock_tools", [])


def run_skill_eval(skills_dir, skill_name):
    print(f"\n--> Running evaluations for skill: {skill_name}")
    eval_cases_path = os.path.join(skills_dir, skill_name, "evals", "eval_cases.json")
    if not os.path.exists(eval_cases_path):
        print(f"    No eval_cases.json found. Skipping.")
        return True

    skill_content = load_skill_content(skills_dir, skill_name)
    if not skill_content:
        print(f"❌ Error: SKILL.md is missing for {skill_name}")
        return False

    spec, err = load_eval_spec(eval_cases_path)
    if err:
        print(f"❌ Error: {skill_name}: {err}")
        return False

    trigger_keywords = spec["trigger_keywords"]
    cases = spec["cases"]

    success = True
    passed_count = 0
    total_count = len(cases)

    for case in cases:
        case_id = case.get("id", "unknown")
        query = case.get("query", "")
        expected_trigger = case.get("expected_trigger", True)
        assertions = case.get("assertions", {})

        print(f"  [Case: {case_id}] Query: '{query}'")

        triggered = is_triggered(query, trigger_keywords)

        if triggered != expected_trigger:
            print(f"    ❌ Fail: Trigger status mismatch. Expected trigger: {expected_trigger}, got: {triggered}")
            success = False
            continue

        if not expected_trigger:
            print("    ✓ Pass: Correctly ignored.")
            passed_count += 1
            continue

        # Simulate LLM Response & Tool Calls
        response, tools = simulate_agent_response(case)

        # Check Assertions
        case_ok = True

        # 1. Contains check
        for match in assertions.get("contains", []):
            if match.lower() not in response.lower():
                print(f"    ❌ Fail: Expected substring '{match}' not found in output.")
                case_ok = False

        # 2. Not contains check
        for match in assertions.get("not_contains", []):
            if match.lower() in response.lower():
                print(f"    ❌ Fail: Forbidden substring '{match}' found in output.")
                case_ok = False

        # 3. Tools called check
        for expected_tool in assertions.get("tools_called", []):
            if expected_tool not in tools:
                print(f"    ❌ Fail: Expected tool '{expected_tool}' was not invoked.")
                case_ok = False

        if case_ok:
            print("    ✓ Pass: All assertions satisfied.")
            passed_count += 1
        else:
            success = False

    print(f"Scorecard for {skill_name}: {passed_count}/{total_count} passed.")
    return success


def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    skills_dir = os.path.join(repo_root, "skills")

    skill_filter = None
    args = sys.argv[1:]
    if "--skill" in args:
        idx = args.index("--skill")
        if idx + 1 >= len(args):
            print("❌ Error: --skill requires a skill name argument.")
            sys.exit(1)
        skill_filter = args[idx + 1]

    skills_to_eval = sorted(
        d for d in os.listdir(skills_dir)
        if os.path.isdir(os.path.join(skills_dir, d))
    )

    if skill_filter:
        if skill_filter not in skills_to_eval:
            print(f"❌ Error: Skill '{skill_filter}' not found in {skills_dir}")
            sys.exit(1)
        skills_to_eval = [skill_filter]

    print("=== Running Skill Prompt Evaluations ===")
    overall_ok = True
    for skill in skills_to_eval:
        if not run_skill_eval(skills_dir, skill):
            overall_ok = False

    if not overall_ok:
        print("\n❌ One or more skill evaluations failed!")
        sys.exit(1)

    print("\n✓ All skill prompt evaluations passed successfully!")
    sys.exit(0)


if __name__ == "__main__":
    main()
