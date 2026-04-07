"""
This module defines the SOL nil class.
Author: Kristian Rucek xrucekk00
"""

from __future__ import annotations

from interpreter.object import SolObject


class NilObject(SolObject):
    """
    Represents the Nil singleton — only one instance ever exists.
    Nil.new and Nil.from: always return the same instance.
    """

    _instance: NilObject | None = None

    def __new__(cls) -> NilObject:
        """Ensures only one instance of NilObject exists (singleton pattern)."""
        if cls is NilObject:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance
        # Subclasses of Nil behave normally (no singleton)
        return super().__new__(cls)

    def __init__(self) -> None:
        """Initialize Nil singleton (only once)."""
        if not hasattr(self, "_initialized"):
            super().__init__("Nil", None)
            self._initialized = True

    def sol_new(self) -> NilObject:
        """Returns same Nil singleton"""
        return self

    def sol_from(self, obj: SolObject) -> NilObject:
        """Returns same Nil singleton"""
        return self

    def as_string(self) -> SolObject:
        """Returns string 'nil'"""
        from interpreter.string_object import StringObject

        return StringObject("nil")

    def is_nil(self) -> SolObject:
        """Returns true — nil is nil"""
        from interpreter.boolean_object import true

        return true


# Global singleton instance
nil = NilObject()
