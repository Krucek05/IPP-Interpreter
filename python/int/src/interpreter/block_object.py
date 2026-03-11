"""
This module defines the SOL block class.
Author: Kristian Rucek xrucekk00
"""

from __future__ import annotations

from interpreter.input_model import Block
from interpreter.object import SolObject


class BlockObject(SolObject):
    """
    Represents a SOL block object.
    """

    def __init__(self, block: Block):
        super().__init__("Block", None)
        self.block = block  # the Block from input_model — holds parameters and assigns

    def is_block(self) -> bool:
        """Evaluates if object is block"""
        return True
