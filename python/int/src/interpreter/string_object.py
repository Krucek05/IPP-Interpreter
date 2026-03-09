"""
This module defines the SOL String object class.
Author: Kristian Rucek xrucekk00
"""

from __future__ import annotations

from interpreter.object import SolObject


class StringObject(SolObject):
    """
    Represents a SOL String object.
    """

    value: str

    def __init__(self, value: str):
        super().__init__("String", value)

    @staticmethod
    def read() -> StringObject:
        """Reads a line of input from stdin and returns it as a StringObject"""
        return StringObject(input())

    def sol_print(self) -> SolObject:
        """Prints string value to stdout"""
        print(self.value)
        return self

    def equal_to(self, other: SolObject) -> bool:
        """Evaluates if two strings are equal"""
        return bool(self.value == other.value)

    def as_string(self) -> StringObject:
        """Returns string itself"""
        return self

    def as_integer(self) -> SolObject:
        """Converts string to integer and returns it"""
        from interpreter.integer_object import IntegerObject

        try:
            return IntegerObject(int(self.value))
        except ValueError:
            return SolObject("Nil", None)

    def concatenate_with(self, other: SolObject) -> StringObject | SolObject:
        """Concatenates two strings together and returns the result"""
        if isinstance(other, StringObject):
            return StringObject(self.value + str(other.value))
        return SolObject("Nil", None)

    def starts_with_ends_before(self, start: str, end: str) -> StringObject | SolObject:
        """Evaluates if string starts with start and ends with end"""

        if not isinstance(start, int) or not isinstance(end, int) or start <= 0 or end <= 0:
            return SolObject("Nil", None)
        if end - start <= 0:
            return StringObject("")

        return StringObject(self.value[start - 1 : end - 1])

    def length(self) -> int:
        """Returns length of string"""
        return len(self.value)
