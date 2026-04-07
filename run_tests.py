#!/usr/bin/env python3
"""
Simple test runner for SOL26 interpreter tests.
Parses .test files and runs them against the interpreter.
This test is AI generated for own purposes
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class TestCase:
    name: str
    description: Optional[str]
    category: Optional[str]
    weight: int
    compiler_code: Optional[int]
    interpreter_code: Optional[int]
    source_code: str
    stdin_file: Optional[Path]
    expected_stdout: Optional[str]


def parse_test_file(test_path: Path) -> Optional[TestCase]:
    """Parse a .test file and return TestCase object."""
    with open(test_path, "r") as f:
        content = f.read()
    
    lines = content.split("\n")
    test_name = test_path.stem
    description = None
    category = None
    weight = 1
    compiler_code = None
    interpreter_code = None
    source_code_lines = []
    in_source = False
    
    for line in lines:
        if line.startswith("***"):
            description = line[3:].strip()
        elif line.startswith("+++"):
            category = line[3:].strip()
        elif line.startswith("!C!"):
            try:
                compiler_code = int(line[3:].strip())
            except ValueError:
                pass
        elif line.startswith("!I!"):
            try:
                interpreter_code = int(line[3:].strip())
            except ValueError:
                pass
        elif line.startswith(">>>"):
            try:
                weight = int(line[3:].strip())
            except ValueError:
                pass
        elif line.strip() == "" and not in_source:
            in_source = True
        elif in_source:
            source_code_lines.append(line)
    
    source_code = "\n".join(source_code_lines).strip()
    
    # Check for .in file
    stdin_file = None
    in_path = test_path.with_suffix(".in")
    if in_path.exists():
        stdin_file = in_path
    
    # Check for .out file
    expected_stdout = None
    out_path = test_path.with_suffix(".out")
    if out_path.exists():
        with open(out_path, "r") as f:
            expected_stdout = f.read()
    
    return TestCase(
        name=test_name,
        description=description,
        category=category,
        weight=weight,
        compiler_code=compiler_code,
        interpreter_code=interpreter_code,
        source_code=source_code,
        stdin_file=stdin_file,
        expected_stdout=expected_stdout,
    )


def run_test(test: TestCase, interpreter_path: str) -> dict:
    """Run a single test and return result."""
    import tempfile
    
    result = {
        "name": test.name,
        "description": test.description,
        "category": test.category,
        "weight": test.weight,
        "status": "PASS",
        "error": None,
        "output": None,
    }
    
    try:
        # Check if source is SOL code (contains "class") or XML
        if test.source_code.strip().startswith("<"):
            # It's XML already
            with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
                f.write(test.source_code)
                temp_xml = f.name
        else:
            # It's SOL source - need to convert to XML first
            import subprocess as conv_subprocess
            with tempfile.NamedTemporaryFile(mode="w", suffix=".sol", delete=False) as f:
                f.write(test.source_code)
                temp_sol = f.name
            
            # Run sol_to_xml converter (writes XML to stdout)
            conv_result = conv_subprocess.run(
                [sys.executable, "sol2xml/sol_to_xml.py", temp_sol],
                capture_output=True,
                text=True,
                timeout=5,
                cwd="/home/ubuntu/IPP",
            )
            
            if conv_result.returncode != 0:
                result["status"] = "ERROR"
                result["error"] = f"SOL compilation failed: {conv_result.stderr[:100]}"
                if os.path.exists(temp_sol):
                    os.unlink(temp_sol)
                return result
            
            # Save XML output to a temp file
            with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
                f.write(conv_result.stdout)
                temp_xml = f.name
            
            os.unlink(temp_sol)
        
        try:
            # Run interpreter only if we have valid XML
            cmd = [sys.executable, interpreter_path, "-s", temp_xml]
            
            stdin_data = None
            if test.stdin_file and test.stdin_file.exists():
                with open(test.stdin_file, "r") as f:
                    stdin_data = f.read()
            
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                input=stdin_data,
                timeout=5,
            )
            
            # Check return code (always check this if specified)
            if test.interpreter_code is not None:
                if proc.returncode != test.interpreter_code:
                    result["status"] = "FAIL"
                    result["error"] = f"Expected exit code {test.interpreter_code}, got {proc.returncode}"
                    result["output"] = f"stdout: {repr(proc.stdout)}\nstderr: {repr(proc.stderr)}"
                    return result
            
            # Check output only if status is still PASS
            if test.expected_stdout is not None:
                if proc.stdout != test.expected_stdout:
                    result["status"] = "FAIL"
                    result["error"] = f"Output mismatch"
                    result["output"] = f"Expected:\n{repr(test.expected_stdout)}\n\nGot:\n{repr(proc.stdout)}"
                    return result
            
            result["output"] = proc.stdout if proc.stdout else "(no output)"
        finally:
            if os.path.exists(temp_xml):
                os.unlink(temp_xml)
    
    except subprocess.TimeoutExpired:
        result["status"] = "TIMEOUT"
        result["error"] = "Test timed out (5s)"
    except Exception as e:
        result["status"] = "ERROR"
        result["error"] = str(e)
    
    return result


def main():
    test_dir = Path("tests")
    interpreter_path = "python/int/src/solint.py"
    
    if not test_dir.exists():
        print(f"❌ Test directory not found: {test_dir}")
        sys.exit(1)
    
    if not Path(interpreter_path).exists():
        print(f"❌ Interpreter not found: {interpreter_path}")
        sys.exit(1)
    
    # Find all test files
    test_files = sorted(test_dir.rglob("*.test"))
    print(f"📋 Found {len(test_files)} test files\n")
    
    results = []
    passed = 0
    failed = 0
    errors = 0
    
    by_category = {}
    
    for test_file in test_files:
        test = parse_test_file(test_file)
        if test is None:
            continue
        
        result = run_test(test, interpreter_path)
        results.append(result)
        
        # Track by category
        cat = result["category"] or "uncategorized"
        if cat not in by_category:
            by_category[cat] = {"passed": 0, "failed": 0, "errors": 0}
        
        if result["status"] == "PASS":
            passed += 1
            by_category[cat]["passed"] += 1
            print(f"✅ {result['name']:40s} [{result['category'] or 'N/A'}]")
        elif result["status"] == "ERROR" or result["status"] == "TIMEOUT":
            errors += 1
            by_category[cat]["errors"] += 1
            print(f"⚠️  {result['name']:40s} [{result['category'] or 'N/A'}] - {result['error']}")
        else:
            failed += 1
            by_category[cat]["failed"] += 1
            print(f"❌ {result['name']:40s} [{result['category'] or 'N/A'}]")
            if result["error"]:
                print(f"   {result['error']}")
    
    print(f"\n{'='*70}")
    print(f"SUMMARY: {passed} passed, {failed} failed, {errors} errors (total: {len(results)})")
    print(f"{'='*70}\n")
    
    print("By category:")
    for cat in sorted(by_category.keys()):
        stats = by_category[cat]
        total = stats["passed"] + stats["failed"] + stats["errors"]
        print(f"  {cat:20s}: {stats['passed']:2d} passed, {stats['failed']:2d} failed, {stats['errors']:2d} errors (total: {total})")
    
    # Save detailed report
    report_path = Path("test_report.json")
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n📄 Detailed report saved to: {report_path}")


if __name__ == "__main__":
    main()
