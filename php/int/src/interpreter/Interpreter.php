<?php

/**
 * This module contains the main logic of the interpreter.
 *
 * IPP: You must definitely modify this file. Bend it to your will.
 *
 * Author: Ondrej Ondryas <iondryas@fit.vut.cz>
 * Author:
 *
 * AI usage notice: The template author used OpenAI Codex to create the implementation of this
 *                  module based on its Python counterpart.
 */

declare(strict_types=1);

namespace IPP\Interpreter;

use DOMDocument;
use DOMElement;
use IPP\Interpreter\InputModel\Program;
use IPP\Interpreter\InputModel\XmlValidationException;
use IPP\Interpreter\Exception\InterpreterError;
use IPP\Interpreter\Exception\ErrorCode;
use Psr\Log\NullLogger;
use Psr\Log\LoggerInterface;
use SplFileObject;

/**
 * The main interpreter class, responsible for loading the source file and executing the program.
 */
class Interpreter
{
    private LoggerInterface $logger;
    private ?Program $currentProgram = null;

    public function __construct(?LoggerInterface $logger = null)
    {
        $this->logger = $logger ?? new NullLogger();
    }

    /**
     * Reads the source SOL-XML file and stores it as the target program for this interpreter.
     * If any program was previously loaded, it is replaced by the new one.
     *
     * IPP: If you wish to run static checks on the program before execution, this is a good
     *      place to call them from.
     */
    public function loadProgram(string $sourceFilePath): void
    {
        $this->logger->info('Opening source file: {source_file}', ['source_file' => $sourceFilePath]);

        $xmlDocument = new DOMDocument();
        $previous = libxml_use_internal_errors(true);

        try {
            if ($xmlDocument->load($sourceFilePath) !== true) {
                throw new InterpreterError(
                    ErrorCode::INT_XML,
                    'Error parsing input XML'
                );
            }
        } finally {
            libxml_clear_errors();
            libxml_use_internal_errors($previous);
        }

        $rootElement = $xmlDocument->documentElement;
        if (!$rootElement instanceof DOMElement) {
            throw new InterpreterError(ErrorCode::INT_STRUCTURE, 'Invalid SOL-XML structure');
        }

        try {
            $this->currentProgram = Program::fromXml($rootElement);
        } catch (XmlValidationException $e) {
            throw new InterpreterError(ErrorCode::INT_STRUCTURE, 'Invalid SOL-XML structure', $e);
        }
    }

    /**
     * Executes the currently loaded program, using the provided input stream as standard input.
     */
    public function execute(?SplFileObject $inputIo): void
    {
        if ($this->currentProgram === null) {
            throw new InterpreterError(ErrorCode::INT_OTHER, 'No program is loaded.');
        }

        $this->logger->info('Executing program');

        // Template placeholder: implement interpretation logic here.
    }
}
