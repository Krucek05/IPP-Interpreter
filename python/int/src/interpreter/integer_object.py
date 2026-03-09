"""
This module defines the SOL Integer object class.
Author: Kristian Rucek xrucekk00
"""

from __future__ import annotations

from interpreter.error_codes import ErrorCode
from interpreter.exceptions import InterpreterError
from interpreter.object import SolObject


class IntegerObject(SolObject):
    """
    Represents a SOL Integer object.
    """

    value: int

    def __init__(self, value: int):
        super().__init__("Integer", value)

    def equal_to(self, other: SolObject) -> bool:
        """Evaluates if data of two objects are same"""
        return bool(self.value == other.value)

    def greather_then(self, first_value: int, second_value: int) -> bool:
        """Evaulates if first value is greather then second value"""
        return first_value > second_value

    def plus(self, first_value: int, second_value: int) -> int:
        """Adds two integers together and returns the result"""
        return first_value + second_value

    def minus(self, first_value: int, second_value: int) -> int:
        """Subtracts second integer from first and returns the result"""
        return first_value - second_value

    def multiply_by(self, first_value: int, second_value: int) -> int:
        """Multiplies two integers together and returns the result"""
        return first_value * second_value

    def devide_by(self, first_value: int, second_value: int) -> int:
        """Divides first integer by second and returns the result"""
        if not second_value:
            raise InterpreterError(
                error_code=ErrorCode.INT_INVALID_ARG, message="Can not devide by zero"
            )

        return first_value // second_value

    def as_string(self) -> SolObject:
        """Converts integer to string and returns it"""
        from interpreter.string_object import StringObject

        return StringObject(str(self.value))

    def as_integer(self, number: int) -> int:
        """Returns integer itself"""
        return number

    def times_repeated(self, block: SolObject) -> SolObject:
        """Executes block number of times — block execution handled by interpreter"""
        return SolObject("Nil", None)
