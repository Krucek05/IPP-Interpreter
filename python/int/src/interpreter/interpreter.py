"""
This module contains the main logic of the interpreter.

IPP: You must definitely modify this file. Bend it to your will.

Author: Ondřej Ondryáš <iondryas@fit.vut.cz>
Author: Kristian Rucek xrucekk00
"""

import logging
from collections.abc import Callable
from pathlib import Path
from typing import TextIO

from lxml import etree
from lxml.etree import ParseError
from pydantic import ValidationError

from interpreter.block_object import BlockObject
from interpreter.boolean_object import BooleanObject, false, true
from interpreter.error_codes import ErrorCode
from interpreter.exceptions import InterpreterError
from interpreter.input_model import Program
from interpreter.integer_object import IntegerObject
from interpreter.nil_object import nil
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
                return nil
            if node_class == "Integer":
                assert node_value is not None
                return IntegerObject(int(node_value))
            if node_class == "String":
                assert node_value is not None
                return StringObject(node_value)
            if node_class == "Nil":
                return nil
            if node_class == "True":
                return true
            if node_class == "False":
                return false
            if node_class == "class":
                assert node_value is not None
                return StringObject(node_value)  # Return the class name as a string for now

        if node.tag == "block":
            # Parse XML block element back to pydantic Block model
            from interpreter.input_model import Block

            block_model = Block.from_xml_tree(node)  # type: ignore[arg-type]
            block_obj = BlockObject(block_model)
            block_obj.interpreter = self
            return block_obj

        if node.tag == "send":
            return self.dispatching(node)

        if node.tag == "var":
            var_name = node.get("name")
            if var_name is None:
                return nil
            return self.variables.get(var_name, nil)

        return nil

    def dispatching(self, sender: etree._Element) -> SolObject:
        """Dispatches message to appropriate handler based on selector"""
        selector = sender.get("selector")

        output_node = sender.find("expr")
        assert output_node is not None
        output = self.evaluate_node(output_node)

        # Handle block value selectors (value, value:, value:value:, etc.)
        if selector is not None and selector.startswith("value"):
            if isinstance(output, BlockObject):
                arity = selector.count(":")
                args: list[SolObject] = []
                for i in range(1, arity + 1):
                    arg_node = sender.find(f'arg[@order="{i}"]/expr')
                    if arg_node is not None:
                        args.append(self.evaluate_node(arg_node))

                output.interpreter = self

                return output.sol_value(*args)
            raise InterpreterError(ErrorCode.INT_DNU, f"{selector} only for Block")

        handlers: dict[str, Callable[[SolObject, etree._Element], SolObject]] = {
            "print": self._handle_print,
            "asString": self._handle_as_string,
            "asInteger": self._handle_as_integer,
            "identicalTo": self._handle_identical_to,
            "equalTo": self._handle_equal_to,
            "isNumber": lambda o, _: o.is_number(),
            "isBlock": lambda o, _: o.is_block(),
            "isNil": lambda o, _: o.is_nil(),
            "isBoolean": lambda o, _: o.is_boolean(),
            "greaterThan:": self._handle_greater_than,
            "plus:": self._handle_plus,
            "minus:": self._handle_minus,
            "multiplyBy:": self._handle_multiply_by,
            "divBy:": self._handle_div_by,
            "timesRepeat:": self._handle_times_repeat,
            "read": lambda o, _: StringObject.read(),
            "concatenateWith": self._handle_concat_with,
            "startsWith:endsBefore:": self._handle_starts_with_ends_before,
            "whileTrue:": self._handle_while_true,
            "not": self._handle_not,
            "and": self._handle_and,
            "or": self._handle_or,
            "ifTrue:ifFalse": self._handle_if_true_if_false,
            "new": lambda o, _: o.sol_new(),
            "from:": self._handle_from,
        }

        if selector in handlers:
            return handlers[selector](output, sender)

        return output

    def _handle_print(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for print selector"""
        if not isinstance(output, StringObject):
            raise InterpreterError(ErrorCode.SEM_ARITY, "print can only be called on String")
        return output.sol_print()

    def _handle_as_string(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for asString selector"""
        return output.as_string()

    def _handle_as_integer(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for asInteger selector"""
        if not isinstance(output, IntegerObject):
            raise InterpreterError(ErrorCode.INT_DNU, "asInteger: only for Integer")
        return output

    def _handle_identical_to(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for identicalTo selector"""
        arg_node = sender.find('arg[@order="1"]/expr')
        assert arg_node is not None
        other = self.evaluate_node(arg_node)
        return true if output.identical_to(other) else false

    def _handle_equal_to(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for equalTo selector"""
        arg_node = sender.find('arg[@order="1"]/expr')
        assert arg_node is not None
        other = self.evaluate_node(arg_node)
        return true if output.equal_to(other) else false

    def _handle_greater_than(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for greaterThan: selector"""
        if not isinstance(output, IntegerObject):
            raise InterpreterError(ErrorCode.INT_DNU, "greaterThan: only for Integer")
        arg_node = sender.find('arg[@order="1"]/expr')
        assert arg_node is not None
        other = self.evaluate_node(arg_node)
        return output.greater_than(other)

    def _handle_plus(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for plus: selector"""
        if not isinstance(output, IntegerObject):
            raise InterpreterError(ErrorCode.INT_DNU, "plus: only for Integer")
        arg_node = sender.find('arg[@order="1"]/expr')
        assert arg_node is not None
        other = self.evaluate_node(arg_node)
        return output.plus(other)

    def _handle_minus(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for minus: selector"""
        if not isinstance(output, IntegerObject):
            raise InterpreterError(ErrorCode.INT_DNU, "minus: only for Integer")
        arg_node = sender.find('arg[@order="1"]/expr')
        assert arg_node is not None
        other = self.evaluate_node(arg_node)
        return output.minus(other)

    def _handle_multiply_by(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for multiplyBy: selector"""
        if not isinstance(output, IntegerObject):
            raise InterpreterError(ErrorCode.INT_DNU, "multiplyBy: only for Integer")
        arg_node = sender.find('arg[@order="1"]/expr')
        assert arg_node is not None
        other = self.evaluate_node(arg_node)
        return output.multiply_by(other)

    def _handle_div_by(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for divBy: selector"""
        if not isinstance(output, IntegerObject):
            raise InterpreterError(ErrorCode.INT_DNU, "divBy: only for Integer")
        arg_node = sender.find('arg[@order="1"]/expr')
        assert arg_node is not None
        other = self.evaluate_node(arg_node)
        return output.divide_by(other)

    def _handle_times_repeat(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for timesRepeat: selector"""
        if not isinstance(output, IntegerObject):
            raise InterpreterError(ErrorCode.INT_DNU, "timesRepeat: only for Integer")
        arg_node = sender.find('arg[@order="1"]/expr')
        assert arg_node is not None
        block = self.evaluate_node(arg_node)

        if not isinstance(block, BlockObject):
            raise InterpreterError(ErrorCode.INT_DNU, "timesRepeat: requires a block")

        result: SolObject = nil
        if output.value > 0:
            for i in range(1, output.value + 1):
                iteration = IntegerObject(i)
                result = block.sol_value(iteration)

        return result

    def _handle_concat_with(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for concatenateWith selector"""
        if not isinstance(output, StringObject):
            raise InterpreterError(ErrorCode.INT_DNU, "concatenateWith not called with String")
        arg_node = sender.find('arg[@order="1"]/expr')
        assert arg_node is not None
        other = self.evaluate_node(arg_node)
        return output.concatenate_with(other)

    def _handle_starts_with_ends_before(
        self, output: SolObject, sender: etree._Element
    ) -> SolObject:
        """Handler for startsWith:endsBefore: selector"""
        if not isinstance(output, StringObject):
            raise InterpreterError(
                ErrorCode.INT_DNU, "startsWith:endsBefore: not called with String"
            )
        arg_node1 = sender.find('arg[@order="1"]/expr')
        assert arg_node1 is not None
        start = self.evaluate_node(arg_node1)
        arg_node2 = sender.find('arg[@order="2"]/expr')
        assert arg_node2 is not None
        end = self.evaluate_node(arg_node2)

        if not isinstance(start, IntegerObject) or not isinstance(end, IntegerObject):
            return nil

        return output.starts_with_ends_before(start, end)

    def _handle_while_true(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for whileTrue: selector"""
        if not isinstance(output, BlockObject):
            raise InterpreterError(ErrorCode.INT_DNU, "whileTrue: not called with Block")
        arg_node = sender.find('arg[@order="1"]/expr')
        assert arg_node is not None
        block = self.evaluate_node(arg_node)

        if not isinstance(block, BlockObject):
            raise InterpreterError(ErrorCode.INT_DNU, "whileTrue: requires a block")

        return output.while_true(block)

    def _handle_not(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for not selector"""
        if not isinstance(output, BooleanObject):
            raise InterpreterError(ErrorCode.INT_DNU, "not: can only be called on Boolean")
        return output.sol_not()

    def _handle_and(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for and selector"""
        if not isinstance(output, BooleanObject):
            raise InterpreterError(ErrorCode.INT_DNU, "and: not called with Boolean")
        arg_node = sender.find('arg[@order="1"]/expr')
        assert arg_node is not None
        block = self.evaluate_node(arg_node)

        if not isinstance(block, BlockObject):
            raise InterpreterError(ErrorCode.INT_DNU, "and: requires a block")

        return output.sol_and(block)

    def _handle_or(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for or selector"""
        if not isinstance(output, BooleanObject):
            raise InterpreterError(ErrorCode.INT_DNU, "or: not called with Boolean")
        arg_node = sender.find('arg[@order="1"]/expr')
        assert arg_node is not None
        block = self.evaluate_node(arg_node)

        if not isinstance(block, BlockObject):
            raise InterpreterError(ErrorCode.INT_DNU, "or: requires a block")

        return output.sol_or(block)

    def _handle_if_true_if_false(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for ifTrue:ifFalse selector"""
        if not isinstance(output, BooleanObject):
            raise InterpreterError(
                ErrorCode.INT_DNU, "ifTrue:ifFalse: can only be called on Boolean"
            )

        arg_node1 = sender.find('arg[@order="1"]/expr')
        assert arg_node1 is not None
        true_block = self.evaluate_node(arg_node1)

        if not isinstance(true_block, BlockObject):
            raise InterpreterError(ErrorCode.INT_DNU, "ifTrue:ifFalse: requires a block")

        arg_node2 = sender.find('arg[@order="2"]/expr')
        assert arg_node2 is not None
        false_block = self.evaluate_node(arg_node2)

        if not isinstance(false_block, BlockObject):
            raise InterpreterError(ErrorCode.INT_DNU, "ifTrue:ifFalse: requires a block")

        return output.if_true_if_false(true_block, false_block)

    def _handle_from(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for from: selector (constructor)"""
        arg_node = sender.find('arg[@order="1"]/expr')
        assert arg_node is not None
        obj = self.evaluate_node(arg_node)
        return output.sol_from(obj)

    def _handle_block_value(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for value/value:/value:value: etc. - block execution with variable arity"""
        if not isinstance(output, BlockObject):
            raise InterpreterError(ErrorCode.INT_DNU, "value selector only for Block")

        # Extract arguments based on actual arity in the block
        args: list[SolObject] = []
        for i in range(1, output.block.arity + 1):
            arg_node = sender.find(f'arg[@order="{i}"]/expr')
            if arg_node is not None:
                args.append(self.evaluate_node(arg_node))

        output.interpreter = self

        # Call sol_value with collected arguments
        return output.sol_value(*args)

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
