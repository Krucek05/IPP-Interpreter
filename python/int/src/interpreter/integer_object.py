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

    value: int = 0

    def __init__(self, value: int):
        super().__init__("Integer", value)

    def sol_new(self) -> IntegerObject:
        """Creates new integer instance"""
        return IntegerObject(0)

    def sol_from(self, obj: SolObject) -> SolObject:
        """Creates new Integer from another object"""
        from interpreter.string_object import StringObject

        if isinstance(obj, IntegerObject):
            return IntegerObject(obj.value)

        if isinstance(obj, StringObject):
            try:
                return IntegerObject(int(obj.value))
            except ValueError as err:
                raise InterpreterError(
                    ErrorCode.INT_INVALID_ARG, "Cannot convert to integer"
                ) from err

        raise InterpreterError(ErrorCode.INT_INVALID_ARG, "Incompatible type")

    def equal_to(self, other: SolObject) -> SolObject:
        """Evaluates if data of two objects are same"""
        from interpreter.boolean_object import false, true

        if not isinstance(other, IntegerObject):
            return false
        return true if self.value == other.value else false

    def greater_than(self, other: SolObject) -> SolObject:
        """Evaluates if this integer is greater than other"""
        from interpreter.boolean_object import false, true

        if not isinstance(other, IntegerObject):
            raise InterpreterError(ErrorCode.INT_DNU, "greaterThan: requires Integer")
        return true if self.value > other.value else false

    def plus(self, other: SolObject) -> SolObject:
        """Adds two integers together and returns the result"""
        if not isinstance(other, IntegerObject):
            raise InterpreterError(ErrorCode.INT_DNU, "plus: requires Integer")
        return IntegerObject(self.value + other.value)

    def minus(self, other: SolObject) -> SolObject:
        """Subtracts other integer from this and returns the result"""
        if not isinstance(other, IntegerObject):
            raise InterpreterError(ErrorCode.INT_DNU, "minus: requires Integer")
        return IntegerObject(self.value - other.value)

    def multiply_by(self, other: SolObject) -> SolObject:
        """Multiplies two integers together and returns the result"""
        if not isinstance(other, IntegerObject):
            raise InterpreterError(ErrorCode.INT_DNU, "multiplyBy: requires Integer")
        return IntegerObject(self.value * other.value)

    def divide_by(self, other: SolObject) -> SolObject:
        """Divides this integer by other and returns the result"""
        if not isinstance(other, IntegerObject):
            raise InterpreterError(ErrorCode.INT_DNU, "divBy: requires Integer")
        if other.value == 0:
            raise InterpreterError(ErrorCode.INT_INVALID_ARG, "Cannot divide by zero")
        return IntegerObject(self.value // other.value)

    def as_string(self) -> SolObject:
        """Converts integer to string and returns it"""
        from interpreter.string_object import StringObject

        return StringObject(str(self.value))

    def as_integer(self) -> SolObject:
        """Returns integer itself"""
        return self

    def is_number(self) -> SolObject:
        """Evaluates if object is number"""
        from interpreter.boolean_object import true

        return true

    def times_repeated(self, block: SolObject) -> SolObject:
        """Executes block number of times — block execution handled by interpreter"""
        from interpreter.block_object import BlockObject
        from interpreter.nil_object import nil

        if not isinstance(block, BlockObject):
            raise InterpreterError(
                error_code=ErrorCode.INT_DNU,
                message="timesRepeat: expects block with value: message",
            )

        if self.value <= 0:
            return nil

        last_result: SolObject = nil
        for _ in range(1, self.value + 1):
            last_result = block.sol_value()

        return last_result
