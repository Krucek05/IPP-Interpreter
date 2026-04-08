"""
Module for boolean objects
Author: Kristian Rucek xrucekk00
"""

from __future__ import annotations

from interpreter.block_object import BlockObject
from interpreter.error_codes import ErrorCode
from interpreter.exceptions import InterpreterError
from interpreter.object import SolObject
from interpreter.string_object import StringObject


class BooleanObject(SolObject):
    """Shared base for True and False."""

    value: bool  # Store the actual boolean value

    def as_string(self) -> StringObject:
        """Returns string representation of boolean object"""
        return StringObject(str(self.value).lower())  # "true" or "false"

    def sol_and(self, other: SolObject) -> SolObject:
        """Logical AND operation"""
        if not isinstance(other, BlockObject):
            raise InterpreterError(ErrorCode.INT_DNU)

        # if left is false, don't execute right block
        if not self.value:
            return false

        return other.sol_value()

    def sol_or(self, other: SolObject) -> SolObject:
        """Logical OR operation with short-circuit evaluation"""
        if not isinstance(other, BlockObject):
            raise InterpreterError(ErrorCode.INT_DNU)

        # if left is true, don't execute right block
        if self.value:
            return true

        return other.sol_value()

    def if_true_if_false(self, true_block: SolObject, false_block: SolObject) -> SolObject:
        """Executes true_block if condition is true, else false_block"""

        if not isinstance(true_block, BlockObject):
            raise InterpreterError(ErrorCode.INT_DNU)

        if not isinstance(false_block, BlockObject):
            raise InterpreterError(ErrorCode.INT_DNU)

        if isinstance(self, TrueObject):
            return true_block.sol_value()
        return false_block.sol_value()

    def is_boolean(self) -> TrueObject:
        """Evaluates if object is boolean"""
        return true

    def sol_not(self) -> SolObject:
        """Logical NOT operation"""
        return false if self.value else true


class TrueObject(BooleanObject):
    """Represents a true boolean object."""

    def __init__(self) -> None:
        super().__init__("True", True)


class FalseObject(BooleanObject):
    """Represents a false boolean object."""

    def __init__(self) -> None:
        super().__init__("False", False)


true = TrueObject()
false = FalseObject()
