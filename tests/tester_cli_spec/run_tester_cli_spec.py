#!/usr/bin/env python3
"""CLI conformance checks for tester templates against ipp26.tex requirements."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

Expectation = Literal["help", "success_stdout_json", "success_output_json", "error"]


@dataclass(frozen=True)
class Variant:
    key: str
    command_prefix: list[str]


@dataclass(frozen=True)
class CliCase:
    name: str
    args_template: list[str]
    expectation: Expectation
    description: str


@dataclass(frozen=True)
class RunResult:
    variant: Variant
    return_code: int
    stdout: str
    stderr: str


REPO_ROOT = Path(__file__).resolve().parents[2]


def resolve_python_executable() -> str:
    configured = os.environ.get("TESTER_CLI_PYTHON")
    if configured:
        return configured

    venv_python = REPO_ROOT / "python" / "tester" / ".venv" / "bin" / "python"
    if venv_python.is_file():
        return str(venv_python)

    return "python3"


def variants() -> list[Variant]:
    return [
        Variant(
            key="python",
            command_prefix=[resolve_python_executable(), str(REPO_ROOT / "python" / "tester" / "src" / "tester.py")],
        ),
        Variant(
            key="typescript",
            command_prefix=["node", str(REPO_ROOT / "typescript" / "tester" / "dist" / "tester.js")],
        ),
        Variant(
            key="php",
            command_prefix=["php", str(REPO_ROOT / "php" / "tester" / "src" / "tester.php")],
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


CASES: list[CliCase] = [
    CliCase(
        name="help_short",
        args_template=["-h"],
        expectation="help",
        description="Short help switch should print help and exit.",
    ),
    CliCase(
        name="help_long",
        args_template=["--help"],
        expectation="help",
        description="Long help switch should print help and exit.",
    ),
    CliCase(
        name="missing_positional",
        args_template=[],
        expectation="error",
        description="tests_dir positional argument is required.",
    ),
    CliCase(
        name="too_many_positionals",
        args_template=["{tests_dir}", "{tests_dir}"],
        expectation="error",
        description="Exactly one positional tests_dir should be accepted.",
    ),
    CliCase(
        name="unknown_option",
        args_template=["--no-such-option", "{tests_dir}"],
        expectation="error",
        description="Unknown options must fail argument parsing.",
    ),
    CliCase(
        name="bad_tests_dir",
        args_template=["{missing_tests_dir}"],
        expectation="error",
        description="Non-existent tests directory should be rejected.",
    ),
    CliCase(
        name="bad_output_parent",
        args_template=["-o", "{bad_output_file}", "{tests_dir}"],
        expectation="error",
        description="Output path with missing parent directory should be rejected.",
    ),
    CliCase(
        name="minimal_ok",
        args_template=["{tests_dir}"],
        expectation="success_stdout_json",
        description="Minimal valid invocation should succeed and emit JSON report.",
    ),
    CliCase(
        name="recursive_ok",
        args_template=["--recursive", "{tests_dir}"],
        expectation="success_stdout_json",
        description="Recursive switch should be accepted.",
    ),
    CliCase(
        name="dry_run_ok",
        args_template=["--dry-run", "{tests_dir}"],
        expectation="success_stdout_json",
        description="Dry-run switch should be accepted.",
    ),
    CliCase(
        name="output_short_ok",
        args_template=["-o", "{output_file}", "{tests_dir}"],
        expectation="success_output_json",
        description="Short output switch should write JSON file.",
    ),
    CliCase(
        name="output_long_equals_ok",
        args_template=["--output={output_file}", "{tests_dir}"],
        expectation="success_output_json",
        description="Long output switch with '=' should write JSON file.",
    ),
    CliCase(
        name="filters_long_ok",
        args_template=[
            "--include=basic",
            "--exclude=slow",
            "--include-category=cat1",
            "--include-test=t1",
            "--exclude-category=cat2",
            "--exclude-test=t2",
            "{tests_dir}",
        ],
        expectation="success_stdout_json",
        description="All long filter options should be accepted.",
    ),
    CliCase(
        name="filters_short_ok",
        args_template=[
            "-i",
            "basic",
            "-e",
            "slow",
            "-ic",
            "cat1",
            "-it",
            "t1",
            "-ec",
            "cat2",
            "-et",
            "t2",
            "{tests_dir}",
        ],
        expectation="success_stdout_json",
        description="All short filter options should be accepted.",
    ),
    CliCase(
        name="repeated_filters_ok",
        args_template=[
            "-i",
            "one",
            "-i",
            "two",
            "-e",
            "x",
            "-e",
            "y",
            "{tests_dir}",
        ],
        expectation="success_stdout_json",
        description="Repeated include/exclude filters should be accepted.",
    ),
    CliCase(
        name="whitespace_filter_ok",
        args_template=["-i", "  basic  ", "-ec", "  catX  ", "{tests_dir}"],
        expectation="success_stdout_json",
        description="Filter values with surrounding whitespace should be accepted.",
    ),
    CliCase(
        name="verbose_repeated_ok",
        args_template=["-v", "-v", "{tests_dir}"],
        expectation="success_stdout_json",
        description="Repeated verbose flag should be accepted.",
    ),
]


def render_args(case: CliCase, variant: Variant, sandbox_dir: Path) -> tuple[list[str], Path]:
    tests_dir = sandbox_dir / "tests"
    output_dir = sandbox_dir / "out"
    output_dir.mkdir(parents=True, exist_ok=True)
    missing_parent = sandbox_dir / "missing-parent"

    context = {
        "tests_dir": str(tests_dir),
        "missing_tests_dir": str(sandbox_dir / "does-not-exist"),
        "output_file": str(output_dir / f"{case.name}-{variant.key}.json"),
        "bad_output_file": str(missing_parent / f"{case.name}-{variant.key}.json"),
    }

    rendered = [arg.format_map(context) for arg in case.args_template]
    return rendered, Path(context["output_file"])


def run_case(variant: Variant, case: CliCase, sandbox_dir: Path) -> tuple[RunResult, Path]:
    args, output_file = render_args(case, variant, sandbox_dir)
    cmd = [*variant.command_prefix, *args]

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return (
        RunResult(
            variant=variant,
            return_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        ),
        output_file,
    )


def validate_json_payload(raw_json: str) -> str | None:
    try:
        payload = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        return f"invalid JSON: {exc}"

    if not isinstance(payload, dict):
        return "JSON root is not an object"

    if "unexecuted" not in payload:
        return "JSON does not contain required key 'unexecuted'"

    return None


def validate_expectation(
    case: CliCase,
    result: RunResult,
    output_file: Path,
) -> list[str]:
    errors: list[str] = []

    if case.expectation == "help":
        if result.return_code != 0:
            errors.append(f"expected exit code 0 for help, got {result.return_code}")

        help_text = result.stdout.lower()
        if "usage" not in help_text:
            errors.append("help output does not contain usage text")

        return errors

    if case.expectation == "error":
        if result.return_code == 0:
            errors.append("expected non-zero exit code for invalid invocation")
        return errors

    if result.return_code != 0:
        errors.append(f"expected successful exit code 0, got {result.return_code}")
        return errors

    if case.expectation == "success_stdout_json":
        json_error = validate_json_payload(result.stdout)
        if json_error is not None:
            errors.append(f"stdout {json_error}")

        return errors

    if case.expectation == "success_output_json":
        if not output_file.is_file():
            errors.append(f"output file was not created: {output_file}")
            return errors

        try:
            output_text = output_file.read_text(encoding="utf-8")
        except OSError as exc:
            errors.append(f"cannot read output file: {exc}")
            return errors

        json_error = validate_json_payload(output_text)
        if json_error is not None:
            errors.append(f"output file {json_error}")

        return errors

    errors.append(f"unsupported expectation type: {case.expectation}")
    return errors


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--case",
        action="append",
        default=[],
        help="Run only selected case name(s).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()

    selected_cases = CASES
    if args.case:
        by_name = {case.name: case for case in CASES}
        missing = [name for name in args.case if name not in by_name]
        if missing:
            print(f"Unknown case names: {', '.join(missing)}", file=sys.stderr)
            return 2
        selected_cases = [by_name[name] for name in args.case]

    try:
        ensure_typescript_build()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    all_failures: list[str] = []

    with tempfile.TemporaryDirectory(prefix="tester-cli-spec-") as tmp_dir:
        sandbox_dir = Path(tmp_dir)
        (sandbox_dir / "tests").mkdir(parents=True, exist_ok=True)

        for case in selected_cases:
            print(f"[CASE] {case.name} - {case.description}")
            case_results: list[RunResult] = []

            for variant in variants():
                result, output_file = run_case(variant, case, sandbox_dir)
                case_results.append(result)

                validation_errors = validate_expectation(case, result, output_file)
                if validation_errors:
                    print(f"  - {variant.key}: FAIL")
                    for err in validation_errors:
                        all_failures.append(
                            f"{case.name}/{variant.key}: {err}\n"
                            f"stdout:\n{result.stdout.strip()}\n"
                            f"stderr:\n{result.stderr.strip()}"
                        )
                else:
                    print(f"  - {variant.key}: OK")

            return_codes = {res.variant.key: res.return_code for res in case_results}
            distinct_codes = set(return_codes.values())
            if len(distinct_codes) > 1:
                all_failures.append(
                    f"{case.name}: inconsistent exit codes across variants: {return_codes}"
                )
                print(f"  - consistency: DIFF exit codes {return_codes}")
            else:
                only_code = next(iter(distinct_codes))
                print(f"  - consistency: same exit code ({only_code})")

    if all_failures:
        print("\nCLI conformance FAILED.")
        for failure in all_failures:
            print(f"\n---\n{failure}")
        return 1

    print("\nCLI conformance passed for all selected cases.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
