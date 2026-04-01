#!/usr/bin/env php
<?php

declare(strict_types=1);

use IPP\Interpreter\InputModel\Arg;
use IPP\Interpreter\InputModel\Assign;
use IPP\Interpreter\InputModel\Block;
use IPP\Interpreter\InputModel\ClassDef;
use IPP\Interpreter\InputModel\Expr;
use IPP\Interpreter\InputModel\Method;
use IPP\Interpreter\InputModel\Program;
use IPP\Interpreter\InputModel\Send;
use IPP\Interpreter\InputModel\Variable;

$repoRoot = dirname(__DIR__, 3);

spl_autoload_register(static function (string $class) use ($repoRoot): void {
    $prefix = 'IPP\\Interpreter\\';
    if (!str_starts_with($class, $prefix)) {
        return;
    }

    $relativeClass = substr($class, strlen($prefix));
    if ($relativeClass === false) {
        return;
    }

    $pathSuffix = str_replace('\\', '/', $relativeClass) . '.php';
    $path = $repoRoot . '/php/int/src/interpreter/' . $pathSuffix;

    if (is_file($path)) {
        require_once $path;
    }
});

/**
 * @return array<string, mixed>
 */
function normalizeVariable(Variable $variable): array
{
    return ['name' => $variable->name];
}

/**
 * @return array<string, mixed>
 */
function normalizeExpr(Expr $expr): array
{
    if ($expr->literal !== null) {
        return [
            'kind' => 'literal',
            'literal' => [
                'class_id' => $expr->literal->classId,
                'value' => $expr->literal->value,
            ],
        ];
    }

    if ($expr->variable !== null) {
        return ['kind' => 'var', 'var' => normalizeVariable($expr->variable)];
    }

    if ($expr->block !== null) {
        return ['kind' => 'block', 'block' => normalizeBlock($expr->block)];
    }

    if ($expr->send !== null) {
        return ['kind' => 'send', 'send' => normalizeSend($expr->send)];
    }

    throw new RuntimeException('Invalid Expr: missing payload');
}

/**
 * @return array<string, mixed>
 */
function normalizeSend(Send $send): array
{
    return [
        'selector' => $send->selector,
        'receiver' => normalizeExpr($send->receiver),
        'args' => array_map(
            static fn (Arg $arg): array => normalizeArg($arg),
            $send->args
        ),
    ];
}

/**
 * @return array<string, mixed>
 */
function normalizeArg(Arg $arg): array
{
    return [
        'order' => $arg->order,
        'expr' => normalizeExpr($arg->expr),
    ];
}

/**
 * @return array<string, mixed>
 */
function normalizeAssign(Assign $assign): array
{
    return [
        'order' => $assign->order,
        'target' => normalizeVariable($assign->target),
        'expr' => normalizeExpr($assign->expr),
    ];
}

/**
 * @return array<string, mixed>
 */
function normalizeBlock(Block $block): array
{
    return [
        'arity' => $block->arity,
        'parameters' => array_map(
            static fn ($parameter): array => ['name' => $parameter->name, 'order' => $parameter->order],
            $block->parameters
        ),
        'assigns' => array_map(
            static fn (Assign $assign): array => normalizeAssign($assign),
            $block->assigns
        ),
    ];
}

/**
 * @return array<string, mixed>
 */
function normalizeMethod(Method $method): array
{
    return [
        'selector' => $method->selector,
        'block' => normalizeBlock($method->block),
    ];
}

/**
 * @return array<string, mixed>
 */
function normalizeClass(ClassDef $classDef): array
{
    return [
        'name' => $classDef->name,
        'parent' => $classDef->parent,
        'methods' => array_map(
            static fn (Method $method): array => normalizeMethod($method),
            $classDef->methods
        ),
    ];
}

/**
 * @return array<string, mixed>
 */
function normalizeProgram(Program $program): array
{
    return [
        'language' => $program->language,
        'description' => $program->description,
        'classes' => array_map(
            static fn (ClassDef $classDef): array => normalizeClass($classDef),
            $program->classes
        ),
    ];
}

if ($argc !== 2) {
    fwrite(STDERR, "Usage: php_dump.php <xml-file>\n");
    exit(2);
}

$sourcePath = $argv[1];

try {
    $xmlDocument = new \DOMDocument();
    $previous = libxml_use_internal_errors(true);

    try {
        if ($xmlDocument->load($sourcePath) !== true) {
            throw new RuntimeException('Error parsing XML.');
        }
    } finally {
        libxml_clear_errors();
        libxml_use_internal_errors($previous);
    }

    $root = $xmlDocument->documentElement;
    if (!$root instanceof \DOMElement) {
        throw new RuntimeException('Missing XML root element.');
    }

    $program = Program::fromXml($root);
    $normalized = normalizeProgram($program);

    $json = json_encode($normalized, JSON_THROW_ON_ERROR);
    fwrite(STDOUT, $json . "\n");
    exit(0);
} catch (Throwable $error) {
    fwrite(STDERR, $error->getMessage() . "\n");
    exit(1);
}
