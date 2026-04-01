"""
This module defines the SOL nil class.
Author: Kristian Rucek xrucekk00
"""

from __future__ import annotations

from interpreter.object import SolObject


class NilObject(SolObject):
    """
    Represents the Nil singleton — only one instance ever exists.
    """

    _instance: NilObject | None = None

    def __new__(cls) -> NilObject:
        """Ensures only one instance of NilObject exists (singleton pattern)"""
        if cls is NilObject:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance
        # subclasses of Nil behave normally (no singleton)
        return super().__new__(cls)

    def __init__(self) -> None:
        if not hasattr(self, "_initialized"):
            super().__init__("Nil", None)
            self._initialized = True

    def as_string(self) -> SolObject:
        """Returns string representation of nil object"""
        from interpreter.string_object import StringObject

        return StringObject("nil")

    def is_nil(self) -> bool:
        """Evaluates if object is nil"""
        return True
