#!/usr/bin/env python3
"""Dump a normalized SOL-XML Program model parsed by the Python template."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from lxml import etree

REPO_ROOT = Path(__file__).resolve().parents[3]
PYTHON_SRC = REPO_ROOT / "python" / "int" / "src"
if str(PYTHON_SRC) not in sys.path:
    sys.path.insert(0, str(PYTHON_SRC))

from interpreter.input_model import (  # noqa: E402
    Arg,
    Assign,
    Block,
    ClassDef,
    Expr,
    Method,
    Program,
    Send,
)


def normalize_expr(expr: Expr) -> dict[str, Any]:
    if expr.literal is not None:
        return {
            "kind": "literal",
            "literal": {
                "class_id": expr.literal.class_id,
                "value": expr.literal.value,
            },
        }

    if expr.var is not None:
        return {"kind": "var", "var": {"name": expr.var.name}}

    if expr.block is not None:
        return {"kind": "block", "block": normalize_block(expr.block)}

    if expr.send is not None:
        return {"kind": "send", "send": normalize_send(expr.send)}

    raise ValueError("Invalid Expr: missing payload")


def normalize_send(send: Send) -> dict[str, Any]:
    return {
        "selector": send.selector,
        "receiver": normalize_expr(send.receiver),
        "args": [normalize_arg(arg) for arg in send.args],
    }


def normalize_arg(arg: Arg) -> dict[str, Any]:
    return {"order": arg.order, "expr": normalize_expr(arg.expr)}


def normalize_assign(assign: Assign) -> dict[str, Any]:
    return {
        "order": assign.order,
        "target": {"name": assign.target.name},
        "expr": normalize_expr(assign.expr),
    }


def normalize_block(block: Block) -> dict[str, Any]:
    return {
        "arity": block.arity,
        "parameters": [
            {"name": parameter.name, "order": parameter.order}
            for parameter in block.parameters
        ],
        "assigns": [normalize_assign(assign) for assign in block.assigns],
    }


def normalize_method(method: Method) -> dict[str, Any]:
    return {"selector": method.selector, "block": normalize_block(method.block)}


def normalize_class(class_def: ClassDef) -> dict[str, Any]:
    return {
        "name": class_def.name,
        "parent": class_def.parent,
        "methods": [normalize_method(method) for method in class_def.methods],
    }


def normalize_program(program: Program) -> dict[str, Any]:
    return {
        "language": program.language,
        "description": program.description,
        "classes": [normalize_class(class_def) for class_def in program.classes],
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python_dump.py <xml-file>", file=sys.stderr)
        return 2

    xml_file = Path(sys.argv[1])

    try:
        xml_tree = etree.parse(xml_file)
        program = Program.from_xml_tree(xml_tree.getroot())  # type: ignore[arg-type]
    except Exception as exc:  # noqa: BLE001
        print(str(exc), file=sys.stderr)
        return 1

    print(
        json.dumps(
            normalize_program(program),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
