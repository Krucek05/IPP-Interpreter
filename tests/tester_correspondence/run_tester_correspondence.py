#!/usr/bin/env python3
"""Run cross-language correspondence checks for tester output-model serialization."""

from __future__ import annotations

import argparse
import difflib
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CommandSpec:
    language: str
    command: list[str]


REPO_ROOT = Path(__file__).resolve().parents[2]
CASE_DIR = REPO_ROOT / "tests" / "tester_correspondence" / "cases"


def resolve_python_executable() -> str:
    configured = os.environ.get("TESTER_CORR_PYTHON")
    if configured:
        return configured

    venv_python = REPO_ROOT / "python" / "tester" / ".venv" / "bin" / "python"
    if venv_python.is_file():
        return str(venv_python)

    return "python3"


def command_specs_for_case(case_path: Path) -> list[CommandSpec]:
    return [
        CommandSpec(
            language="python",
            command=[resolve_python_executable(), str(case_path / "case.py")],
        ),
        CommandSpec(
            language="php",
            command=["php", str(case_path / "case.php")],
        ),
        CommandSpec(
            language="typescript",
            command=["node", str(case_path / "case.mjs")],
        ),
    ]


def ensure_typescript_build() -> None:
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=REPO_ROOT / "typescript" / "tester",
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            "TypeScript build failed:\n"
            f"{result.stdout.strip()}\n{result.stderr.strip()}".strip()
        )


def run_case_command(spec: CommandSpec) -> dict[str, Any]:
    result = subprocess.run(spec.command, capture_output=True, text=True, check=False)

    if result.returncode != 0:
        raise RuntimeError(
            f"{spec.language} case script failed with code {result.returncode}:\n"
            f"{result.stderr.strip()}"
        )

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"{spec.language} case script produced invalid JSON:\n{result.stdout.strip()}"
        ) from exc


def make_diff(left_name: str, left_obj: dict[str, Any], right_name: str, right_obj: dict[str, Any]) -> str:
    left_json = json.dumps(left_obj, indent=2, sort_keys=True)
    right_json = json.dumps(right_obj, indent=2, sort_keys=True)

    diff_lines = difflib.unified_diff(
        left_json.splitlines(),
        right_json.splitlines(),
        fromfile=left_name,
        tofile=right_name,
        lineterm="",
    )
    return "\n".join(diff_lines)


def collect_cases(selected_cases: list[str]) -> list[Path]:
    available = {
        case.name: case
        for case in sorted(CASE_DIR.iterdir())
        if case.is_dir()
    }

    if not available:
        raise RuntimeError(f"No case directories found in {CASE_DIR}")

    if not selected_cases:
        return list(available.values())

    missing = [name for name in selected_cases if name not in available]
    if missing:
        raise RuntimeError(
            "Unknown case names: "
            + ", ".join(missing)
            + f". Available: {', '.join(sorted(available))}"
        )

    return [available[name] for name in selected_cases]


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case",
        action="append",
        default=[],
        help="Specific case directory to run (can be used multiple times).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()

    try:
        ensure_typescript_build()
        cases = collect_cases(args.case)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    failures: list[str] = []

    for case_path in cases:
        print(f"[CASE] {case_path.name}")

        outputs: dict[str, dict[str, Any]] = {}
        for spec in command_specs_for_case(case_path):
            try:
                outputs[spec.language] = run_case_command(spec)
                print(f"  - {spec.language}: OK")
            except RuntimeError as exc:
                failures.append(f"{case_path.name}: {exc}")
                print(f"  - {spec.language}: FAIL")
                break

        if len(outputs) != 3:
            continue

        baseline = outputs["python"]
        for language in ("php", "typescript"):
            current = outputs[language]
            if current != baseline:
                diff = make_diff("python", baseline, language, current)
                failures.append(f"{case_path.name}: python != {language}\n{diff}")
                print(f"  - compare python vs {language}: DIFF")
            else:
                print(f"  - compare python vs {language}: match")

    if failures:
        print("\nCorrespondence check FAILED.")
        for failure in failures:
            print(f"\n---\n{failure}")
        return 1

    print("\nCorrespondence check passed for all cases.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
