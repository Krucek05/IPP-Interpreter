"""This module defines the SOL Integer object class."""

from interpreter.object import SolObject


class IntegerObject(SolObject):
    """
    Represents a SOL Integer object.
    """

    value: int

    def __init__(self, value: int):
        super().__init__("Integer", value)
