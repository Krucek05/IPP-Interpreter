/**
 * IPP projekt Tester
 * Autor : Kristian Rucek (xrucekk00)
 * VUT FIT 2026
 */

// Run interpreter or sol_to_xml parser

import { spawn } from "child_process";
import { promises as fs } from "fs";

export interface ProcessResult {
  stdout: string;
  stderr: string;
  exitCode: number;
}

function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function streamToString(data: Buffer | string): string {
  return typeof data === "string" ? data : data.toString();
}

export async function runParser(inputFile: string): Promise<ProcessResult> {
  try {
    // Extract SOL code from .test file (skip metadata headers)
    const fileContent = await fs.readFile(inputFile, "utf-8");
    const lines = fileContent.split("\n");

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
        stdout += streamToString(data);
      });

      proc.stderr.on("data", (data: Buffer | string) => {
        stderr += streamToString(data);
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
export async function runInterpreter(
  xmlfileContent: string,
  stdinFile?: string
): Promise<ProcessResult> {
  try {
    // Write XML to temp file
    const tempXmlFile = `/tmp/soltest_${String(Date.now())}.xml`;
    await fs.writeFile(tempXmlFile, xmlfileContent, "utf-8");

    let stdinfileContent: string | null = null;
    if (stdinFile) {
      try {
        stdinfileContent = await fs.readFile(stdinFile, "utf-8");
      } catch {
        stdinfileContent = null;
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
        stdout += streamToString(data);
      });

      proc.stderr.on("data", (data: Buffer | string) => {
        stderr += streamToString(data);
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

      if (stdinfileContent !== null) {
        proc.stdin.write(stdinfileContent);
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
