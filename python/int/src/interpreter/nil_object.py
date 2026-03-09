"""
This module defines the SOL nil class.
Author: Kristian Rucek xrucekk00
"""

from __future__ import annotations

from interpreter.object import SolObject


class NilObject(SolObject):
    """
    Represents a nil object.
    """

    def __init__(self, value: str):
        super().__init__("String", value)

    def as_string(self) -> SolObject:
        """Returns string representation of nil object"""
        from interpreter.string_object import StringObject

        return StringObject("nil")
