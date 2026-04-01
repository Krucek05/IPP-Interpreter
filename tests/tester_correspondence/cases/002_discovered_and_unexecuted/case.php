#!/usr/bin/env php
<?php

declare(strict_types=1);

$repoRoot = dirname(__DIR__, 4);
require $repoRoot . '/php/tester/vendor/autoload.php';

use IPP\Tester\Model\TestCaseDefinition;
use IPP\Tester\Model\TestCaseType;
use IPP\Tester\Model\TestReport;
use IPP\Tester\Model\UnexecutedReason;
use IPP\Tester\Model\UnexecutedReasonCode;

$report = new TestReport(
    discoveredTestCases: [
        new TestCaseDefinition(
            name: 'alpha',
            testSourcePath: '/tmp/tests/alpha.test',
            testType: TestCaseType::PARSE_ONLY,
            category: 'syntax',
            expectedParserExitCodes: [21, 22],
        ),
        new TestCaseDefinition(
            name: 'beta',
            testSourcePath: '/tmp/tests/beta.test',
            testType: TestCaseType::EXECUTE_ONLY,
            category: 'runtime',
            stdinFile: '/tmp/tests/beta.in',
            expectedStdoutFile: '/tmp/tests/beta.out',
            description: 'execute-only sample',
            points: 3,
            expectedInterpreterExitCodes: [0],
        ),
    ],
    unexecuted: [
        'skip_filtered' => new UnexecutedReason(UnexecutedReasonCode::FILTERED_OUT),
        'skip_exec' => new UnexecutedReason(
            UnexecutedReasonCode::CANNOT_EXECUTE,
            'interpreter binary missing',
        ),
    ],
    results: null,
);

$json = json_encode($report->toArray(), JSON_PRETTY_PRINT);
if (!is_string($json)) {
    throw new RuntimeException('Failed to serialize JSON.');
}

echo $json . PHP_EOL;
