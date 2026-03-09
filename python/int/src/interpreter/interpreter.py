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

from interpreter.error_codes import ErrorCode
from interpreter.exceptions import InterpreterError
from interpreter.input_model import Program
from interpreter.integer_object import IntegerObject
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
        self.xml_tree: etree._ElementTree | None = None
        self.root: etree._Element | None = None

    def check_main(self) -> None:
        """Checks if class Main exists and if there is selector run"""
        assert self.root is not None

        if not self.root.xpath('//class[@name="Main"]'):
            raise InterpreterError(ErrorCode.SEM_MAIN, "Missing Main class")
        if not self.root.xpath('//class[@name="Main"]/method[@selector="run"]'):
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
            self.xml_tree = xml_tree
            self.root = self.xml_tree.getroot()
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

    def evaluate_node(self, node: etree._Element) -> SolObject:
        """Evaulating what contains current node"""
        if node.tag == "expr":
            return self.evaluate_node(node[0])  # find child

        if node.tag == "literal":
            node_class = node.get("class")
            node_value = node.get("value")
            if node_class is None:
                return SolObject("Nil", None)
            if node_class == "Integer":
                assert node_value is not None
                return IntegerObject(int(node_value))
            if node_class == "String":
                assert node_value is not None
                return StringObject(node_value)
            return SolObject(node_class, node_value)

        if node.tag == "send":
            return self.dispatching(node)

        if node.tag == "var":
            var_name = node.get("name")
            if var_name is None:
                return SolObject("Nil", None)
            return self.variables.get(var_name, SolObject("Nil", None))

        return SolObject("Nil", None)

    def dispatching(self, sender: etree._Element) -> SolObject:
        """Finds proper selector, calls evaluations of expression and executed choosen funcion"""
        selector = sender.get("selector")

        output_node = sender.find("expr")
        assert output_node is not None
        output = self.evaluate_node(output_node)

        if selector == "print":
            if not isinstance(output, StringObject):
                raise InterpreterError(ErrorCode.SEM_ARITY, "print can only be called on String")
            return output.sol_print()

        return output

    def execute(self, input_io: TextIO) -> None:
        """
        Executes the currently loaded program, using the provided input stream as standard input.
        """
        logger.info("Executing program")

        assert self.root is not None

        run_block = self.root.find('.//class[@name="Main"]/method[@selector="run"]/block')
        assert run_block is not None

        for assign in sorted(run_block.findall("assign"), key=lambda x: int(x.get("order", 0))):
            expr_node = assign.find("expr")
            assert expr_node is not None
            value = self.evaluate_node(expr_node)

            var_elem = assign.find("var")
            assert var_elem is not None
            var_name = var_elem.get("name")
            assert var_name is not None

            if var_name != "_":
                self.variables[var_name] = value
