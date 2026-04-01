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
            name: 'parse_min',
            testSourcePath: '/tmp/tests/parse_min.test',
            testType: TestCaseType::PARSE_ONLY,
            category: 'syntax',
            expectedParserExitCodes: [0],
        ),
    ],
    unexecuted: [
        'skip_other' => new UnexecutedReason(UnexecutedReasonCode::OTHER),
    ],
);

$json = json_encode($report->toArray(), JSON_PRETTY_PRINT);
if (!is_string($json)) {
    throw new RuntimeException('Failed to serialize JSON.');
}

echo $json . PHP_EOL;
