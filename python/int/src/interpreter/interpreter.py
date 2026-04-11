"""
This module contains the main logic of the interpreter.

IPP: You must definitely modify this file. Bend it to your will.

Author: Ondřej Ondryáš <iondryas@fit.vut.cz>
Author: Kristian Rucek xrucekk00
"""

import logging
from pathlib import Path
from typing import Any, TextIO, cast

from lxml import etree
from lxml.etree import ParseError
from pydantic import ValidationError

from interpreter.block_object import BlockObject
from interpreter.boolean_object import BooleanObject, false, true
from interpreter.error_codes import ErrorCode
from interpreter.exceptions import InterpreterError
from interpreter.input_model import ClassDef, Method, Program
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
        self.classes: dict[str, ClassDef] = {}
        self.xml_tree: etree._ElementTree | None = None
        self.root: etree._Element | None = None
        self.current_method_class: str | None = None  # Helper for super handling
        self.current_method_selector: str | None = None  # helper for super handling

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

        if self.current_program:
            for class_def in self.current_program.classes:
                if class_def.name in self.classes:
                    raise InterpreterError(
                        ErrorCode.SEM_ERROR, f"Class {class_def.name} is redefined"
                    )
                self.classes[class_def.name] = class_def

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
                return SolObject("class", node_value)

        if node.tag == "block":
            # Parse XML block element back to pydantic Block model
            from interpreter.input_model import Block

            block_model = Block.from_xml_tree(cast(Any, node))
            block_obj = BlockObject(block_model)
            block_obj.interpreter = self
            # Capture the current self at block creation time (lexical closure)
            block_obj.captured_self = self.variables.get("self", nil)
            return block_obj

        if node.tag == "send":
            return self.dispatching(node)

        if node.tag == "var":
            var_name = node.get("name")
            if var_name is None:
                return nil
            return self._evaluate_variable(var_name)

        return nil

    def _evaluate_variable(self, var_name: str) -> SolObject:
        """Evaluate a variable by name, handling special case of 'super'."""
        if var_name == "super":
            current_self = self.variables.get("self")
            if not current_self:
                raise InterpreterError(ErrorCode.SEM_UNDEF, "super: not in instance context")
            return current_self

        if var_name not in self.variables:
            raise InterpreterError(ErrorCode.SEM_UNDEF, f"Undefined variable: {var_name}")

        return self.variables[var_name]

    def _handle_super_call(self, selector: str, sender: etree._Element) -> SolObject:
        """Handle super calls. Looks up method in parent class and executes it."""
        output = self.variables.get("self", nil)
        if not selector or not isinstance(output, SolObject):
            return output

        # When super called, look in the parent of the class that's currently executing the method
        if self.current_method_class:
            method_class_def = self.classes.get(self.current_method_class)
            if (
                not method_class_def
                or not method_class_def.parent
                or method_class_def.parent == "Object"
            ):
                return output
            parent_class = method_class_def.parent
        else:
            class_def = self.classes.get(output.class_name)
            if not class_def or not class_def.parent or class_def.parent == "Object":
                return output
            parent_class = class_def.parent

        # Never recurse
        if self.current_method_class == parent_class and self.current_method_selector == selector:
            return output

        method = self.find_method(parent_class, selector)
        if method:
            args: list[SolObject] = []
            i = 1
            while True:
                arg_node = sender.find(f'arg[@order="{i}"]/expr')
                if arg_node is None:
                    break
                args.append(self.evaluate_node(arg_node))
                i += 1
            return self._execute_method(output, method, args)

        return output

    def _handle_attribute_access(
        self, output: SolObject, selector: str, sender: etree._Element
    ) -> SolObject | None:
        """Handle instance attribute getters/setters. Returns value if handled, None otherwise."""
        if not selector:
            return None

        # attributeName:
        if selector.endswith(":"):
            attr_name = selector[:-1]  # Remove the ':'
            arg_node = sender.find('arg[@order="1"]/expr')
            if arg_node is not None:
                value = self.evaluate_node(arg_node)
                output.instance_vars[attr_name] = value
                return value

        # attributeName (no colon)
        else:
            if selector in output.instance_vars:
                return output.instance_vars[selector]

        return None

    def dispatching(self, sender: etree._Element) -> SolObject | Any:
        """Dispatches message to appropriate handler based on selector"""
        selector = sender.get("selector")

        output_node = sender.find("expr")
        assert output_node is not None

        # Check if this is a super call
        is_super_call = (
            len(output_node) > 0
            and output_node[0].tag == "var"
            and output_node[0].get("name") == "super"
        )

        if is_super_call:
            # Handle super method calls specially
            return self._handle_super_call(selector or "", sender)

        output = self.evaluate_node(output_node)

        # Handle block value selectors (value, value:, value:value:, etc.)
        if (
            selector is not None
            and selector.startswith("value")
            and isinstance(output, BlockObject)
        ):
            arity = selector.count(":")
            block_args: list[SolObject] = []
            for i in range(1, arity + 1):
                arg_node = sender.find(f'arg[@order="{i}"]/expr')
                if arg_node is not None:
                    block_args.append(self.evaluate_node(arg_node))

            output.interpreter = self
            return output.sol_value(*block_args)

        if selector:
            method = self.find_method(output.class_name, selector)
            if method:
                method_args: list[SolObject] = []
                i = 1
                while True:
                    arg_node = sender.find(f'arg[@order="{i}"]/expr')
                    if arg_node is None:
                        break
                    method_args.append(self.evaluate_node(arg_node))
                    i += 1

                return self.send_message(output, selector, method_args)

            # Check for attribute/method collision
            if selector.endswith(":"):
                base_name = selector.rstrip(":")
                base_method = self.find_method(output.class_name, base_name)

                handlers_keys = {
                    "print",
                    "asString",
                    "asInteger",
                    "identicalTo:",
                    "equalTo:",
                    "isNumber",
                    "isBlock",
                    "isNil",
                    "isBoolean",
                    "greaterThan:",
                    "plus:",
                    "minus:",
                    "multiplyBy:",
                    "divBy:",
                    "timesRepeat:",
                    "read",
                    "concatenateWith:",
                    "startsWith:endsBefore:",
                    "whileTrue:",
                    "not",
                    "and:",
                    "or:",
                    "ifTrue:ifFalse:",
                    "new",
                    "from:",
                    "self",
                    "length",
                }

                if base_method or base_name in handlers_keys:
                    raise InterpreterError(
                        ErrorCode.INT_INST_ATTR,
                        f"Attribute {selector} collides with method {base_name}",
                    )

        handlers = {
            "print": self._handle_print,
            "asString": lambda o, _: o.as_string(),
            "isString": lambda o, _: o.is_string(),
            "asInteger": self._handle_as_integer,
            "identicalTo:": self._handle_identical_to,
            "equalTo:": self._handle_equal_to,
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
            "concatenateWith:": self._handle_concat_with,
            "startsWith:endsBefore:": self._handle_starts_with_ends_before,
            "whileTrue:": self._handle_while_true,
            "not": self._handle_not,
            "and:": self._handle_and,
            "or:": self._handle_or,
            "ifTrue:ifFalse:": self._handle_if_true_if_false,
            "new": self._handle_new,
            "from:": self._handle_from,
            "self": self._handle_self,
            "length": self._handle_length,
        }

        if selector in handlers:
            return handlers[selector](output, sender)

        attr_result = self._handle_attribute_access(output, selector or "", sender)
        if attr_result is not None:
            return attr_result

        raise InterpreterError(ErrorCode.INT_DNU, f"Unknown message {selector}")

    def _handle_print(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for print selector"""
        if not isinstance(output, StringObject):
            raise InterpreterError(ErrorCode.SEM_ARITY, "print can only be called on String")
        return output.sol_print()

    def _handle_as_integer(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for asInteger selector"""
        if isinstance(output, IntegerObject):
            return output
        if isinstance(output, StringObject):
            try:
                return IntegerObject(int(output.value))
            except ValueError:
                return nil
        raise InterpreterError(ErrorCode.SEM_ARITY, "asInteger: only for Integer or String")

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
        return output.equal_to(other)

    def _handle_greater_than(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for greaterThan: selector"""
        if not isinstance(output, IntegerObject):
            raise InterpreterError(ErrorCode.SEM_ARITY, "greaterThan: only for Integer")
        arg_node = sender.find('arg[@order="1"]/expr')
        assert arg_node is not None
        other = self.evaluate_node(arg_node)
        return output.greater_than(other)

    def _handle_plus(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for plus: selector"""
        if not isinstance(output, IntegerObject):
            raise InterpreterError(ErrorCode.SEM_ARITY, "plus: only for Integer")
        arg_node = sender.find('arg[@order="1"]/expr')
        assert arg_node is not None
        other = self.evaluate_node(arg_node)
        return output.plus(other)

    def _handle_minus(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for minus: selector"""
        if not isinstance(output, IntegerObject):
            raise InterpreterError(ErrorCode.SEM_ARITY, "minus: only for Integer")
        arg_node = sender.find('arg[@order="1"]/expr')
        assert arg_node is not None
        other = self.evaluate_node(arg_node)
        return output.minus(other)

    def _handle_multiply_by(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for multiplyBy: selector"""
        if not isinstance(output, IntegerObject):
            raise InterpreterError(ErrorCode.SEM_ARITY, "multiplyBy: only for Integer")
        arg_node = sender.find('arg[@order="1"]/expr')
        assert arg_node is not None
        other = self.evaluate_node(arg_node)
        return output.multiply_by(other)

    def _handle_div_by(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for divBy: selector"""
        if not isinstance(output, IntegerObject):
            raise InterpreterError(ErrorCode.SEM_ARITY, "divBy: only for Integer")
        arg_node = sender.find('arg[@order="1"]/expr')
        assert arg_node is not None
        other = self.evaluate_node(arg_node)
        return output.divide_by(other)

    def _handle_times_repeat(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for timesRepeat: selector"""
        if not isinstance(output, IntegerObject):
            raise InterpreterError(ErrorCode.SEM_ARITY, "timesRepeat: only for Integer")
        arg_node = sender.find('arg[@order="1"]/expr')
        assert arg_node is not None
        block = self.evaluate_node(arg_node)

        if not isinstance(block, BlockObject):
            raise InterpreterError(ErrorCode.SEM_ARITY, "timesRepeat: requires a block")

        result: SolObject = nil
        if output.value > 0:
            for i in range(1, output.value + 1):
                iteration = IntegerObject(i)
                result = block.sol_value(iteration)

        return result

    def _handle_concat_with(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for concatenateWith selector"""
        if not isinstance(output, StringObject):
            raise InterpreterError(ErrorCode.SEM_ARITY, "concatenateWith not called with String")
        arg_node = sender.find('arg[@order="1"]/expr')
        assert arg_node is not None
        other = self.evaluate_node(arg_node)
        return output.concatenate_with(other)

    def _handle_length(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for length selector"""
        if not isinstance(output, StringObject):
            raise InterpreterError(ErrorCode.SEM_ARITY, "length: only for String")
        return output.length()

    def _handle_starts_with_ends_before(
        self, output: SolObject, sender: etree._Element
    ) -> SolObject:
        """Handler for startsWith:endsBefore: selector"""
        if not isinstance(output, StringObject):
            raise InterpreterError(
                ErrorCode.SEM_ARITY, "startsWith:endsBefore: not called with String"
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
            raise InterpreterError(ErrorCode.SEM_ARITY, "whileTrue: not called with Block")
        arg_node = sender.find('arg[@order="1"]/expr')
        assert arg_node is not None
        block = self.evaluate_node(arg_node)

        if not isinstance(block, BlockObject):
            raise InterpreterError(ErrorCode.SEM_ARITY, "whileTrue: requires a block")

        return output.while_true(block)

    def _handle_not(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for not selector"""
        if not isinstance(output, BooleanObject):
            raise InterpreterError(ErrorCode.SEM_ARITY, "not: can only be called on Boolean")
        return output.sol_not()

    def _handle_and(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for and selector"""
        if not isinstance(output, BooleanObject):
            raise InterpreterError(ErrorCode.SEM_ARITY, "and: not called with Boolean")
        arg_node = sender.find('arg[@order="1"]/expr')
        assert arg_node is not None
        block = self.evaluate_node(arg_node)

        if not isinstance(block, BlockObject):
            raise InterpreterError(ErrorCode.SEM_ARITY, "and: requires a block")

        return output.sol_and(block)

    def _handle_or(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for or selector"""
        if not isinstance(output, BooleanObject):
            raise InterpreterError(ErrorCode.SEM_ARITY, "or: not called with Boolean")
        arg_node = sender.find('arg[@order="1"]/expr')
        assert arg_node is not None
        block = self.evaluate_node(arg_node)

        if not isinstance(block, BlockObject):
            raise InterpreterError(ErrorCode.SEM_ARITY, "or: requires a block")

        return output.sol_or(block)

    def _handle_if_true_if_false(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for ifTrue:ifFalse selector"""
        if not isinstance(output, BooleanObject):
            raise InterpreterError(
                ErrorCode.SEM_ARITY, "ifTrue:ifFalse: can only be called on Boolean"
            )

        arg_node1 = sender.find('arg[@order="1"]/expr')
        assert arg_node1 is not None
        true_block = self.evaluate_node(arg_node1)

        if not isinstance(true_block, BlockObject):
            raise InterpreterError(ErrorCode.SEM_ARITY, "ifTrue:ifFalse: requires a block")

        arg_node2 = sender.find('arg[@order="2"]/expr')
        assert arg_node2 is not None
        false_block = self.evaluate_node(arg_node2)

        if not isinstance(false_block, BlockObject):
            raise InterpreterError(ErrorCode.SEM_ARITY, "ifTrue:ifFalse: requires a block")

        return output.if_true_if_false(true_block, false_block)

    def _handle_from(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for from: selector (constructor)"""
        arg_node = sender.find('arg[@order="1"]/expr')
        assert arg_node is not None
        obj = self.evaluate_node(arg_node)

        # For class references, check if it's a subclass of Integer or String
        if output.class_name == "class":
            class_name = str(output.value)

            current_class = self.classes.get(class_name)
            if current_class:
                parent: str | None = current_class.parent
                while parent and parent != "Object":
                    if parent == "Integer":
                        from interpreter.integer_object import IntegerObject

                        int_instance: SolObject = IntegerObject(0)
                        result = int_instance.sol_from(obj)
                        result.class_name = class_name
                        return result
                    if parent == "String":
                        from interpreter.string_object import StringObject

                        str_instance: SolObject = StringObject("")
                        result = str_instance.sol_from(obj)
                        result.class_name = class_name
                        return result

                    parent_def = self.classes.get(parent)
                    parent = parent_def.parent if parent_def else None

        return output.sol_from(obj)

    def _handle_new(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for new selector - creates instance of receiver's class"""
        # Special case for built-in classes that need special instantiation
        if output.class_name == "Block":
            from interpreter.input_model import Block

            empty_block = Block(arity=0, parameters=[], assigns=[])
            block_obj = BlockObject(empty_block)
            block_obj.interpreter = self
            return block_obj

        return output.sol_new()

    def _handle_block_value(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for value/value:/value:value: etc. - block execution with variable arity"""
        if not isinstance(output, BlockObject):
            raise InterpreterError(ErrorCode.SEM_ARITY, "value selector only for Block")

        # Extract arguments based on actual arity in the block
        args: list[SolObject] = []
        for i in range(1, output.block.arity + 1):
            arg_node = sender.find(f'arg[@order="{i}"]/expr')
            if arg_node is not None:
                args.append(self.evaluate_node(arg_node))

        output.interpreter = self

        return output.sol_value(*args)

    def _handle_self(self, output: SolObject, sender: etree._Element) -> SolObject:
        """Handler for self selector"""
        return output

    def find_method(self, class_name: str, selector: str) -> Method | None:
        """Recursively lookup method in class and parent classes"""
        class_def = self.classes.get(class_name)
        if not class_def:
            # If class not found, it might be a built-in class
            return None

        method = next((m for m in class_def.methods if m.selector == selector), None)
        if method:
            return method

        # Recursively look in parent class
        if class_def.parent != "Object":
            return self.find_method(class_def.parent, selector)

        return None

    def send_message(
        self, receiver: SolObject, selector: str, args: list[SolObject] | None = None
    ) -> SolObject:
        """Send message to an object (user-defined or built-in)"""
        if args is None:
            args = []

        # First check for user-defined methods
        method = self.find_method(receiver.class_name, selector)
        if method:
            return self._execute_method(receiver, method, args)

        raise InterpreterError(ErrorCode.INT_DNU, f"Unknown selector: {selector}")

    def _execute_method(
        self, receiver: SolObject, method: Method, args: list[SolObject]
    ) -> SolObject:
        """Execute a user-defined method"""
        saved_vars = self.variables.copy()
        saved_method_class = self.current_method_class
        saved_method_selector = self.current_method_selector

        try:
            # Determine which class the method belongs to by searching
            for class_name, class_def in self.classes.items():
                if method in class_def.methods:
                    self.current_method_class = class_name
                    break

            # Track the selector being executed
            self.current_method_selector = method.selector

            self.variables["self"] = receiver

            for i, param in enumerate(method.block.parameters):
                if i < len(args):
                    self.variables[param.name] = args[i]

            result: SolObject = nil
            for assign in method.block.assigns:
                expr_xml = assign.expr.to_xml_tree()
                casted_expr_xml = cast(etree._Element, expr_xml)
                result = self.evaluate_node(casted_expr_xml)

                var_name = assign.target.name

                if var_name != "_":
                    self.variables[var_name] = result

            return result
        finally:
            self.variables = saved_vars
            self.current_method_class = saved_method_class
            self.current_method_selector = saved_method_selector

    def execute(self, input_io: TextIO) -> None:
        """
        Executes the currently loaded program, using the provided input stream as standard input.
        """
        logger.info("Executing program")

        assert self.root is not None
        assert self.current_program is not None

        main_class_def = next((c for c in self.current_program.classes if c.name == "Main"), None)

        if main_class_def is None:
            raise InterpreterError(ErrorCode.SEM_MAIN, "Main class not found")

        # Find the run method in Main class
        run_method = next((m for m in main_class_def.methods if m.selector == "run"), None)

        if run_method is None:
            raise InterpreterError(ErrorCode.SEM_MAIN, "Main missing run method")

        # Create Main instance and execute run method
        main_instance = SolObject("Main", None)
        self._execute_method(main_instance, run_method, [])
