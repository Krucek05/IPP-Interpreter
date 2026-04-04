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
        if self.class_name == "class":
            class_name = str(self.value)
            return SolObject(class_name, None)
        return self

    def sol_from(self, obj: SolObject) -> SolObject:
        """Class message 'from:' — creates a new instance and shallow-copies
        all instance attributes from obj into it.
        """

        if self.class_name == "class":
            class_name = str(self.value)
            new_obj = SolObject(class_name, None)

            new_obj.instance_vars = obj.instance_vars.copy()

            # Todoo: Check for required internal attributes
            # For now, assume all are provided (error 53 check goes here)

            return new_obj

        return self

    def new_instance(self, class_name: str, value: object = None) -> SolObject:
        """Creates new instance of class with given name and value"""
        return SolObject(class_name, value)

    def as_string(self) -> SolObject:
        """Returns string representation of object"""
        return SolObject("String", "")

    def identical_to(self, other: SolObject) -> bool:
        """Evaluates if two objects are identical"""
        return self is other

    def equal_to(self, other: SolObject) -> bool:
        """Evaluates if two objects are equal (have the same value)"""
        if not self.instance_vars:
            return self.identical_to(other)

        if set(self.instance_vars.keys()) != set(other.instance_vars.keys()):
            return False

        for key in self.instance_vars:
            if not self.instance_vars[key].equal_to(other.instance_vars[key]):
                return False

        return True

    def is_number(self) -> SolObject:
        """Evaluates if object is number"""
        from interpreter.boolean_object import false

        return false

    def is_string(self) -> SolObject:
        """Evaluates if object is string"""
        from interpreter.boolean_object import false

        return false

    def is_block(self) -> SolObject:
        """Evaluates if object is block"""
        from interpreter.boolean_object import false

        return false

    def is_nil(self) -> SolObject:
        """Evaluates if object is nil"""
        from interpreter.boolean_object import false

        return false

    def is_boolean(self) -> SolObject:
        """Evaluates if object is boolean"""
        from interpreter.boolean_object import false

        return false
