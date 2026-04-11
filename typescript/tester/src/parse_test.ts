/**
 * IPP projekt Tester
 * Autor : Kristian Rucek (xrucekk00)
 * VUT FIT 2026
 */

// Parse .test file headers to get test metadata

import { promises as fs } from "node:fs";
import {
  TestCaseDefinitionFile,
  TestCaseDefinition,
  TestCaseType,
  UnexecutedReason,
  UnexecutedReasonCode,
} from "./models.js";

// what we extract from the .test file header
export interface metadata {
  category: string;
  description?: string | null;
  parserExitCodes?: number[] | null;
  interpreterExitCodes?: number[] | null;
  points?: number;
}

// build full test case from file + metadata
export function buildTestCase(
  file: TestCaseDefinitionFile,
  metadata: metadata
): TestCaseDefinition {
  const testType = findTestType(metadata.parserExitCodes, metadata.interpreterExitCodes);

  return new TestCaseDefinition({
    name: file.name,
    test_type: testType,
    description: metadata.description ?? null,
    category: metadata.category,
    points: metadata.points ?? 1,
    test_source_path: file.test_source_path,
    stdin_file: file.stdin_file,
    expected_stdout_file: file.expected_stdout_file,
    expected_parser_exit_codes: metadata.parserExitCodes ?? null,
    expected_interpreter_exit_codes: metadata.interpreterExitCodes ?? null,
  });
}

// read .test file and get the header metadata
export async function parseTestMetadata(
  testPath: string,
  unexecutedCases: Record<string, UnexecutedReason> = {},
  testCase: TestCaseDefinitionFile
): Promise<metadata> {
  const content = await fs.readFile(testPath, "utf-8");
  const lines = content.split("\n");

  const metadata: Partial<metadata> = {};

  // Parse header lines until we hit a blank line
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) break; // Stop at first blank line

    if (line.startsWith("+++")) {
      metadata.category = line.replace("+++", "").trim();
    } else if (line.startsWith("!C!")) {
      metadata.parserExitCodes = addExitCodes(metadata.parserExitCodes, parseNumbers(line));
    } else if (line.startsWith("!I!")) {
      metadata.interpreterExitCodes = addExitCodes(
        metadata.interpreterExitCodes,
        parseNumbers(line)
      );
    } else if (line.startsWith(">>>")) {
      metadata.points = parseInt(line.replace(">>>", "").trim());
    } else if (line.startsWith("***")) {
      metadata.description = line.replace("***", "").trim();
    }
  }

  if (!metadata.category) {
    unexecutedCases[testCase.name] = new UnexecutedReason(
      UnexecutedReasonCode.CANNOT_DETERMINE_TYPE,
      "Test case is missing category header"
    );
  }

  return metadata as metadata;
}

// parse comma-separated numbers from a line
function parseNumbers(line: string): number[] {
  return line
    .replace(/^!C!|^!I!/, "")
    .trim()
    .split(",")
    .map((n) => parseInt(n.trim()));
}

// Helper to add to arrays
function addExitCodes(current: number[] | null | undefined, newCodes: number[]): number[] {
  return current ? [...current, ...newCodes] : newCodes;
}

// figure out test type from what codes are set
function findTestType(
  parser: number[] | null | undefined,
  interpreter: number[] | null | undefined
): TestCaseType {
  const hasParser = parser && parser.length > 0;
  const hasInterpreter = interpreter && interpreter.length > 0;

  if (hasParser && !hasInterpreter) return TestCaseType.PARSE_ONLY;
  if (!hasParser && hasInterpreter) return TestCaseType.EXECUTE_ONLY;
  return TestCaseType.COMBINED;
}
