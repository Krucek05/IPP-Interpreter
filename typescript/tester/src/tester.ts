#!/usr/bin/env node
/**
 * An integration testing script for the SOL26 interpreter.
 *
 * IPP: You can implement the entire tool in this file if you wish, but it is recommended to split
 *      the code into multiple files and modules as you see fit.
 *
 *      Below, you have some code to get you started with the CLI argument parsing and logging setup,
 *      but you are **free to modify it** in whatever way you like.
 *
 * Author: Ondřej Ondryáš <iondryas@fit.vut.cz>
 *
 * AI usage notice: The author used OpenAI Codex to create the implementation of this
 *                  module based on its Python counterpart.
 */

import { existsSync, lstatSync, writeFileSync, promises as fs } from "node:fs";
import { dirname, resolve } from "node:path";
import { parseArgs } from "node:util";

import { spawn } from "node:child_process";

import {
  TestReport,
  TestCaseDefinition,
  CategoryReport,
  TestCaseType,
  TestCaseReport,
  TestResult,
  UnexecutedReason,
  UnexecutedReasonCode,
} from "./models.js";
import { findTests } from "./tests_finder.js";
import { parseTestMetadata, buildTestCase } from "./parse_test.js";

import { pino } from "pino";

interface ProcessResult {
  stdout: string;
  stderr: string;
  exitCode: number;
}

interface TestExecutionOutcome {
  report: TestCaseReport;
  passed: boolean;
}

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function chunkToString(chunk: Buffer | string): string {
  return typeof chunk === "string" ? chunk : chunk.toString();
}

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
  tests_dir: string;
  recursive: boolean;
  output: string | null;
  dry_run: boolean;
  include: string[] | null;
  include_category: string[] | null;
  include_test: string[] | null;
  exclude: string[] | null;
  exclude_category: string[] | null;
  exclude_test: string[] | null;
  verbose: number;
  regex_filters: boolean;
}

function writeResult(resultReport: TestReport, outputFile: string | null): void {
  /**
   * Writes the final report to the specified output file or standard output if no file is provided.
   */
  const resultJson = JSON.stringify(resultReport, null, 2);
  if (outputFile !== null) {
    writeFileSync(outputFile, resultJson, "utf8");
    return;
  }

  console.log(resultJson);
}

const DOUBLE_LETTER_SHORT_OPTION_NORMALIZATION = new Map<string, string>([
  ["-ic", "--include-category"],
  ["-it", "--include-test"],
  ["-ec", "--exclude-category"],
  ["-et", "--exclude-test"],
]);

const HELP_TEXT = [
  "Usage:",
  "  tester [options] tests_dir",
  "",
  "Positional arguments:",
  "  tests_dir                 Path to a directory with the test cases in the SOLtest format.",
  "",
  "Options:",
  "  -h, --help                Show this help message and exit.",
  "  -r, --recursive           Recursively search for test cases in subdirectories of the provided directory.",
  "  -o, --output <path>       The output file to write the test results to. If not provided, results will be printed to standard output.",
  "  --dry-run                 Perform a dry run: discover the test cases but don't actually execute them.",
  "  -i, --include <value>     Include only test cases with the specified name or category. Can be used multiple times to specify multiple criteria.Can be combined with -ic and -it.",
  "  -ic, --include-category <value>",
  "                            Include only test cases with the specified category. Can be used multiple times to specify multiple accepted categories. Can be combined with -it and -i.",
  "  -it, --include-test <value>",
  "                            Include only test cases with the specified name. Can be used multiple times to specify multiple accepted names. Can be combined with -ic and -i.",
  "  -e, --exclude <value>     Exclude test cases with the specified name or category. Can be used multiple times to specify multiple criteria.Can be combined with -ic and -it.",
  "  -ec, --exclude-category <value>",
  "                            Exclude test cases with the specified category. Can be used multiple times to specify multiple accepted categories. Can be combined with -it and -i.",
  "  -et, --exclude-test <value>",
  "                            Exclude test cases with the specified name. Can be used multiple times to specify multiple accepted names. Can be combined with -ic and -i.",
  "  -g                        When used, the filters specified with -i[ct]/-e[ct] will be interpreted as regular expressions instead of literal strings.",
  "  -v, --verbose             Enable verbose logging output (using once = INFO level, using twice = DEBUG level).",
];

