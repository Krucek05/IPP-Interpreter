#!/usr/bin/env php
<?php

declare(strict_types=1);

$repoRoot = dirname(__DIR__, 4);
require $repoRoot . '/php/tester/vendor/autoload.php';

use IPP\Tester\Model\CategoryReport;
use IPP\Tester\Model\TestCaseDefinition;
use IPP\Tester\Model\TestCaseReport;
use IPP\Tester\Model\TestCaseType;
use IPP\Tester\Model\TestReport;
use IPP\Tester\Model\TestResult;

$report = new TestReport(
    discoveredTestCases: [
        new TestCaseDefinition(
            name: 'combo',
            testSourcePath: '/tmp/tests/combo.test',
            testType: TestCaseType::COMBINED,
            category: 'integration',
            stdinFile: '/tmp/tests/combo.in',
            expectedStdoutFile: '/tmp/tests/combo.out',
            description: 'Combined happy path',
            points: 5,
            expectedParserExitCodes: [0],
            expectedInterpreterExitCodes: [0, 52],
        ),
    ],
    unexecuted: [],
    results: [
        'semantics' => new CategoryReport(
            totalPoints: 5,
            passedPoints: 2,
            testResults: [
                'sem_ok' => new TestCaseReport(
                    result: TestResult::PASSED,
                    parserExitCode: 0,
                    interpreterExitCode: 0,
                    parserStdout: '<xml/>',
                    parserStderr: '',
                    interpreterStdout: "OK\n",
                    interpreterStderr: '',
                    diffOutput: null,
                ),
                'sem_fail' => new TestCaseReport(
                    result: TestResult::INTERPRETER_RESULT_DIFFERS,
                    parserExitCode: 0,
                    interpreterExitCode: 0,
                    parserStdout: '<xml/>',
                    parserStderr: '',
                    interpreterStdout: 'A',
                    interpreterStderr: 'warn',
                    diffOutput: "--- expected\n+++ actual\n",
                ),
            ],
        ),
        'runtime' => new CategoryReport(
            totalPoints: 0,
            passedPoints: 0,
            testResults: [],
        ),
    ],
);

$json = json_encode($report->toArray(), JSON_PRETTY_PRINT);
if (!is_string($json)) {
    throw new RuntimeException('Failed to serialize JSON.');
}

echo $json . PHP_EOL;
