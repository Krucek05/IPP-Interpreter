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

    value: str  # Store the actual string value

    def __init__(self, value: str):
        super().__init__("String", value)

    def sol_new(self) -> StringObject:
        """Creates new empty string instance"""
        return StringObject("")

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
            from interpreter.nil_object import nil

            return nil

    def concatenate_with(self, other: SolObject) -> StringObject | SolObject:
        """Concatenates two strings together and returns the result"""
        if isinstance(other, StringObject):
            return StringObject(self.value + str(other.value))
        return SolObject("Nil", None)

    def starts_with_ends_before(
        self, start: SolObject, end: SolObject
    ) -> StringObject | SolObject:
        """Evaluates if string starts with start and ends with end"""

        if not isinstance(start, int) or not isinstance(end, int) or start <= 0 or end <= 0:
            from interpreter.nil_object import nil

            return nil
        if end - start <= 0:
            return StringObject("")

        return StringObject(self.value[start - 1 : end - 1])

    def length(self) -> SolObject:
        """Returns length of string"""
        from interpreter.integer_object import IntegerObject

        return IntegerObject(len(self.value))
