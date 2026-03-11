"""
This module defines the SOL block class.
Author: Kristian Rucek xrucekk00
"""

from __future__ import annotations

from interpreter.object import SolObject


class BlockObject(SolObject):
    """
    Represents a SOL block object.
    """

    def __init__(self, value: str):
        super().__init__("Block", value)

    def while_true(self, block: SolObject) -> None:
        """Executes block while condition is true"""

    def is_block(self) -> bool:
        """Evaluates if object is block"""
        return True
