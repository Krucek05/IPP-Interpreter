#!/usr/bin/env php
<?php

declare(strict_types=1);

$repoRoot = dirname(__DIR__, 4);
require $repoRoot . '/php/tester/vendor/autoload.php';

use IPP\Tester\Model\TestCaseDefinition;
use IPP\Tester\Model\TestCaseType;
use IPP\Tester\Model\TestReport;

$report = new TestReport(
    discoveredTestCases: [
        new TestCaseDefinition(
            name: 'combo_min',
            testSourcePath: '/tmp/tests/combo_min.test',
            testType: TestCaseType::COMBINED,
            category: 'integration',
            expectedInterpreterExitCodes: [0],
        ),
    ],
    unexecuted: [],
    results: null,
);

$json = json_encode($report->toArray(), JSON_PRETTY_PRINT);
if (!is_string($json)) {
    throw new RuntimeException('Failed to serialize JSON.');
}

echo $json . PHP_EOL;
