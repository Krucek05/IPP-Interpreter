"""This module defines the base SOL object class."""


class SolObject:
    """
    SOL class, responsible for representing everything
    """

    def __init__(self, class_name: str, value: object = None):
        self.class_name = class_name
        self.value = value