const PARSE_OPTIONS = {
  help: { type: "boolean", short: "h", default: false },
  recursive: { type: "boolean", short: "r", default: false },
  output: { type: "string", short: "o" },
  "dry-run": { type: "boolean", default: false },
  include: { type: "string", short: "i", multiple: true },
  "include-category": { type: "string", multiple: true },
  "include-test": { type: "string", multiple: true },
  exclude: { type: "string", short: "e", multiple: true },
  "exclude-category": { type: "string", multiple: true },
  "exclude-test": { type: "string", multiple: true },
  "regex-filters": { type: "boolean", short: "g", default: false },
  verbose: { type: "boolean", short: "v", multiple: true },
} as const;

function normalizeArgv(argv: string[]): string[] {
  return argv.map((arg) => DOUBLE_LETTER_SHORT_OPTION_NORMALIZATION.get(arg) ?? arg);
}

function printHelp(): void {
  console.log(HELP_TEXT.join("\n"));
}

function listOrNull(values: string[] | undefined): string[] | null {
  if (values === undefined || values.length === 0) {
    return null;
  }

  return values;
}

function parseCliArgumentsRaw(argv: string[]) {
  return parseArgs({
    args: normalizeArgv(argv),
    options: PARSE_OPTIONS,
    allowPositionals: true,
    strict: true,
  } as const);
}

function parseArguments(): CliArguments {
  /**
   * Parses the command-line arguments and performs basic validation a sanitization.
   */
  let parsed: ReturnType<typeof parseCliArgumentsRaw>;

  try {
    parsed = parseCliArgumentsRaw(process.argv.slice(2));
  } catch (error: unknown) {
    const message = error instanceof Error ? error.message : String(error);
    console.error(message);
    process.exit(2);
  }

  const parsedValues = parsed.values;

  if (parsedValues["help"]) {
    printHelp();
    process.exit(0);
  }

  if (parsed.positionals.length !== 1 || parsed.positionals[0] === undefined) {
    console.error("Exactly one positional argument (tests_dir) is required.");
    process.exit(2);
  }

  const args: CliArguments = {
    tests_dir: resolve(parsed.positionals[0]),
    recursive: parsedValues["recursive"],
    output: parsedValues["output"] ?? null,
    dry_run: parsedValues["dry-run"],
    include: listOrNull(parsedValues["include"]),
    include_category: listOrNull(parsedValues["include-category"]),
    include_test: listOrNull(parsedValues["include-test"]),
    exclude: listOrNull(parsedValues["exclude"]),
    exclude_category: listOrNull(parsedValues["exclude-category"]),
    exclude_test: listOrNull(parsedValues["exclude-test"]),
    verbose: parsedValues["verbose"]?.length ?? 0,
    regex_filters: parsedValues["regex-filters"],
  };

  // Check source directory
  if (!existsSync(args.tests_dir) || !lstatSync(args.tests_dir).isDirectory()) {
    console.error("The provided path is not a directory.");
    process.exit(1);
  }

  // Warn if the output file already exists
  if (args.output !== null) {
    const outputParent = dirname(args.output);
    if (!existsSync(outputParent)) {
      console.error("The parent directory of the output file does not exist.");
      process.exit(1);
    }

    if (existsSync(args.output)) {
      logger.warn("The output file will be overwritten: %s", args.output);
    }
  }

  return args;
}

async function runParser(inputFile: string): Promise<ProcessResult> {
  try {
    // Extract SOL code from .test file (skip metadata headers)
    const content = await fs.readFile(inputFile, "utf-8");
    const lines = content.split("\n");

    let codeStartIndex = 0;
    for (let i = 0; i < lines.length; i++) {
      if (lines[i]?.trim() === "") {
        codeStartIndex = i + 1;
        break;
      }
    }

    const solCode = lines.slice(codeStartIndex).join("\n");

    return await new Promise<ProcessResult>((resolve) => {
      let stdout = "";
      let stderr = "";

      const proc = spawn("python", ["/IPP_Projekt/sol2xml/sol_to_xml.py", "-"]);

      proc.stdout.on("data", (data: Buffer | string) => {
        stdout += chunkToString(data);
      });

      proc.stderr.on("data", (data: Buffer | string) => {
        stderr += chunkToString(data);
      });

      proc.on("error", (error: Error) => {
        resolve({
          stdout,
          stderr: error.message,
          exitCode: 1,
        });
      });

      proc.on("close", (exitCode) => {
        resolve({
          stdout,
          stderr,
          exitCode: exitCode ?? 1,
        });
      });

      proc.stdin.write(solCode);
      proc.stdin.end();
    });
  } catch (error: unknown) {
    return {
      stdout: "",
      stderr: getErrorMessage(error),
      exitCode: 1,
    };
  }
}

