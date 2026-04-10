// parse .test file headers to get test metadata

import { promises as fs } from "node:fs";
import { TestCaseDefinitionFile, TestCaseDefinition, TestCaseType } from "./models.js";

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
  const testType = determineTestType(metadata.parserExitCodes, metadata.interpreterExitCodes);

  return new TestCaseDefinition({
    name: file.name,
    test_source_path: file.test_source_path,
    stdin_file: file.stdin_file,
    expected_stdout_file: file.expected_stdout_file,
    test_type: testType,
    description: metadata.description ?? null,
    category: metadata.category,
    points: metadata.points ?? 1,
    expected_parser_exit_codes: metadata.parserExitCodes ?? null,
    expected_interpreter_exit_codes: metadata.interpreterExitCodes ?? null,
  });
}

// read .test file and get the header metadata
export async function parseTestMetadata(testPath: string): Promise<metadata> {
  const content = await fs.readFile(testPath, "utf-8");
  const lines = content.split("\n");

  const metadata: Partial<metadata> = {};

  // Parse header lines until we hit a blank line (marks end of metadata)
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed) break; // Stop at first blank line

    if (line.startsWith("+++")) {
      metadata.category = line.replace("+++", "").trim();
    } else if (line.startsWith("!C!")) {
      metadata.parserExitCodes = parseNumbers(line);
    } else if (line.startsWith("!I!")) {
      metadata.interpreterExitCodes = parseNumbers(line);
    } else if (line.startsWith(">>>")) {
      metadata.points = parseInt(line.replace(">>>", "").trim());
    } else if (line.startsWith("***")) {
      metadata.description = line.replace("***", "").trim();
    }
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

// figure out test type from what codes are set
function determineTestType(
  parser: number[] | null | undefined,
  interp: number[] | null | undefined
): TestCaseType {
  const hasParser = parser && parser.length > 0;
  const hasInterp = interp && interp.length > 0;

  if (hasParser && !hasInterp) return TestCaseType.PARSE_ONLY;
  if (!hasParser && hasInterp) return TestCaseType.EXECUTE_ONLY;
  return TestCaseType.COMBINED;
}
