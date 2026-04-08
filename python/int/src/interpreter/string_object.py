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

    @staticmethod
    def _unescape_string(s: str) -> str:
        """
        Process escape sequences in string literals.
        """
        result = s.replace("\\\\", "\x00")  # Temporarily replace \\ with null char
        result = result.replace("\\n", "\n")  # \n → newline
        result = result.replace("\\'", "'")  # \' → apostrophe
        return result.replace("\x00", "\\")  # null char → backslash

    def __init__(self, value: str):
        unescaped = self._unescape_string(value)
        super().__init__("String", unescaped)

    def sol_new(self) -> StringObject:
        """Creates new empty string instance"""
        return StringObject("")

    def sol_from(self, obj: SolObject) -> SolObject:
        """Creates new String from another object"""
        from interpreter.error_codes import ErrorCode
        from interpreter.exceptions import InterpreterError
        from interpreter.integer_object import IntegerObject

        if isinstance(obj, StringObject):
            return StringObject(obj.value)

        if isinstance(obj, IntegerObject):
            return StringObject(str(obj.value))

        # For other types, raise error
        raise InterpreterError(ErrorCode.INT_INVALID_ARG, "Cannot convert to string")

    @staticmethod
    def read() -> StringObject:
        """Reads a line of input from stdin and returns it as a StringObject"""
        return StringObject(input())

    def sol_print(self) -> SolObject:
        """Prints string value to stdout"""
        print(self.value, end="")
        return self

    def equal_to(self, other: SolObject) -> SolObject:
        """Evaluates if two strings are equal"""
        from interpreter.boolean_object import false, true

        if not isinstance(other, StringObject):
            return false
        return true if self.value == other.value else false

    def as_string(self) -> StringObject:
        """Returns string itself"""
        return self

    def is_string(self) -> SolObject:
        """Evaluates if object is string"""
        from interpreter.boolean_object import true

        return true

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
        from interpreter.nil_object import nil

        return nil

    def starts_with_ends_before(
        self, start: SolObject, end: SolObject
    ) -> StringObject | SolObject:
        """Evaluates if string starts with start and ends with end"""
        from interpreter.integer_object import IntegerObject
        from interpreter.nil_object import nil

        if not isinstance(start, IntegerObject) or not isinstance(end, IntegerObject):
            return nil
        if start.value <= 0 or end.value <= 0:
            return nil
        if end.value - start.value <= 0:
            return StringObject("")

        return StringObject(self.value[start.value - 1 : end.value - 1])

    def length(self) -> SolObject:
        """Returns length of string"""
        from interpreter.integer_object import IntegerObject

        return IntegerObject(len(self.value))
