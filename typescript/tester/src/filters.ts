/**
 * IPP projekt Tester
 * Autor : Kristian Rucek (xrucekk00)
 * VUT FIT 2026
 */

// Apply user defined filters for testing

import { writeFileSync } from "fs";
import {
  TestReport,
  TestCaseDefinition,
  CategoryReport,
  UnexecutedReason,
  UnexecutedReasonCode,
} from "./models.js";
import { logger, CliArguments } from "./tester.js";

function printResult(resultReport: TestReport, outputFile: string | null): void {
  const resultJson = JSON.stringify(resultReport, null, 2);
  if (outputFile !== null) {
    writeFileSync(outputFile, resultJson, "utf8");
    return;
  }

  console.log(resultJson);
}

export function applyIncludeFilters(
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

export function applyExcludeFilters(
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

export function applyFilters(
  testCases: TestCaseDefinition[],
  args: CliArguments,
  unexecutedCases: Record<string, UnexecutedReason>
): void {
  applyIncludeFilters(testCases, args, unexecutedCases);
  applyExcludeFilters(testCases, args, unexecutedCases);
}

export function handleDryRun(
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
  printResult(report, args.output);
}
