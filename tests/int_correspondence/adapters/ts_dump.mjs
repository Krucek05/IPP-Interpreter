#!/usr/bin/env node

import { readFileSync } from "node:fs";

import { parseProgramXml } from "../../../typescript/int/dist/interpreter/input_model.js";

function normalizeExpr(expr) {
  if (expr.literal !== null) {
    return {
      kind: "literal",
      literal: {
        class_id: expr.literal.class_id,
        value: expr.literal.value,
      },
    };
  }

  if (expr.var !== null) {
    return {
      kind: "var",
      var: { name: expr.var.name },
    };
  }

  if (expr.block !== null) {
    return {
      kind: "block",
      block: normalizeBlock(expr.block),
    };
  }

  if (expr.send !== null) {
    return {
      kind: "send",
      send: normalizeSend(expr.send),
    };
  }

  throw new Error("Invalid Expr: missing payload");
}

function normalizeArg(arg) {
  return {
    order: arg.order,
    expr: normalizeExpr(arg.expr),
  };
}

function normalizeSend(send) {
  return {
    selector: send.selector,
    receiver: normalizeExpr(send.receiver),
    args: send.args.map((arg) => normalizeArg(arg)),
  };
}

function normalizeAssign(assign) {
  return {
    order: assign.order,
    target: { name: assign.target.name },
    expr: normalizeExpr(assign.expr),
  };
}

function normalizeBlock(block) {
  return {
    arity: block.arity,
    parameters: block.parameters.map((parameter) => ({
      name: parameter.name,
      order: parameter.order,
    })),
    assigns: block.assigns.map((assign) => normalizeAssign(assign)),
  };
}

function normalizeMethod(method) {
  return {
    selector: method.selector,
    block: normalizeBlock(method.block),
  };
}

function normalizeClass(classDef) {
  return {
    name: classDef.name,
    parent: classDef.parent,
    methods: classDef.methods.map((method) => normalizeMethod(method)),
  };
}

function normalizeProgram(program) {
  return {
    language: program.language,
    description: program.description,
    classes: program.classes.map((classDef) => normalizeClass(classDef)),
  };
}

function main() {
  if (process.argv.length !== 3) {
    process.stderr.write("Usage: ts_dump.mjs <xml-file>\n");
    process.exit(2);
  }

  const sourcePath = process.argv[2];

  try {
    const xml = readFileSync(sourcePath, "utf8");
    const program = parseProgramXml(xml);
    process.stdout.write(`${JSON.stringify(normalizeProgram(program))}\n`);
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    process.stderr.write(`${message}\n`);
    process.exit(1);
  }
}

main();
