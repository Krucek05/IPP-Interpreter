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

            # Handle built-in classes with special instantiation
            if class_name == "Nil":
                from interpreter.nil_object import nil

                return nil
            if class_name == "Integer":
                from interpreter.integer_object import IntegerObject

                return IntegerObject(0)
            if class_name == "String":
                from interpreter.string_object import StringObject

                return StringObject("")
            if class_name == "Block":
                from interpreter.block_object import BlockObject
                from interpreter.input_model import Block

                empty_block = Block(arity=0, parameters=[], assigns=[])
                return BlockObject(empty_block)
            return SolObject(class_name, None)

        return self

    def sol_from(self, obj: SolObject) -> SolObject:
        """Class message 'from:' — creates a new instance and shallow-copies
        all instance attributes from obj into it.
        """

        if self.class_name == "class":
            class_name = str(self.value)

            if class_name == "Integer":
                from interpreter.integer_object import IntegerObject

                int_instance: SolObject = IntegerObject(0)
                return int_instance.sol_from(obj)
            if class_name == "String":
                from interpreter.string_object import StringObject

                str_instance: SolObject = StringObject("")
                return str_instance.sol_from(obj)
            if class_name == "Nil":
                from interpreter.nil_object import nil

                return nil
            if class_name == "Block":
                from interpreter.block_object import BlockObject
                from interpreter.input_model import Block

                empty_block = Block(arity=0, parameters=[], assigns=[])
                return BlockObject(empty_block)
            new_obj = SolObject(class_name, None)
            new_obj.instance_vars = obj.instance_vars.copy()
            return new_obj

        return self

    def new_instance(self, class_name: str, value: object = None) -> SolObject:
        """Creates new instance of class with given name and value"""
        return SolObject(class_name, value)

    def as_string(self) -> SolObject:
        """Returns string representation of object"""
        from interpreter.string_object import StringObject

        return StringObject("")

    def identical_to(self, other: SolObject) -> bool:
        """Evaluates if two objects are identical"""
        return self is other

    def equal_to(self, other: SolObject) -> SolObject:
        """Evaluates if two objects are equal (have the same value)"""
        from interpreter.boolean_object import false, true

        if not self.instance_vars:
            return true if self.identical_to(other) else false

        if set(self.instance_vars.keys()) != set(other.instance_vars.keys()):
            return false

        for key in self.instance_vars:
            other_result = self.instance_vars[key].equal_to(other.instance_vars[key])
            from interpreter.boolean_object import TrueObject

            if not isinstance(other_result, TrueObject):
                return false

        return true

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
