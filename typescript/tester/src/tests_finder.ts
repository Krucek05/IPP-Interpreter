// finds all test files (.test, .in, .out) in a folder

import { promises as fs } from "node:fs";
import { join, extname, basename } from "node:path";
import { TestCaseDefinitionFile } from "./models.js";

interface TestFile {
  name: string;
  testPath: string;
  inPath?: string;
  outPath?: string;
}

// looks for all .test, .in, .out files and groups them together
export async function findTests(
  test_dir: string,
  recursive: boolean
): Promise<TestCaseDefinitionFile[]> {
  const tests = new Map<string, TestFile>();

  async function searchFolder(dir: string): Promise<void> {
    const files = await fs.readdir(dir, { withFileTypes: true });

    for (const file of files) {
      const path = join(dir, file.name);

      if (file.isDirectory() && recursive) {
        await searchFolder(path);
        continue;
      }

      if (!file.isFile()) continue;

      const fileExt = extname(file.name);
      if (![".test", ".in", ".out"].includes(fileExt)) continue;

      const fileName = basename(file.name, fileExt);

      let testInfo = tests.get(fileName);
      if (!testInfo) {
        testInfo = {
          name: fileName,
          testPath: "",
        };
        tests.set(fileName, testInfo);
      }
      if (fileExt === ".test") testInfo.testPath = path;
      else if (fileExt === ".in") testInfo.inPath = path;
      else if (fileExt === ".out") testInfo.outPath = path;
    }
  }

  await searchFolder(test_dir);

  return Array.from(tests.values())
    .filter((t) => t.testPath)
    .map(
      (t) =>
        new TestCaseDefinitionFile({
          name: t.name,
          test_source_path: t.testPath,
          stdin_file: t.inPath || null,
          expected_stdout_file: t.outPath || null,
        })
    );
}