// Run interpreter with XML file path
async function runInterpreter(xmlContent: string, stdinFile?: string): Promise<ProcessResult> {
  try {
    // Write XML to temp file
    const tempXmlFile = `/tmp/soltest_${String(Date.now())}.xml`;
    await fs.writeFile(tempXmlFile, xmlContent, "utf-8");

    let stdinContent: string | null = null;
    if (stdinFile) {
      try {
        stdinContent = await fs.readFile(stdinFile, "utf-8");
      } catch {
        stdinContent = null;
      }
    }

    return await new Promise<ProcessResult>((resolve) => {
      const args = ["/IPP_Projekt/int/src/solint.py", "-s", tempXmlFile];
      if (stdinFile) {
        args.push("-i", stdinFile);
      }

      let stdout = "";
      let stderr = "";
      const proc = spawn("python", args);

      proc.stdout.on("data", (data: Buffer | string) => {
        stdout += chunkToString(data);
      });

      proc.stderr.on("data", (data: Buffer | string) => {
        stderr += chunkToString(data);
      });

      proc.on("error", (error: Error) => {
        void fs.unlink(tempXmlFile).catch(() => {});
        resolve({
          stdout,
          stderr: error.message,
          exitCode: 1,
        });
      });

      proc.on("close", (exitCode) => {
        // Clean up temp file
        void fs.unlink(tempXmlFile).catch(() => {});

        resolve({
          stdout,
          stderr,
          exitCode: exitCode ?? 1,
        });
      });

      if (stdinContent !== null) {
        proc.stdin.write(stdinContent);
      }
      proc.stdin.end();
    });
  } catch (error: unknown) {
    return {
      stdout: "",
      stderr: getErrorMessage(error),
      exitCode: 1,
    };
  }
}

// Compares expected file content with actual output. Used for output validation.
async function getDiff(expectedFile: string, actualOutput: string): Promise<string> {
  try {
    const expectedContent = await fs.readFile(expectedFile, "utf-8");
    if (expectedContent === actualOutput) {
      return "";
    }
    // Simple diff output
    return `Expected:\n${expectedContent}\n---\nActual:\n${actualOutput}`;
  } catch {
    return "Error generating diff";
  }
}

async function executeParseOnlyTest(testCase: TestCaseDefinition): Promise<TestExecutionOutcome> {
  // Run only sol2xml parser
  logger.debug("Running parser only");
  const { stdout, stderr, exitCode } = await runParser(testCase.test_source_path);
  logger.debug("Parser exited with code %d", exitCode);
  logger.debug("Parser stdout: %s", stdout);
  logger.debug("Parser stderr: %s", stderr);

  const parserPassed = testCase.expected_parser_exit_codes?.includes(exitCode) ?? false;
  logger.debug("Parser exit code check: %s", parserPassed);

  return {
    report: new TestCaseReport(
      parserPassed ? TestResult.PASSED : TestResult.UNEXPECTED_PARSER_EXIT_CODE,
      exitCode,
      null,
      stdout,
      stderr
    ),
    passed: parserPassed,
  };
}

