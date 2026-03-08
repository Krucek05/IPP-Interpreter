"""
This module contains the main logic of the interpreter.

IPP: You must definitely modify this file. Bend it to your will.

Author: Ondřej Ondryáš <iondryas@fit.vut.cz>
Author:
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

logger = logging.getLogger(__name__)


class Interpreter:
    """
    The main interpreter class, responsible for loading the source file and executing the program.
    """

    def __init__(self) -> None:
        self.current_program: Program | None = None

    def check_main(self) -> None:
        """Checks if class Main exists and if there is selector run"""

        root = self.xml_tree.getroot()
        is_main = root.xpath('//class[@name="Main"]')

        if not is_main:
            raise InterpreterError(ErrorCode.SEM_MAIN, "Missing Main class")

        main_run = root.xpath('//class[@name="Main"]/method[@selector="run"]')
        if not main_run:
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

    def execute(self, input_io: TextIO) -> None:
        """
        Executes the currently loaded program, using the provided input stream as standard input.
        """
        logger.info("Executing program")

        # # Debug: print every XML node (tag, attributes, text)
        # if self.xml_tree is not None:
        #     for node in self.xml_tree.iter():
        #         print(f"TAG: {node.tag}  |  ATTRS: {dict(node.attrib)}  |  TEXT: {node.text!r}")

        # # Debug: print the parsed Pydantic model
        # if self.current_program is not None:
        #     print(self.current_program.model_dump())
