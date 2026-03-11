"""
This module defines the base SOL object class.
Author: Kristian Rucek xrucekk00
"""

from __future__ import annotations


class SolObject:
    """
    SOL class, responsible for representing everything
    """

    def __init__(self, class_name: str, value: object = None):
        self.class_name = class_name
        self.value = value
        self.instance_vars: dict[str, SolObject] = {}

    def sol_new(self) -> SolObject:
        """Class message 'new' — creates a fresh instance of this object's class.
        self is the class literal (class_name='class', value='ClassName').
        """
        assert isinstance(self.value, str)
        return SolObject(self.value)

    def sol_from(self, obj: SolObject) -> SolObject:
        """Class message 'from:' — creates a new instance and shallow-copies
        all instance attributes from obj into it.
        """
        assert isinstance(self.value, str)
        new_obj = SolObject(self.value)
        new_obj.instance_vars = obj.instance_vars.copy()  # shallow copy
        return new_obj

    def new_instance(self, class_name: str, value: object = None) -> SolObject:
        """Creates new instance of class with given name and value"""
        return SolObject(class_name, value)

    def as_string(self) -> SolObject:
        """Returns string representation of object"""
        return SolObject("String", "")

    def as_integer(self) -> SolObject:
        """Returns integer representation of object, Nil by default"""
        return SolObject("Nil", None)

    def identical_to(self, other: SolObject) -> bool:
        """Evaluates if two objects are identical"""
        return self is other

    def equal_to(self, other: SolObject) -> bool:
        """Evaluates if two objects are equal (have the same value)"""
        return self.identical_to(other)

    def is_number(self) -> bool:
        """Evaluates if object is number"""
        return False

    def is_string(self) -> bool:
        """Evaluates if object is string"""
        return False

    def is_block(self) -> bool:
        """Evaluates if object is block"""
        return False

    def is_nil(self) -> bool:
        """Evaluates if object is nil"""
        return False

    def is_boolean(self) -> bool:
        """Evaluates if object is boolean"""
        return False