async function executeRunThroughInterpreter(
  testCase: TestCaseDefinition,
  includeParserOutput: boolean
): Promise<TestExecutionOutcome> {
  const parserResult = await runParser(testCase.test_source_path);
  const parserPassed =
    testCase.expected_parser_exit_codes?.includes(parserResult.exitCode) ?? false;

  if (!parserPassed) {
    return {
      report: new TestCaseReport(
        TestResult.UNEXPECTED_PARSER_EXIT_CODE,
        parserResult.exitCode,
        null,
        includeParserOutput ? parserResult.stdout : null,
        includeParserOutput ? parserResult.stderr : null
      ),
      passed: false,
    };
  }

  const interpreterResult = await runInterpreter(
    parserResult.stdout,
    testCase.stdin_file ?? undefined
  );
  const report = includeParserOutput
    ? await validateInterpreterResult(testCase, interpreterResult, parserResult)
    : await validateInterpreterResult(testCase, interpreterResult);

  return {
    report,
    passed: report.result === TestResult.PASSED,
  };
}

async function executeTestCase(testCase: TestCaseDefinition): Promise<TestExecutionOutcome> {
  if (testCase.test_type === TestCaseType.PARSE_ONLY) {
    return executeParseOnlyTest(testCase);
  }

  if (testCase.test_type === TestCaseType.EXECUTE_ONLY) {
    return executeRunThroughInterpreter(testCase, false);
  }

  return executeRunThroughInterpreter(testCase, true);
}

// Validates interpreter execution and compares output with expected file
async function validateInterpreterResult(
  testCase: TestCaseDefinition,
  interpreterResult: { stdout: string; stderr: string; exitCode: number },
  parserResult?: { stdout: string; stderr: string; exitCode: number }
): Promise<TestCaseReport> {
  const interpreterPassed =
    testCase.expected_interpreter_exit_codes?.includes(interpreterResult.exitCode) ?? false;

  let diffOutput: string | null = null;
  let testPassed = interpreterPassed;

  if (interpreterPassed && testCase.expected_stdout_file) {
    const expectedOutputContent = await fs.readFile(testCase.expected_stdout_file, "utf-8");
    if (interpreterResult.stdout !== expectedOutputContent) {
      diffOutput = await getDiff(testCase.expected_stdout_file, interpreterResult.stdout);
      testPassed = false;
    }
  }

  return new TestCaseReport(
    testPassed
      ? TestResult.PASSED
      : diffOutput
        ? TestResult.INTERPRETER_RESULT_DIFFERS
        : TestResult.UNEXPECTED_INTERPRETER_EXIT_CODE,
    parserResult?.exitCode ?? null,
    interpreterResult.exitCode,
    parserResult?.stdout ?? null,
    parserResult?.stderr ?? null,
    interpreterResult.stdout,
    interpreterResult.stderr,
    diffOutput
  );
}

async function runTests(
  _testCases: TestCaseDefinition[],
  unexecutedCases: Record<string, UnexecutedReason> = {}
): Promise<Record<string, CategoryReport>> {
  const categoryData: Record<
    string,
    {
      total_points: number;
      passed_points: number;
      test_results: Record<string, TestCaseReport>;
    }
  > = {};

  for (const testCase of _testCases) {
    // Skip tests that are marked as unexecuted (filtered out, etc.)
    if (unexecutedCases[testCase.name]) {
      logger.debug("Skipping test case '%s' (already marked unexecuted)", testCase.name);
      continue;
    }

    logger.debug("Executing test case: %s", testCase.name);

    let category = categoryData[testCase.category];
    if (category === undefined) {
      category = {
        total_points: 0,
        passed_points: 0,
        test_results: {},
      };
      categoryData[testCase.category] = category;
    }

    category.total_points += testCase.points;

    const outcome = await executeTestCase(testCase);
    category.test_results[testCase.name] = outcome.report;
    if (outcome.passed) {
      category.passed_points += testCase.points;
    }
    if (outcome.report.result === TestResult.UNEXPECTED_PARSER_EXIT_CODE) {
      unexecutedCases[testCase.name] = new UnexecutedReason(
        UnexecutedReasonCode.MALFORMED_TEST_CASE_FILE,
        "Test case failed parser validation"
      );
    }
    if (outcome.report.result === TestResult.UNEXPECTED_INTERPRETER_EXIT_CODE) {
      unexecutedCases[testCase.name] = new UnexecutedReason(
        UnexecutedReasonCode.CANNOT_EXECUTE,
        "Test case failed interpreter validation"
      );
    }
  }

  const results: Record<string, CategoryReport> = {};
  for (const [categoryName, catData] of Object.entries(categoryData)) {
    results[categoryName] = new CategoryReport(
      catData.total_points,
      catData.passed_points,
      catData.test_results
    );
  }

  return results;
}

