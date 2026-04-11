"""
This module defines the SOL block class.
Author: Kristian Rucek xrucekk00
"""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from lxml import etree

from interpreter.error_codes import ErrorCode
from interpreter.exceptions import InterpreterError
from interpreter.input_model import Block
from interpreter.nil_object import nil
from interpreter.object import SolObject

if TYPE_CHECKING:
    from interpreter.interpreter import Interpreter


class BlockObject(SolObject):
    """
    Represents a SOL block object.
    """

    def __init__(self, block: Block):
        super().__init__("Block", None)
        self.block = block  # the Block from input_model — holds parameters and assigns
        self.interpreter: Interpreter | None = None  # Reference to interpreter for evaluation
        self.captured_self: SolObject | None = None  # self captured at block creation time

    def sol_new(self) -> BlockObject:
        """Creates new instance"""

        empty_block = Block(arity=0, parameters=[], assigns=[])
        return BlockObject(empty_block)

    def is_block(self) -> SolObject:
        """Evaluates if object is block"""
        from interpreter.boolean_object import true

        return true

    def sol_value(self, *args: SolObject) -> SolObject:
        """Execute block with variable number of parameters"""

        if self.interpreter is None:
            raise InterpreterError(ErrorCode.INT_DNU, "Block not properly initialized")

        if len(args) != self.block.arity:
            raise InterpreterError(ErrorCode.INT_DNU, "Wrong arguments")

        saved_vars = self.interpreter.variables.copy()

        # Start with a new scope
        local_vars: dict[str, SolObject] = saved_vars.copy()

        # Restore the captured self
        if self.captured_self is not None:
            local_vars["self"] = self.captured_self

        # Add parameter bindings
        for i, param in enumerate(self.block.parameters):
            local_vars[param.name] = args[i]

        self.interpreter.variables = local_vars

        try:
            result: SolObject = nil
            for assign in sorted(self.block.assigns, key=lambda a: int(a.order)):
                expr_xml = assign.expr.to_xml_tree()
                casted_expr_xml = cast(etree._Element, expr_xml)
                result = self.interpreter.evaluate_node(casted_expr_xml)
                var_name = assign.target.name

                if var_name in [param.name for param in self.block.parameters]:
                    raise InterpreterError(ErrorCode.SEM_COLLISION, "Cannot assign to parameter")

                self.interpreter.variables[var_name] = result

            return result

        finally:
            # Update outer scope with any changes made in block
            param_names = {param.name for param in self.block.parameters}
            for var_name, var_value in self.interpreter.variables.items():
                if var_name not in param_names and var_name != "self":
                    saved_vars[var_name] = var_value

            # Restore outer scope
            self.interpreter.variables = saved_vars

    def while_true(self, body: SolObject) -> SolObject:
        """Execute body block while condition (self) evaluates to true"""
        from interpreter.boolean_object import TrueObject

        if not isinstance(body, BlockObject):
            raise InterpreterError(
                error_code=ErrorCode.INT_DNU, message="whileTrue: expects block with value message"
            )

        last_result: SolObject = nil

        while True:
            condition_result = self.sol_value()

            if not isinstance(condition_result, TrueObject):
                break

            last_result = body.sol_value()

        return last_result
