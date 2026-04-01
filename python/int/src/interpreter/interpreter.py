"""
This module contains the main logic of the interpreter.

IPP: You must definitely modify this file. Bend it to your will.

Author: Ondřej Ondryáš <iondryas@fit.vut.cz>
Author: Kristian Rucek xrucekk00
"""

import logging
from pathlib import Path
from typing import TextIO

from lxml import etree
from lxml.etree import ParseError
from pydantic import ValidationError

from interpreter.block_object import BlockObject
from interpreter.boolean_object import FALSE, TRUE
from interpreter.error_codes import ErrorCode
from interpreter.exceptions import InterpreterError
from interpreter.input_model import Expr, Program, Send
from interpreter.integer_object import IntegerObject
from interpreter.nil_object import NilObject
from interpreter.object import SolObject
from interpreter.string_object import StringObject

logger = logging.getLogger(__name__)


class Interpreter:
    """
    The main interpreter class, responsible for loading the source file and executing the program.
    """

    def __init__(self) -> None:
        self.current_program: Program | None = None
        self.variables: dict[str, SolObject] = {}

    def check_main(self) -> None:
        """Checks if class Main exists and has a run method"""
        assert self.current_program is not None

        main_class = next((c for c in self.current_program.classes if c.name == "Main"), None)
        if main_class is None:
            raise InterpreterError(ErrorCode.SEM_MAIN, "Missing Main class")
        if not any(m.selector == "run" for m in main_class.methods):
            raise InterpreterError(ErrorCode.SEM_MAIN, "Main missing run method")

    def load_program(self, source_file_path: Path) -> None:
        """
        Reads the source SOL-XML file and stores it as the target program for this interpreter.
        If any program was previously loaded, it is replaced by the new one.

        IPP: If you wish to run static checks on the program before execution, this is a good place
             to call them from.
        """

        logger.info("Opening source file: %s", source_file_path)
        try:
            xml_tree = etree.parse(source_file_path)
        except ParseError as e:
            raise InterpreterError(
                error_code=ErrorCode.INT_XML, message="Error parsing input XML"
            ) from e
        try:
            self.current_program = Program.from_xml_tree(xml_tree.getroot())  # type: ignore
        except ValidationError as e:
            raise InterpreterError(
                error_code=ErrorCode.INT_STRUCTURE, message="Invalid SOL-XML structure"
            ) from e

        self.check_main()

    def evaluate_expr(self, expr: Expr) -> SolObject:
        """Evaluates a Expr into a SolObject"""
        if expr.literal is not None:
            lit = expr.literal
            if lit.class_id == "Integer":
                return IntegerObject(int(lit.value))
            if lit.class_id == "String":
                return StringObject(lit.value)
            if lit.class_id == "Nil":
                return NIL
            if lit.class_id == "True":
                return TRUE
            if lit.class_id == "False":
                return FALSE
            # class literal — e.g. <literal class="class" value="Integer"/>
            return SolObject("class", lit.value)

        if expr.block is not None:
            return BlockObject(expr.block)

        if expr.var is not None:
            var_name = expr.var.name
            if var_name in self.variables:
                return self.variables[var_name]
            return NilObject()

        if expr.send is not None:
            return self.dispatch(expr.send)

        return NilObject()

    def dispatch(self, send: Send) -> SolObject:
        """Dispatches a message send to the appropriate handler"""
        receiver = self.evaluate_expr(send.receiver)
        selector = send.selector

        if receiver.class_name == "class":
            if selector == "new":
                return receiver.sol_new()
            if selector == "from:":
                obj = self.evaluate_expr(send.args[0].expr)
                return receiver.sol_from(obj)

        # if receiver.class_name == "Block" and selector == "whileTrue:":
        #     block = self.evaluate_expr(send.args[0].expr)
        #     return receiver.while_true(block)

        if selector == "print":
            if not isinstance(receiver, StringObject):
                raise InterpreterError(ErrorCode.SEM_ARITY, "print can only be called on String")
            return receiver.sol_print()

        if selector == "asString":
            return receiver.as_string()

        if selector == "asInteger":
            return receiver.as_integer()

        if selector == "identicalTo":
            first_arg = send.args[0].expr
            other = self.evaluate_expr(first_arg)
            return SolObject("Boolean", receiver.identical_to(other))

        if selector == "equalTo":
            first_arg = send.args[0].expr
            other = self.evaluate_expr(first_arg)
            return SolObject("Boolean", receiver.equal_to(other))

        return receiver

    def execute(self, input_io: TextIO) -> None:
        """
        Executes the currently loaded program, using the provided input stream as standard input.
        """
        logger.info("Executing program")
        assert self.current_program is not None

        main_class = next(c for c in self.current_program.classes if c.name == "Main")
        run_method = next(m for m in main_class.methods if m.selector == "run")

        for assign in run_method.block.assigns:
            value = self.evaluate_expr(assign.expr)
            if assign.target.name != "_":
                self.variables[assign.target.name] = value

        # print(self.current_program)
        logger.info("Program execution finished")