function applyIncludeFilters(
  testCases: TestCaseDefinition[],
  args: CliArguments,
  unexecutedCases: Record<string, UnexecutedReason>
): void {
  if (args.include || args.include_category || args.include_test) {
    for (const testCase of testCases) {
      if (
        (args.include &&
          !args.include.includes(testCase.name) &&
          !args.include.includes(testCase.category)) ||
        (args.include_category && !args.include_category.includes(testCase.category)) ||
        (args.include_test && !args.include_test.includes(testCase.name))
      ) {
        logger.debug("Exclude test case '%s' due to include filters", testCase.name);
        unexecutedCases[testCase.name] = new UnexecutedReason(
          UnexecutedReasonCode.FILTERED_OUT,
          "Test case excluded by include filters"
        );
      }
    }
  }
}

function applyExcludeFilters(
  testCases: TestCaseDefinition[],
  args: CliArguments,
  unexecutedCases: Record<string, UnexecutedReason>
): void {
  if (args.exclude || args.exclude_category || args.exclude_test) {
    for (const testCase of testCases) {
      if (
        (args.exclude && args.exclude.includes(testCase.name)) ||
        (args.exclude_category && args.exclude_category.includes(testCase.category)) ||
        (args.exclude_test && args.exclude_test.includes(testCase.name))
      ) {
        logger.debug("Excluding test case '%s' due to exclude filters", testCase.name);
        unexecutedCases[testCase.name] = new UnexecutedReason(
          UnexecutedReasonCode.FILTERED_OUT,
          "Test case excluded by exclude filters"
        );
      }
    }
  }
}

function applyFilters(
  testCases: TestCaseDefinition[],
  args: CliArguments,
  unexecutedCases: Record<string, UnexecutedReason>
): void {
  applyIncludeFilters(testCases, args, unexecutedCases);
  applyExcludeFilters(testCases, args, unexecutedCases);
}

function handleDryRun(
  testCases: TestCaseDefinition[],
  unexecutedCases: Record<string, UnexecutedReason>,
  args: CliArguments
): void {
  logger.info("Dry run enabled, skipping test execution.");
  const emptyResults: Record<string, CategoryReport> = {};
  const report = new TestReport({
    discovered_test_cases: testCases,
    unexecuted: unexecutedCases,
    results: emptyResults,
  });
  writeResult(report, args.output);
}

async function main(): Promise<void> {
  /**
   * The main entry point for the SOL26 integration testing script.
   * It parses command-line arguments and executes the testing process.
   */

  // Set up logging
  // IPP: You do not have to use logging - but it is the recommended practice.
  //      See https://getpino.io/#/docs/api for more information.
  logger.level = "warn";

  // Parse the CLI arguments
  const args = parseArguments();

  // Enable debug or info logging if the verbose flag was set twice or once
  if (args.verbose >= 2) {
    logger.level = "debug";
  } else if (args.verbose === 1) {
    logger.level = "info";
  }
  const discoveredTests = await findTests(args.tests_dir, args.recursive);
  logger.info(`Found ${String(discoveredTests.length)} test files`);

  // parse each test file and build test cases
  const testCases: TestCaseDefinition[] = [];
  const unexecutedCases: Record<string, UnexecutedReason> = {};
  for (const file of discoveredTests) {
    const meta = await parseTestMetadata(file.test_source_path, unexecutedCases, file);
    const testCase = buildTestCase(file, meta);
    testCases.push(testCase);
  }

  const foundTestCases = testCases;

  logger.info(`Parsed ${String(testCases.length)} test cases`);

  applyFilters(testCases, args, unexecutedCases);

  if (args.dry_run) {
    handleDryRun(testCases, unexecutedCases, args);
    return;
  }

  // Execute tests and get results
  const testResults = await runTests(testCases, unexecutedCases);

  const report = new TestReport({
    discovered_test_cases: foundTestCases,
    unexecuted: unexecutedCases,
    results: testResults,
  });
  writeResult(report, args.output);
}

void main();
