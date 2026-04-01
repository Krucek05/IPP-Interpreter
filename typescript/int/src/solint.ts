#!/usr/bin/env node
/**
 * This script serves as the main entry point for the SOL26 interpreter.
 *
 * IPP: You should not need to modify this file (except for adding additional CLI arguments
 * or using async/await in main, if you want to).
 *
 * Author: Ondřej Ondryáš <iondryas@fit.vut.cz>
 *
 * AI usage notice: The author used OpenAI Codex to create the implementation of this
 *                  module based on its Python counterpart.
 */

import { readFileSync, statSync } from "node:fs";
import { basename } from "node:path";
import { Readable } from "node:stream";
import { parseArgs } from "node:util";

import { ErrorCode, fireError } from "./interpreter/error_codes.js";
import { InterpreterError } from "./interpreter/exceptions.js";
import { Interpreter } from "./interpreter/interpreter.js";
import { pino } from "pino";

const logger = pino({
  transport: {
    target: "pino-pretty",
    options: {
      colorize: true,
      destination: 2,
    },
  },
});

interface CliArguments {
  source: string;
  input: string | null;
  verbose: number;
}

class CliArgumentParsingError extends Error {
  public constructor(message: string) {
    super(message);
    this.name = "CliArgumentParsingError";
  }
}

function formatHelpText(progName: string): string {
  return [
    `usage: ${progName} [-h] -s SOURCE [-i INPUT] [-v]`,
    "",
    "options:",
    "  -h, --help            show this help message and exit",
    "  -s SOURCE, --source SOURCE",
    "                        Path to the SOL-XML source file to be interpreted.",
    "  -i INPUT, --input INPUT",
    "                        Path to a file that will be used as the standard input for the interpreted program (optional).",
    "  -v, --verbose         Enable verbose logging output (using once = INFO level, using twice = DEBUG level).",
    "",
  ].join("\n");
}

function parseArguments(argv: string[]): CliArguments {
  /**
   * Parses interpreter CLI arguments.
   */

  const parsedArguments = parseArgs({
    args: argv,
    options: {
      help: { type: "boolean", short: "h" },
      source: { type: "string", short: "s" },
      input: { type: "string", short: "i" },
      verbose: { type: "boolean", short: "v", multiple: true },
    },
    allowPositionals: false,
    strict: true,
  });

  if (parsedArguments.values.help) {
    process.stdout.write(formatHelpText(basename(process.argv[1] ?? "solint")));
    process.exit(0);
  }

  if (parsedArguments.values.source === undefined) {
    throw new CliArgumentParsingError("Missing required argument --source");
  }

  const verbose = parsedArguments.values.verbose?.length ?? 0;

  return {
    source: parsedArguments.values.source,
    input: parsedArguments.values.input ?? null,
    verbose,
  };
}

function parseArgumentsOrFire(argv: string[]): CliArguments {
  try {
    return parseArguments(argv);
  } catch {
    fireError(ErrorCode.GENERAL_OPTIONS);
  }
}

function isFile(path: string): boolean {
  try {
    return statSync(path).isFile();
  } catch {
    return false;
  }
}

function validateInputPaths(args: CliArguments): void {
  // Check that the provided paths are valid files (exist and are not directories)
  if (!isFile(args.source)) {
    fireError(ErrorCode.GENERAL_INPUT, "Source file does not exist or is not a file.");
  }

  if (args.input !== null && !isFile(args.input)) {
    fireError(ErrorCode.GENERAL_INPUT, "Input file does not exist or is not a file.");
  }
}

function configureVerboseLogging(verboseCount: number): void {
  // Enable debug or info logging if the verbose flag was set twice or once
  if (verboseCount >= 2) {
    logger.level = "debug";
    return;
  }

  if (verboseCount === 1) {
    logger.level = "info";
    return;
  }

  logger.level = "warn";
}

function createInputStream(inputPath: string | null): Readable {
  if (inputPath !== null) {
    // Execute the program using the provided input file as standard input
    const inputText = readFileSync(inputPath, "utf8");
    return Readable.from(inputText);
  }

  // Execute the program with an empty input stream if no input file was provided
  return Readable.from("");
}

function handleUnhandledError(error: unknown): void {
  if (error instanceof InterpreterError) {
    logger.debug(error);
    fireError(error.errorCode, error.message);
  }

  logger.error(error, "Unhandled exception during interpretation");
  fireError(ErrorCode.GENERAL_OTHER, error instanceof Error ? error.message : String(error));
}

function main(): void {
  /**
   * The main entry point for the SOL26 interpreter. It parses command-line arguments, and uses
   * the Interpreter class to load and execute the specified program in the SOL-XML format.
   *
   * IPP: Do not modify this function. 
   *      Exceptions: adding additional CLI arguments,
   *                  converting to use Promises (async/await) if necessary.
   */

  // Set up logging
  // IPP: You do not have to use logging - but it is the recommended practice.
  //      See https://getpino.io/#/docs/api for more information.
  const args = parseArgumentsOrFire(process.argv.slice(2));
  validateInputPaths(args);
  configureVerboseLogging(args.verbose);

  // Create an instance of the interpreter
  const interpreter = new Interpreter(logger);

  try {
    // Load the program from the source file
    interpreter.loadProgram(args.source);
    interpreter.execute(createInputStream(args.input));
  } catch (error) {
    handleUnhandledError(error);
  }
}

main();
