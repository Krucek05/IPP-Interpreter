#!/usr/bin/env php
<?php

declare(strict_types=1);

$repoRoot = dirname(__DIR__, 4);
require $repoRoot . '/php/tester/vendor/autoload.php';

use IPP\Tester\Model\CategoryReport;
use IPP\Tester\Model\TestCaseReport;
use IPP\Tester\Model\TestReport;
use IPP\Tester\Model\TestResult;

$report = new TestReport(
    results: [
        'runtime' => new CategoryReport(
            totalPoints: 1,
            passedPoints: 0,
            testResults: [
                'only_exit' => new TestCaseReport(
                    result: TestResult::UNEXPECTED_INTERPRETER_EXIT_CODE,
                    interpreterExitCode: 52,
                ),
            ],
        ),
    ],
);

$json = json_encode($report->toArray(), JSON_PRETTY_PRINT);
if (!is_string($json)) {
    throw new RuntimeException('Failed to serialize JSON.');
}

echo $json . PHP_EOL;
