"""
This module defines the SOL block class.
Author: Kristian Rucek xrucekk00
"""

from __future__ import annotations

from interpreter.error_codes import ErrorCode
from interpreter.exceptions import InterpreterError
from interpreter.input_model import Block
from interpreter.nil_object import nil
from interpreter.object import SolObject


class BlockObject(SolObject):
    """
    Represents a SOL block object.
    """

    def __init__(self, block: Block):
        super().__init__("Block", None)
        self.block = block  # the Block from input_model — holds parameters and assigns

    def sol_new(self) -> BlockObject:
        """Creates new instance"""

        empty_block = Block(arity=0, parameters=[], assigns=[])
        return BlockObject(empty_block)

    def sol_value(self) -> SolObject:
        """0-parameter block execution"""
        return nil

    def sol_value_with_arg(self, arg: SolObject) -> SolObject:
        """1-parameter block execution"""
        return nil

    def sol_value_with_two_args(self, arg1: SolObject, arg2: SolObject) -> SolObject:
        """2-parameter block execution"""
        return nil

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
