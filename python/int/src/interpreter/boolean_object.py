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
        if not isinstance(other, BooleanObject):
            raise InterpreterError(ErrorCode.INT_DNU)

        return true if self.value and other.value else false

    def sol_or(self, other: SolObject) -> SolObject:
        """Logical OR operation"""
        if not isinstance(other, BooleanObject):
            raise InterpreterError(ErrorCode.INT_DNU)

        return true if self.value or other.value else false

    def if_true_if_false(self, true_block: SolObject, false_block: SolObject) -> SolObject:
        """Executes true_block if condition is true — block execution handled by interpreter"""

        if not isinstance(true_block, BlockObject):
            raise InterpreterError(ErrorCode.INT_DNU)

        if not isinstance(false_block, BlockObject):
            raise InterpreterError(ErrorCode.INT_DNU)

        if isinstance(self, TrueObject):
            return true_block
        return false_block

    def is_boolean(self) -> TrueObject:
        """Evaluates if object is boolean"""
        return true


class TrueObject(BooleanObject):
    """Represents a true boolean object."""

    def __init__(self) -> None:
        super().__init__("True", True)

    def sol_not(self) -> FalseObject:
        """Logical NOT operation"""
        return false


class FalseObject(BooleanObject):
    """Represents a false boolean object."""

    def __init__(self) -> None:
        super().__init__("False", False)

    def sol_not(self) -> TrueObject:
        """Logical NOT operation"""
        return true


true = TrueObject()
false = FalseObject()
