"""This module defines the SOL String object class."""

from interpreter.object import SolObject


class StringObject(SolObject):
    """
    Represents a SOL String object.
    """

    value: str

    def __init__(self, value: str):
        super().__init__("String", value)

    def sol_print(self) -> StringObject:
        """Prints string value to stdout"""
        print(self.value)
        return self
