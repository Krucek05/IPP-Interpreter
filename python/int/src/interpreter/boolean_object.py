"""
Module for boolean objects
Author: Kristian Rucek xrucekk00
"""

from __future__ import annotations

from interpreter.object import SolObject
from interpreter.string_object import StringObject


class BooleanObject(SolObject):
    """Shared base for True and False."""

    def as_string(self) -> StringObject:
        """Returns string representation of boolean object"""
        return StringObject(str(self.value).lower())  # "true" or "false"

    def sol_and(self, other: SolObject) -> SolObject:
        """Logical AND operation"""
        if isinstance(other, BooleanObject):
            return TRUE if self.value and other.value else FALSE
        return FALSE

    def sol_or(self, other: SolObject) -> SolObject:
        """Logical OR operation"""
        if isinstance(other, BooleanObject):
            return TRUE if self.value or other.value else FALSE
        return FALSE

    def if_true_if_false(self, true_block: SolObject, false_block: SolObject) -> SolObject:
        """Executes true_block if condition is true — block execution handled by interpreter"""
        return SolObject("Nil", None)

    def is_boolean(self) -> bool:
        """Evaluates if object is boolean"""
        return False


class TrueObject(BooleanObject):
    """Represents a true boolean object."""

    def __init__(self) -> None:
        super().__init__("True", True)

    def sol_not(self) -> FalseObject:
        """Logical NOT operation"""
        return FALSE

    def is_boolean(self) -> bool:
        """Evaluates if object is boolean"""
        return True


class FalseObject(BooleanObject):
    """Represents a false boolean object."""

    def __init__(self) -> None:
        super().__init__("False", False)

    def sol_not(self) -> TrueObject:
        """Logical NOT operation"""
        return TRUE

    def is_boolean(self) -> bool:
        """Evaluates if object is boolean"""
        return True


TRUE = TrueObject()
FALSE = FalseObject()
