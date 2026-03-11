"""Unit tests for the print message in the SOL26 interpreter."""

import sys
from io import StringIO

import pytest
from lxml import etree

sys.path.insert(0, "src")

from interpreter.error_codes import ErrorCode
from interpreter.exceptions import InterpreterError
from interpreter.input_model import Program
from interpreter.interpreter import Interpreter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_xml(body: str) -> str:
    """Wrap a block body inside a minimal Main.run XML program."""
    return f"""\
<?xml version="1.0" encoding="UTF-8"?>
<program language="SOL26">
  <class name="Main" parent="Object">
    <method selector="run">
      <block arity="0">
        {body}
      </block>
    </method>
  </class>
</program>"""


def _run(xml: str, stdin: str = "") -> str:
    """Parse the given XML string, run the interpreter, return captured stdout."""
    interp = Interpreter()
    interp.current_program = Program.from_xml_tree(etree.fromstring(xml.encode()))  # type: ignore
    interp.check_main()

    captured = StringIO()
    sys.stdout = captured
    try:
        interp.execute(StringIO(stdin))
    finally:
        sys.stdout = sys.__stdout__

    return captured.getvalue()


def _assign(order: int, var: str, expr_inner: str) -> str:
    return f"""
    <assign order="{order}">
      <var name="{var}"/>
      <expr>{expr_inner}</expr>
    </assign>"""


def _str_literal(value: str) -> str:
    return f'<literal class="String" value="{value}"/>'


def _int_literal(value: int) -> str:
    return f'<literal class="Integer" value="{value}"/>'


def _send_print(expr_inner: str) -> str:
    return f'<send selector="print"><expr>{expr_inner}</expr></send>'


# ---------------------------------------------------------------------------
# Basic string printing
# ---------------------------------------------------------------------------

class TestPrintString:
    def test_print_simple_string(self):
        xml = _make_xml(_assign(1, "_", _send_print(_str_literal("hello"))))
        assert _run(xml) == "hello\n"

    def test_print_empty_string(self):
        xml = _make_xml(_assign(1, "_", _send_print(_str_literal(""))))
        assert _run(xml) == "\n"

    def test_print_string_with_spaces(self):
        xml = _make_xml(_assign(1, "_", _send_print(_str_literal("hello world"))))
        assert _run(xml) == "hello world\n"

    def test_print_numeric_string(self):
        """A string whose content looks like a number should print as-is."""
        xml = _make_xml(_assign(1, "_", _send_print(_str_literal("42"))))
        assert _run(xml) == "42\n"

    def test_print_zero_string(self):
        xml = _make_xml(_assign(1, "_", _send_print(_str_literal("0"))))
        assert _run(xml) == "0\n"

    def test_print_negative_number_string(self):
        xml = _make_xml(_assign(1, "_", _send_print(_str_literal("-7"))))
        assert _run(xml) == "-7\n"

    def test_print_string_with_special_chars(self):
        xml = _make_xml(_assign(1, "_", _send_print(_str_literal("!@#$%"))))
        assert _run(xml) == "!@#$%\n"

    def test_print_multiple_strings_in_order(self):
        body = (
            _assign(1, "_", _send_print(_str_literal("first")))
            + _assign(2, "_", _send_print(_str_literal("second")))
            + _assign(3, "_", _send_print(_str_literal("third")))
        )
        xml = _make_xml(body)
        assert _run(xml) == "first\nsecond\nthird\n"

    def test_print_stored_string_variable(self):
        """Assign a string to a variable, then print it."""
        body = (
            _assign(1, "x", _str_literal("stored"))
            + _assign(2, "_", _send_print("<var name=\"x\"/>"))
        )
        xml = _make_xml(body)
        assert _run(xml) == "stored\n"

    def test_print_returns_receiver(self):
        """print returns the receiver (StringObject), so result can be stored."""
        body = (
            _assign(1, "x", _send_print(_str_literal("side-effect")))
            + _assign(2, "_", _send_print("<var name=\"x\"/>"))
        )
        xml = _make_xml(body)
        assert _run(xml) == "side-effect\nside-effect\n"


# ---------------------------------------------------------------------------
# Printing integers — must raise SEM_ARITY (print is String-only)
# ---------------------------------------------------------------------------

class TestPrintInteger:
    def test_print_integer_raises_sem_arity(self):
        xml = _make_xml(_assign(1, "_", _send_print(_int_literal(42))))
        with pytest.raises(InterpreterError) as exc_info:
            _run(xml)
        assert exc_info.value.error_code == ErrorCode.SEM_ARITY

    def test_print_zero_integer_raises_sem_arity(self):
        xml = _make_xml(_assign(1, "_", _send_print(_int_literal(0))))
        with pytest.raises(InterpreterError) as exc_info:
            _run(xml)
        assert exc_info.value.error_code == ErrorCode.SEM_ARITY

    def test_print_negative_integer_raises_sem_arity(self):
        xml = _make_xml(_assign(1, "_", _send_print(_int_literal(-1))))
        with pytest.raises(InterpreterError) as exc_info:
            _run(xml)
        assert exc_info.value.error_code == ErrorCode.SEM_ARITY


# ---------------------------------------------------------------------------
# asString — converts objects to their String representation
# _ := (y asString) print.
# ---------------------------------------------------------------------------

def _send_as_string(expr_inner: str) -> str:
    return f'<send selector="asString"><expr>{expr_inner}</expr></send>'


class TestAsString:
    """
    asString is a unary message understood by Integer, String, True, False, Nil.
    It returns a StringObject so print can be called on the result.
    """

    def test_integer_as_string_print(self):
        """(42 asString) print  →  '42'"""
        xml = _make_xml(_assign(1, "_", _send_print(_send_as_string(_int_literal(42)))))
        assert _run(xml) == "42\n"

    def test_zero_as_string_print(self):
        """(0 asString) print  →  '0'"""
        xml = _make_xml(_assign(1, "_", _send_print(_send_as_string(_int_literal(0)))))
        assert _run(xml) == "0\n"

    def test_negative_integer_as_string_print(self):
        """(-7 asString) print  →  '-7'"""
        xml = _make_xml(_assign(1, "_", _send_print(_send_as_string(_int_literal(-7)))))
        assert _run(xml) == "-7\n"

    def test_integer_variable_as_string_print(self):
        """Store Integer in variable, then (y asString) print."""
        body = (
            _assign(1, "y", _int_literal(99))
            + _assign(2, "_", _send_print(_send_as_string('<var name="y"/>')))
        )
        xml = _make_xml(body)
        assert _run(xml) == "99\n"


# ---------------------------------------------------------------------------
# Additional helpers for multi-class programs and general sends
# ---------------------------------------------------------------------------

def _var(name: str) -> str:
    return f'<var name="{name}"/>'


def _nil_literal() -> str:
    return '<literal class="Nil" value="nil"/>'


def _true_literal() -> str:
    return '<literal class="True" value="true"/>'


def _false_literal() -> str:
    return '<literal class="False" value="false"/>'


def _class_literal(name: str) -> str:
    return f'<literal class="class" value="{name}"/>'


def _send_msg(selector: str, receiver: str, *args: str) -> str:
    """Build a <send> element. receiver/args are inner XML — each arg is auto-wrapped in <arg><expr>."""
    args_xml = "".join(
        f'<arg order="{i + 1}"><expr>{a}</expr></arg>' for i, a in enumerate(args)
    )
    return f'<send selector="{selector}"><expr>{receiver}</expr>{args_xml}</send>'


def _block(arity: int, params: list, *assigns: str) -> str:
    """Build a <block> element with optional parameters and assign statements."""
    params_xml = "".join(
        f'<parameter order="{i + 1}" name="{p}"/>' for i, p in enumerate(params)
    )
    return f'<block arity="{arity}">{params_xml}{"".join(assigns)}</block>'


def _make_xml_multiclass(classes_xml: str) -> str:
    """Wrap multiple <class> elements in a full program."""
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<program language="SOL26">\n{classes_xml}\n</program>'


def _make_main_with_methods(extra_methods_xml: str, run_body: str) -> str:
    """Main class that has additional methods besides run."""
    return f"""\
<?xml version="1.0" encoding="UTF-8"?>
<program language="SOL26">
  <class name="Main" parent="Object">
    <method selector="run">
      <block arity="0">
        {run_body}
      </block>
    </method>
    {extra_methods_xml}
  </class>
</program>"""


# ---------------------------------------------------------------------------
# Block literals — [ :x | ... ]   b value   b value: arg
# Exercises: example 1 (b value: 16), example 3 (B passes block arg), example 9
# ---------------------------------------------------------------------------

class TestBlockLiterals:
    @pytest.mark.xfail(reason="block value: not yet implemented")
    def test_block_value_with_string_arg_prints_arg(self):
        """b := [ :x | _ := x print. ]. _ := b value: 'hello'.  →  hello"""
        blk = _block(1, ["x"], _assign(1, "_", _send_print(_var("x"))))
        body = (
            _assign(1, "b", blk)
            + _assign(2, "_", _send_msg("value:", _var("b"), _str_literal("hello")))
        )
        xml = _make_xml(body)
        assert _run(xml) == "hello\n"

    @pytest.mark.xfail(reason="block value not yet implemented")
    def test_block_nullary_value(self):
        """b := [| _ := 'in-block' print. ]. _ := b value.  →  in-block"""
        blk = _block(0, [], _assign(1, "_", _send_print(_str_literal("in-block"))))
        body = (
            _assign(1, "b", blk)
            + _assign(2, "_", _send_msg("value", _var("b")))
        )
        xml = _make_xml(body)
        assert _run(xml) == "in-block\n"

    @pytest.mark.xfail(reason="block value: / asString not yet implemented")
    def test_block_ignores_param_returns_last_expr(self):
        """b := [ :x | _ := 42. ]. c := b value: 16.  c = 42 (example 1)."""
        blk = _block(1, ["x"], _assign(1, "_", _int_literal(42)))
        body = (
            _assign(1, "b", blk)
            + _assign(2, "c", _send_msg("value:", _var("b"), _int_literal(16)))
            + _assign(3, "_", _send_print(_send_as_string(_var("c"))))
        )
        xml = _make_xml(body)
        assert _run(xml) == "42\n"

    @pytest.mark.xfail(reason="block value: not yet implemented")
    def test_block_called_multiple_times_with_different_args(self):
        """Same block [ :x | x print ] evaluated twice with different args."""
        blk = _block(1, ["x"], _assign(1, "_", _send_print(_var("x"))))
        body = (
            _assign(1, "b", blk)
            + _assign(2, "_", _send_msg("value:", _var("b"), _str_literal("first")))
            + _assign(3, "_", _send_msg("value:", _var("b"), _str_literal("second")))
        )
        xml = _make_xml(body)
        assert _run(xml) == "first\nsecond\n"

    @pytest.mark.xfail(reason="block passed as argument not yet implemented")
    def test_block_passed_as_method_argument(self):
        """Pass block to a method; method calls value: on it. (example 2 pattern)."""
        xml = _make_main_with_methods(
            extra_methods_xml="""
            <method selector="applyWith:">
              <block arity="1">
                <parameter order="1" name="b"/>
                <assign order="1">
                  <var name="r"/>
                  <expr>
                    <send selector="value:">
                      <expr><var name="b"/></expr>
                      <arg order="1"><expr><literal class="String" value="applied"/></expr></arg>
                    </send>
                  </expr>
                </assign>
              </block>
            </method>""",
            run_body="""
            <assign order="1">
              <var name="b"/>
              <expr>
                <block arity="1">
                  <parameter order="1" name="x"/>
                  <assign order="1">
                    <var name="_"/>
                    <expr><send selector="print"><expr><var name="x"/></expr></send></expr>
                  </assign>
                </block>
              </expr>
            </assign>
            <assign order="2">
              <var name="_"/>
              <expr>
                <send selector="applyWith:">
                  <expr><var name="self"/></expr>
                  <arg order="1"><expr><var name="b"/></expr></arg>
                </send>
              </expr>
            </assign>""",
        )
        assert _run(xml) == "applied\n"

    @pytest.mark.xfail(reason="blocks as arguments / value:value: not yet implemented")
    def test_blocks_nested_value(self):
        """
        b1 := [ | a := String read. _ := a print. ].
        b2 := [ :x | _ := x plus: 1. ].
        b3 := [ :x:y | val := x value: y. ].
        _ := b1 value.          -- reads stdin, prints it
        c := b3 value: b2 value: 3.   -- c = b2 value: 3 = 3+1 = 4
        """
        b1 = _block(0, [],
            _assign(1, "a", _send_msg("read", _str_literal(""))),
            _assign(2, "_", _send_print(_var("a")))
        )
        b2 = _block(1, ["x"],
            _assign(1, "_", _send_msg("plus:", _var("x"), _int_literal(1)))
        )
        b3 = _block(2, ["x", "y"],
            _assign(1, "val", _send_msg("value:", _var("x"), _var("y")))
        )
        body = (
            _assign(1, "b1", b1)
            + _assign(2, "b2", b2)
            + _assign(3, "b3", b3)
            + _assign(4, "_", _send_msg("value", _var("b1")))
            + _assign(5, "c", _send_msg("value:value:", _var("b3"), _var("b2"), _int_literal(3)))
        )
        xml = _make_xml(body)
        assert _run(xml, stdin="hello\n") == "hello\n"


# ---------------------------------------------------------------------------
# User-defined method dispatch — self foo:, plusOne:, compute:and:and:
# Exercises: example 1 (foo:), example 8 (plusOne:, compute:and:and:)
# ---------------------------------------------------------------------------

class TestUserDefinedMethods:
    @pytest.mark.xfail(reason="user-defined unary method dispatch not yet implemented")
    def test_unary_method_returns_string(self):
        """Main has unary method 'greet' returning 'hi'. self greet prints it."""
        xml = _make_main_with_methods(
            extra_methods_xml="""
            <method selector="greet">
              <block arity="0">
                <assign order="1">
                  <var name="_"/>
                  <expr><literal class="String" value="hi"/></expr>
                </assign>
              </block>
            </method>""",
            run_body="""
            <assign order="1">
              <var name="r"/>
              <expr><send selector="greet"><expr><var name="self"/></expr></send></expr>
            </assign>
            <assign order="2">
              <var name="_"/>
              <expr><send selector="print"><expr><var name="r"/></expr></send></expr>
            </assign>""",
        )
        assert _run(xml) == "hi\n"

    @pytest.mark.xfail(reason="user-defined keyword method / plus: not yet implemented")
    def test_foo_keyword_method_plus_10(self):
        """foo: [ :x | u := x plus: 10. ]  then  a := self foo: 4.  a = 14. (example 1)"""
        xml = _make_main_with_methods(
            extra_methods_xml="""
            <method selector="foo:">
              <block arity="1">
                <parameter order="1" name="x"/>
                <assign order="1">
                  <var name="u"/>
                  <expr>
                    <send selector="plus:">
                      <expr><var name="x"/></expr>
                      <arg order="1"><expr><literal class="Integer" value="10"/></expr></arg>
                    </send>
                  </expr>
                </assign>
              </block>
            </method>""",
            run_body="""
            <assign order="1">
              <var name="a"/>
              <expr>
                <send selector="foo:">
                  <expr><var name="self"/></expr>
                  <arg order="1"><expr><literal class="Integer" value="4"/></expr></arg>
                </send>
              </expr>
            </assign>
            <assign order="2">
              <var name="_"/>
              <expr>
                <send selector="print">
                  <expr><send selector="asString"><expr><var name="a"/></expr></send></expr>
                </send>
              </expr>
            </assign>""",
        )
        assert _run(xml) == "14\n"

    @pytest.mark.xfail(reason="user-defined method / plus: not yet implemented")
    def test_plus_one_method(self):
        """plusOne: [ :x | r := x plus: 1. ]  called with 5  →  6. (example 8)"""
        xml = _make_main_with_methods(
            extra_methods_xml="""
            <method selector="plusOne:">
              <block arity="1">
                <parameter order="1" name="x"/>
                <assign order="1">
                  <var name="r"/>
                  <expr>
                    <send selector="plus:">
                      <expr><var name="x"/></expr>
                      <arg order="1"><expr><literal class="Integer" value="1"/></expr></arg>
                    </send>
                  </expr>
                </assign>
              </block>
            </method>""",
            run_body="""
            <assign order="1">
              <var name="r"/>
              <expr>
                <send selector="plusOne:">
                  <expr><var name="self"/></expr>
                  <arg order="1"><expr><literal class="Integer" value="5"/></expr></arg>
                </send>
              </expr>
            </assign>
            <assign order="2">
              <var name="_"/>
              <expr>
                <send selector="print">
                  <expr><send selector="asString"><expr><var name="r"/></expr></send></expr>
                </send>
              </expr>
            </assign>""",
        )
        assert _run(xml) == "6\n"

    @pytest.mark.xfail(reason="multi-keyword selectors / plus: not yet implemented")
    def test_multi_keyword_selector_compute_and_and(self):
        """compute:and:and: with 3 params (example 8) — result of x plus: y."""
        xml = _make_main_with_methods(
            extra_methods_xml="""
            <method selector="compute:and:and:">
              <block arity="3">
                <parameter order="1" name="x"/>
                <parameter order="2" name="y"/>
                <parameter order="3" name="z"/>
                <assign order="1">
                  <var name="a"/>
                  <expr>
                    <send selector="plus:">
                      <expr><var name="x"/></expr>
                      <arg order="1"><expr><var name="y"/></expr></arg>
                    </send>
                  </expr>
                </assign>
              </block>
            </method>""",
            run_body="""
            <assign order="1">
              <var name="x"/>
              <expr>
                <send selector="compute:and:and:">
                  <expr><var name="self"/></expr>
                  <arg order="1"><expr><literal class="Integer" value="3"/></expr></arg>
                  <arg order="2"><expr><literal class="Integer" value="2"/></expr></arg>
                  <arg order="3"><expr><literal class="Integer" value="5"/></expr></arg>
                </send>
              </expr>
            </assign>
            <assign order="2">
              <var name="_"/>
              <expr>
                <send selector="print">
                  <expr><send selector="asString"><expr><var name="x"/></expr></send></expr>
                </send>
              </expr>
            </assign>""",
        )
        assert _run(xml) == "5\n"


# ---------------------------------------------------------------------------
# Instance attributes — self attr:  /  self attr
# Exercises: example 2 (self attr: arg), example 5, example 6
# ---------------------------------------------------------------------------

class TestInstanceAttributes:
    @pytest.mark.xfail(reason="instance attributes via self not yet implemented")
    def test_set_then_get_instance_attr(self):
        """r := self value: 10.  _ := (self value) asString print.  →  10. (example 5)"""
        body = """
        <assign order="1">
          <var name="r"/>
          <expr>
            <send selector="value:">
              <expr><var name="self"/></expr>
              <arg order="1"><expr><literal class="Integer" value="10"/></expr></arg>
            </send>
          </expr>
        </assign>
        <assign order="2">
          <var name="_"/>
          <expr>
            <send selector="print">
              <expr>
                <send selector="asString">
                  <expr>
                    <send selector="value"><expr><var name="self"/></expr></send>
                  </expr>
                </send>
              </expr>
            </send>
          </expr>
        </assign>"""
        xml = _make_xml(body)
        assert _run(xml) == "10\n"

    @pytest.mark.xfail(reason="instance attribute overwrite not yet implemented")
    def test_overwrite_attr_with_nil(self):
        """self value: 10  then  self value: nil  →  reading it gives nil. (example 5)"""
        body = """
        <assign order="1">
          <var name="r"/>
          <expr>
            <send selector="value:"><expr><var name="self"/></expr>
              <arg order="1"><expr><literal class="Integer" value="10"/></expr></arg>
            </send>
          </expr>
        </assign>
        <assign order="2">
          <var name="t"/>
          <expr>
            <send selector="value:"><expr><var name="self"/></expr>
              <arg order="1"><expr><literal class="Nil" value="nil"/></expr></arg>
            </send>
          </expr>
        </assign>
        <assign order="3">
          <var name="_"/>
          <expr>
            <send selector="print">
              <expr>
                <send selector="asString">
                  <expr><send selector="value"><expr><var name="self"/></expr></send></expr>
                </send>
              </expr>
            </send>
          </expr>
        </assign>"""
        xml = _make_xml(body)
        assert _run(xml) == "nil\n"

    @pytest.mark.xfail(reason="instance-attr/method collision detection not yet implemented")
    def test_attr_colides_with_method_raises_int_inst_attr(self):
        """self foo: 10 where foo is a method → INT_INST_ATTR (54). (example 5)"""
        xml = _make_main_with_methods(
            extra_methods_xml="""
            <method selector="foo">
              <block arity="0">
                <assign order="1"><var name="_"/><expr><literal class="Nil" value="nil"/></expr></assign>
              </block>
            </method>""",
            run_body="""
            <assign order="1">
              <var name="_"/>
              <expr>
                <send selector="foo:">
                  <expr><var name="self"/></expr>
                  <arg order="1"><expr><literal class="Integer" value="10"/></expr></arg>
                </send>
              </expr>
            </assign>""",
        )
        with pytest.raises(InterpreterError) as exc_info:
            _run(xml)
        assert exc_info.value.error_code == ErrorCode.INT_INST_ATTR

    @pytest.mark.xfail(reason="instance attributes via self not yet implemented")
    def test_block_closure_stores_self_ref(self):
        """Block captures self; after calling, self attr is set. (example 2 pattern)"""
        # b := [ :arg | y := self myAttr: arg. ].  _ := b value: 'foo'.
        # Then _ := (self myAttr) print.  → foo
        blk = _block(
            1, ["arg"],
            _assign(1, "y", _send_msg("myAttr:", _var("self"), _var("arg"))),
        )
        body = (
            _assign(1, "b", blk)
            + _assign(2, "_", _send_msg("value:", _var("b"), _str_literal("foo")))
            + _assign(3, "_", _send_print(_send_msg("myAttr", _var("self"))))
        )
        xml = _make_xml(body)
        assert _run(xml) == "foo\n"


# ---------------------------------------------------------------------------
# new — creating instances of classes
# Exercises: example 2 (A new), example 3 (C new)
# ---------------------------------------------------------------------------

class TestNew:
    @pytest.mark.xfail(reason="new message / class instantiation not yet implemented")
    def test_new_creates_instance_and_calls_method(self):
        """a := A new.  _ := a greet print.  →  hello (example 2 pattern)"""
        xml = _make_xml_multiclass("""
  <class name="A" parent="Object">
    <method selector="greet">
      <block arity="0">
        <assign order="1">
          <var name="_"/>
          <expr><literal class="String" value="hello from A"/></expr>
        </assign>
      </block>
    </method>
  </class>
  <class name="Main" parent="Object">
    <method selector="run">
      <block arity="0">
        <assign order="1">
          <var name="a"/>
          <expr><send selector="new"><expr><literal class="class" value="A"/></expr></send></expr>
        </assign>
        <assign order="2">
          <var name="r"/>
          <expr><send selector="greet"><expr><var name="a"/></expr></send></expr>
        </assign>
        <assign order="3">
          <var name="_"/>
          <expr><send selector="print"><expr><var name="r"/></expr></send></expr>
        </assign>
      </block>
    </method>
  </class>""")
        assert _run(xml) == "hello from A\n"

    @pytest.mark.xfail(reason="undefined class detection not yet implemented")
    def test_new_undefined_class_raises_sem_undef(self):
        """Undefined new → SEM_UNDEF (32)."""
        body = _assign(1, "a", _send_msg("new", _class_literal("Undefined")))
        xml = _make_xml(body)
        with pytest.raises(InterpreterError) as exc_info:
            _run(xml)
        assert exc_info.value.error_code == ErrorCode.SEM_UNDEF

    @pytest.mark.xfail(reason="DNU not yet implemented")
    def test_unknown_selector_raises_int_dnu(self):
        """Sending unknown message to string → INT_DNU (51)."""
        body = _assign(1, "_", _send_msg("unknownMsgXyz", _str_literal("hi")))
        xml = _make_xml(body)
        with pytest.raises(InterpreterError) as exc_info:
            _run(xml)
        assert exc_info.value.error_code == ErrorCode.INT_DNU


# ---------------------------------------------------------------------------
# Inheritance — class B : A, method lookup chain
# Exercises: example 3 (A, B, C hierarchy)
# ---------------------------------------------------------------------------

class TestInheritanceChain:
    @pytest.mark.xfail(reason="inheritance / method lookup not yet implemented")
    def test_subclass_inherits_unary_method(self):
        """B inherits 'm:' from A. (b m: 'hello') prints 'hello'."""
        xml = _make_xml_multiclass("""
  <class name="A" parent="Object">
    <method selector="m:">
      <block arity="1">
        <parameter order="1" name="x"/>
        <assign order="1">
          <var name="_"/>
          <expr><send selector="print"><expr><var name="x"/></expr></send></expr>
        </assign>
      </block>
    </method>
  </class>
  <class name="B" parent="A"/>
  <class name="Main" parent="Object">
    <method selector="run">
      <block arity="0">
        <assign order="1">
          <var name="b"/>
          <expr><send selector="new"><expr><literal class="class" value="B"/></expr></send></expr>
        </assign>
        <assign order="2">
          <var name="_"/>
          <expr>
            <send selector="m:">
              <expr><var name="b"/></expr>
              <arg order="1"><expr><literal class="String" value="hello"/></expr></arg>
            </send>
          </expr>
        </assign>
      </block>
    </method>
  </class>""")
        assert _run(xml) == "hello\n"

    @pytest.mark.xfail(reason="method override not yet implemented")
    def test_subclass_overrides_method_uses_own_version(self):
        """B overrides 'm:'. b m: x uses B's version, not A's. (example 3)"""
        xml = _make_xml_multiclass("""
  <class name="A" parent="Object">
    <method selector="m:">
      <block arity="1">
        <parameter order="1" name="x"/>
        <assign order="1">
          <var name="_"/>
          <expr><send selector="print"><expr><literal class="String" value="from-A"/></expr></send></expr>
        </assign>
      </block>
    </method>
  </class>
  <class name="B" parent="A">
    <method selector="m:">
      <block arity="1">
        <parameter order="1" name="x"/>
        <assign order="1">
          <var name="_"/>
          <expr><send selector="print"><expr><literal class="String" value="from-B"/></expr></send></expr>
        </assign>
      </block>
    </method>
  </class>
  <class name="Main" parent="Object">
    <method selector="run">
      <block arity="0">
        <assign order="1">
          <var name="b"/>
          <expr><send selector="new"><expr><literal class="class" value="B"/></expr></send></expr>
        </assign>
        <assign order="2">
          <var name="_"/>
          <expr>
            <send selector="m:">
              <expr><var name="b"/></expr>
              <arg order="1"><expr><literal class="String" value="ignored"/></expr></arg>
            </send>
          </expr>
        </assign>
      </block>
    </method>
  </class>""")
        assert _run(xml) == "from-B\n"

    @pytest.mark.xfail(reason="3-level inheritance dispatch not yet implemented")
    def test_three_level_inheritance_c_m_foo(self):
        """c m: 'foo'  →  B.m: calls A.m:('ahoj') then prints 'foo'. (example 3)"""
        # Expected output: ahoj\nfoo\n
        xml = _make_xml_multiclass("""
  <class name="A" parent="Object">
    <method selector="m:">
      <block arity="1">
        <parameter order="1" name="x"/>
        <assign order="1">
          <var name="_"/>
          <expr><send selector="print"><expr><var name="x"/></expr></send></expr>
        </assign>
      </block>
    </method>
    <method selector="r">
      <block arity="0">
        <assign order="1">
          <var name="_"/>
          <expr><send selector="print"><expr><var name="self"/></expr></send></expr>
        </assign>
      </block>
    </method>
  </class>
  <class name="B" parent="A">
    <method selector="m:">
      <block arity="1">
        <parameter order="1" name="x"/>
        <assign order="1">
          <var name="_"/>
          <expr>
            <send selector="m:">
              <expr><var name="super"/></expr>
              <arg order="1"><expr><literal class="String" value="ahoj"/></expr></arg>
            </send>
          </expr>
        </assign>
        <assign order="2">
          <var name="_"/>
          <expr><send selector="print"><expr><var name="x"/></expr></send></expr>
        </assign>
      </block>
    </method>
  </class>
  <class name="C" parent="B">
    <method selector="u">
      <block arity="0">
        <assign order="1">
          <var name="_"/>
          <expr>
            <send selector="m:">
              <expr><var name="self"/></expr>
              <arg order="1"><expr><var name="super"/></expr></arg>
            </send>
          </expr>
        </assign>
      </block>
    </method>
    <method selector="print">
      <block arity="0">
        <assign order="1">
          <var name="_"/>
          <expr><send selector="print"><expr><literal class="String" value="bar"/></expr></send></expr>
        </assign>
      </block>
    </method>
  </class>
  <class name="Main" parent="Object">
    <method selector="run">
      <block arity="0">
        <assign order="1">
          <var name="c"/>
          <expr><send selector="new"><expr><literal class="class" value="C"/></expr></send></expr>
        </assign>
        <assign order="2">
          <var name="_"/>
          <expr>
            <send selector="m:">
              <expr><var name="c"/></expr>
              <arg order="1"><expr><literal class="String" value="foo"/></expr></arg>
            </send>
          </expr>
        </assign>
        <assign order="3">
          <var name="_"/>
          <expr><send selector="u"><expr><var name="c"/></expr></send></expr>
        </assign>
        <assign order="4">
          <var name="_"/>
          <expr><send selector="r"><expr><var name="c"/></expr></send></expr>
        </assign>
      </block>
    </method>
  </class>""")
        # c m: 'foo'  → B.m: → A.m:('ahoj')→prints ahoj, then B prints foo
        # c u         → C.u  → self m: super → B.m: → A.m:('ahoj')→ahoj, super.print→C.print→bar
        # c r         → A.r  → self print where self=C instance → C.print → bar
        assert _run(xml) == "ahoj\nfoo\nahoj\nbar\nbar\n"


# ---------------------------------------------------------------------------
# super keyword — super m:, super as argument, self vs super dispatch
# Exercises: example 3, example 6
# ---------------------------------------------------------------------------

class TestSuperKeyword:
    @pytest.mark.xfail(reason="super keyword not yet implemented")
    def test_super_calls_parent_method(self):
        """B.m: uses super m: 'ahoj' → delegates to A.m: which prints 'ahoj'."""
        xml = _make_xml_multiclass("""
  <class name="A" parent="Object">
    <method selector="m:">
      <block arity="1">
        <parameter order="1" name="x"/>
        <assign order="1">
          <var name="_"/>
          <expr><send selector="print"><expr><var name="x"/></expr></send></expr>
        </assign>
      </block>
    </method>
  </class>
  <class name="B" parent="A">
    <method selector="m:">
      <block arity="1">
        <parameter order="1" name="x"/>
        <assign order="1">
          <var name="_"/>
          <expr>
            <send selector="m:">
              <expr><var name="super"/></expr>
              <arg order="1"><expr><literal class="String" value="ahoj"/></expr></arg>
            </send>
          </expr>
        </assign>
        <assign order="2">
          <var name="_"/>
          <expr><send selector="print"><expr><var name="x"/></expr></send></expr>
        </assign>
      </block>
    </method>
  </class>
  <class name="Main" parent="Object">
    <method selector="run">
      <block arity="0">
        <assign order="1">
          <var name="b"/>
          <expr><send selector="new"><expr><literal class="class" value="B"/></expr></send></expr>
        </assign>
        <assign order="2">
          <var name="_"/>
          <expr>
            <send selector="m:">
              <expr><var name="b"/></expr>
              <arg order="1"><expr><literal class="String" value="foo"/></expr></arg>
            </send>
          </expr>
        </assign>
      </block>
    </method>
  </class>""")
        assert _run(xml) == "ahoj\nfoo\n"

    @pytest.mark.xfail(reason="super as argument / dynamic dispatch not yet implemented")
    def test_self_method_dispatch_same_as_super_value(self):
        """super value: super / super value: self both equivalent. (example 6)"""
        # a := super value: super.  b := super value: self.
        # c := self value: super.  d := self value: self.
        # In Main, super is the Parent instance context; all four should behave alike.
        xml = _make_xml_multiclass("""
  <class name="Parent" parent="Object">
    <method selector="value:">
      <block arity="1">
        <parameter order="1" name="x"/>
        <assign order="1">
          <var name="_"/>
          <expr><send selector="print"><expr><literal class="String" value="ok"/></expr></send></expr>
        </assign>
      </block>
    </method>
  </class>
  <class name="Main" parent="Parent">
    <method selector="run">
      <block arity="0">
        <assign order="1">
          <var name="a"/>
          <expr>
            <send selector="value:">
              <expr><var name="super"/></expr>
              <arg order="1"><expr><var name="super"/></expr></arg>
            </send>
          </expr>
        </assign>
        <assign order="2">
          <var name="b"/>
          <expr>
            <send selector="value:">
              <expr><var name="super"/></expr>
              <arg order="1"><expr><var name="self"/></expr></arg>
            </send>
          </expr>
        </assign>
      </block>
    </method>
  </class>""")
        assert _run(xml) == "ok\nok\n"


# ---------------------------------------------------------------------------
# Arithmetic — plus:, multiplyBy:, equalTo:, greaterThan:
# Exercises: example 1 (plus:), example 7 (multiplyBy:, equalTo:), example 8 (greaterThan:)
# ---------------------------------------------------------------------------

class TestArithmetic:
    @pytest.mark.xfail(reason="plus: not yet implemented")
    def test_integer_plus(self):
        """4 plus: 10  →  14."""
        body = _assign(1, "_", _send_print(_send_as_string(_send_msg("plus:", _int_literal(4), _int_literal(10)))))
        xml = _make_xml(body)
        assert _run(xml) == "14\n"

    @pytest.mark.xfail(reason="plus: not yet implemented")
    def test_plus_with_negative(self):
        """5 plus: -1  →  4."""
        body = _assign(1, "_", _send_print(_send_as_string(_send_msg("plus:", _int_literal(5), _int_literal(-1)))))
        xml = _make_xml(body)
        assert _run(xml) == "4\n"

    @pytest.mark.xfail(reason="multiplyBy: not yet implemented")
    def test_integer_multiply(self):
        """3 multiplyBy: 4  →  12."""
        body = _assign(1, "_", _send_print(_send_as_string(_send_msg("multiplyBy:", _int_literal(3), _int_literal(4)))))
        xml = _make_xml(body)
        assert _run(xml) == "12\n"

    @pytest.mark.xfail(reason="equalTo: not yet implemented")
    def test_equal_to_same_values(self):
        """0 equalTo: 0  →  True (asString → 'true')."""
        body = _assign(1, "_", _send_print(_send_as_string(_send_msg("equalTo:", _int_literal(0), _int_literal(0)))))
        xml = _make_xml(body)
        assert _run(xml) == "true\n"

    @pytest.mark.xfail(reason="equalTo: not yet implemented")
    def test_equal_to_different_values(self):
        """1 equalTo: 2  →  False (asString → 'false')."""
        body = _assign(1, "_", _send_print(_send_as_string(_send_msg("equalTo:", _int_literal(1), _int_literal(2)))))
        xml = _make_xml(body)
        assert _run(xml) == "false\n"

    @pytest.mark.xfail(reason="greaterThan: not yet implemented")
    def test_greater_than_true(self):
        """5 greaterThan: 0  →  True."""
        body = _assign(1, "_", _send_print(_send_as_string(_send_msg("greaterThan:", _int_literal(5), _int_literal(0)))))
        xml = _make_xml(body)
        assert _run(xml) == "true\n"

    @pytest.mark.xfail(reason="greaterThan: not yet implemented")
    def test_greater_than_false(self):
        """0 greaterThan: 5  →  False."""
        body = _assign(1, "_", _send_print(_send_as_string(_send_msg("greaterThan:", _int_literal(0), _int_literal(5)))))
        xml = _make_xml(body)
        assert _run(xml) == "false\n"


# ---------------------------------------------------------------------------
# ifTrue:ifFalse: — conditional execution with block arguments
# Exercises: example 7 (factorial condition), example 8 (compute:and:and:)
# ---------------------------------------------------------------------------

class TestConditionals:
    @pytest.mark.xfail(reason="ifTrue:ifFalse: not yet implemented")
    def test_if_true_branch_executes(self):
        """(0 equalTo: 0) ifTrue: [| _ := 'yes' print.] ifFalse: [|].  →  yes"""
        body = """
        <assign order="1">
          <var name="_"/>
          <expr>
            <send selector="ifTrue:ifFalse:">
              <expr>
                <send selector="equalTo:">
                  <expr><literal class="Integer" value="0"/></expr>
                  <arg order="1"><expr><literal class="Integer" value="0"/></expr></arg>
                </send>
              </expr>
              <arg order="1">
                <expr>
                  <block arity="0">
                    <assign order="1">
                      <var name="_"/>
                      <expr><send selector="print"><expr><literal class="String" value="yes"/></expr></send></expr>
                    </assign>
                  </block>
                </expr>
              </arg>
              <arg order="2">
                <expr><block arity="0"/></expr>
              </arg>
            </send>
          </expr>
        </assign>"""
        xml = _make_xml(body)
        assert _run(xml) == "yes\n"

    @pytest.mark.xfail(reason="ifTrue:ifFalse: not yet implemented")
    def test_if_false_branch_executes(self):
        """(0 equalTo: 1) ifTrue: [|] ifFalse: [| _ := 'no' print.].  →  no"""
        body = """
        <assign order="1">
          <var name="_"/>
          <expr>
            <send selector="ifTrue:ifFalse:">
              <expr>
                <send selector="equalTo:">
                  <expr><literal class="Integer" value="0"/></expr>
                  <arg order="1"><expr><literal class="Integer" value="1"/></expr></arg>
                </send>
              </expr>
              <arg order="1">
                <expr><block arity="0"/></expr>
              </arg>
              <arg order="2">
                <expr>
                  <block arity="0">
                    <assign order="1">
                      <var name="_"/>
                      <expr><send selector="print"><expr><literal class="String" value="no"/></expr></send></expr>
                    </assign>
                  </block>
                </expr>
              </arg>
            </send>
          </expr>
        </assign>"""
        xml = _make_xml(body)
        assert _run(xml) == "no\n"

    @pytest.mark.xfail(reason="greaterThan: / ifTrue:ifFalse: not yet implemented")
    def test_greater_than_drives_conditional(self):
        """(5 greaterThan: 0) ifTrue: [|'pos' print.] ifFalse: [|'neg' print.].  →  pos"""
        body = """
        <assign order="1">
          <var name="_"/>
          <expr>
            <send selector="ifTrue:ifFalse:">
              <expr>
                <send selector="greaterThan:">
                  <expr><literal class="Integer" value="5"/></expr>
                  <arg order="1"><expr><literal class="Integer" value="0"/></expr></arg>
                </send>
              </expr>
              <arg order="1">
                <expr>
                  <block arity="0">
                    <assign order="1">
                      <var name="_"/>
                      <expr><send selector="print"><expr><literal class="String" value="pos"/></expr></send></expr>
                    </assign>
                  </block>
                </expr>
              </arg>
              <arg order="2">
                <expr>
                  <block arity="0">
                    <assign order="1">
                      <var name="_"/>
                      <expr><send selector="print"><expr><literal class="String" value="neg"/></expr></send></expr>
                    </assign>
                  </block>
                </expr>
              </arg>
            </send>
          </expr>
        </assign>"""
        xml = _make_xml(body)
        assert _run(xml) == "pos\n"


# ---------------------------------------------------------------------------
# Integer from: — class-side factory method
# Exercises: example 4 (Integer from: 10), example 7 (Factorial from:)
# ---------------------------------------------------------------------------

class TestIntegerFrom:
    @pytest.mark.xfail(reason="Integer from: not yet implemented")
    def test_integer_from_int_prints_as_string(self):
        """Integer from: 10  →  IntegerObject; asString gives '10'."""
        body = """
        <assign order="1">
          <var name="a"/>
          <expr>
            <send selector="from:">
              <expr><literal class="class" value="Integer"/></expr>
              <arg order="1"><expr><literal class="Integer" value="10"/></expr></arg>
            </send>
          </expr>
        </assign>
        <assign order="2">
          <var name="_"/>
          <expr>
            <send selector="print">
              <expr><send selector="asString"><expr><var name="a"/></expr></send></expr>
            </send>
          </expr>
        </assign>"""
        xml = _make_xml(body)
        assert _run(xml) == "10\n"

    @pytest.mark.xfail(reason="Integer from: type validation not yet implemented")
    def test_integer_from_string_raises_int_invalid_arg(self):
        """Integer from: 'str'  →  INT_INVALID_ARG (53). (example 7)"""
        body = """
        <assign order="1">
          <var name="y"/>
          <expr>
            <send selector="from:">
              <expr><literal class="class" value="Integer"/></expr>
              <arg order="1"><expr><literal class="String" value="str"/></expr></arg>
            </send>
          </expr>
        </assign>"""
        xml = _make_xml(body)
        with pytest.raises(InterpreterError) as exc_info:
            _run(xml)
        assert exc_info.value.error_code == ErrorCode.INT_INVALID_ARG


# ---------------------------------------------------------------------------
# String messages — concatenateWith:, String read, asInteger
# Exercises: example 4, example 7, example 9
# ---------------------------------------------------------------------------

class TestStringMessages:
    @pytest.mark.xfail(reason="concatenateWith: not yet implemented")
    def test_concatenate_two_strings(self):
        """'hello' concatenateWith: ' world'  →  'hello world'. (example 4)"""
        body = _assign(1, "_", _send_print(_send_msg("concatenateWith:", _str_literal("hello"), _str_literal(" world"))))
        xml = _make_xml(body)
        assert _run(xml) == "hello world\n"

    @pytest.mark.xfail(reason="concatenateWith: / asString not yet implemented")
    def test_concatenate_integer_asstring(self):
        """((self attrib) asString) concatenateWith: (10 asString). (example 4 pattern)"""
        body = """
        <assign order="1">
          <var name="x"/>
          <expr>
            <send selector="concatenateWith:">
              <expr>
                <send selector="asString">
                  <expr><literal class="Integer" value="5"/></expr>
                </send>
              </expr>
              <arg order="1">
                <expr>
                  <send selector="asString">
                    <expr><literal class="Integer" value="10"/></expr>
                  </send>
                </expr>
              </arg>
            </send>
          </expr>
        </assign>
        <assign order="2">
          <var name="_"/>
          <expr><send selector="print"><expr><var name="x"/></expr></send></expr>
        </assign>"""
        xml = _make_xml(body)
        assert _run(xml) == "510\n"

    @pytest.mark.xfail(reason="String read not yet implemented")
    def test_string_read_from_stdin(self):
        """String read reads a line from stdin. (example 7, 9)"""
        body = """
        <assign order="1">
          <var name="line"/>
          <expr>
            <send selector="read">
              <expr><literal class="class" value="String"/></expr>
            </send>
          </expr>
        </assign>
        <assign order="2">
          <var name="_"/>
          <expr><send selector="print"><expr><var name="line"/></expr></send></expr>
        </assign>"""
        xml = _make_xml(body)
        assert _run(xml, stdin="hello from stdin\n") == "hello from stdin\n"

    def test_as_integer_then_as_string(self):
        """'42' asInteger  gives IntegerObject(42); asString back → '42'. (example 7)"""
        body = _assign(
            1, "_",
            _send_print(_send_as_string(_send_msg("asInteger", _str_literal("42"))))
        )
        xml = _make_xml(body)
        assert _run(xml) == "42\n"

    @pytest.mark.xfail(reason="asInteger not yet implemented")
    def test_as_integer_then_arithmetic(self):
        """('10' asInteger) plus: 5  →  15."""
        body = _assign(
            1, "_",
            _send_print(_send_as_string(_send_msg("plus:", _send_msg("asInteger", _str_literal("10")), _int_literal(5))))
        )
        xml = _make_xml(body)
        assert _run(xml) == "15\n"


# ---------------------------------------------------------------------------
# Closures — block captures outer variables by reference
# Exercises: example 9 (giveObjectWithBlock, x mutated after block creation)
# ---------------------------------------------------------------------------

class TestClosures:
    @pytest.mark.xfail(reason="closures / block value not yet implemented")
    def test_block_sees_updated_outer_variable(self):
        """x := 1. b := [| ...x... ]. x := 9. b value.  →  block uses x=9. (example 9)"""
        body = """
        <assign order="1">
          <var name="x"/>
          <expr><literal class="Integer" value="1"/></expr>
        </assign>
        <assign order="2">
          <var name="b"/>
          <expr>
            <block arity="0">
              <assign order="1">
                <var name="_"/>
                <expr>
                  <send selector="print">
                    <expr>
                      <send selector="asString"><expr><var name="x"/></expr></send>
                    </expr>
                  </send>
                </expr>
              </assign>
            </block>
          </expr>
        </assign>
        <assign order="3">
          <var name="x"/>
          <expr><literal class="Integer" value="9"/></expr>
        </assign>
        <assign order="4">
          <var name="_"/>
          <expr><send selector="value"><expr><var name="b"/></expr></send></expr>
        </assign>"""
        xml = _make_xml(body)
        # Block closes over x; after x := 9 the block should see 9
        assert _run(xml) == "9\n"

    @pytest.mark.xfail(reason="closures / block value not yet implemented")
    def test_block_evaluated_twice_reads_same_closure_var(self):
        """Block evaluated twice; both reads see the same (latest) x. (example 9 r1/r2)"""
        body = """
        <assign order="1">
          <var name="x"/>
          <expr><literal class="Integer" value="5"/></expr>
        </assign>
        <assign order="2">
          <var name="b"/>
          <expr>
            <block arity="0">
              <assign order="1">
                <var name="_"/>
                <expr>
                  <send selector="print">
                    <expr><send selector="asString"><expr><var name="x"/></expr></send></expr>
                  </send>
                </expr>
              </assign>
            </block>
          </expr>
        </assign>
        <assign order="3">
          <var name="_"/>
          <expr><send selector="value"><expr><var name="b"/></expr></send></expr>
        </assign>
        <assign order="4">
          <var name="_"/>
          <expr><send selector="value"><expr><var name="b"/></expr></send></expr>
        </assign>"""
        xml = _make_xml(body)
        assert _run(xml) == "5\n5\n"

    def test_string_as_string_is_identity(self):
        """('hello' asString) print  →  'hello'  (String asString returns itself)"""
        xml = _make_xml(_assign(1, "_", _send_print(_send_as_string(_str_literal("hello")))))
        assert _run(xml) == "hello\n"

    @pytest.mark.xfail(reason="asString on True/False not yet implemented")
    def test_true_as_string_print(self):
        """(true asString) print  →  'true'"""
        xml = _make_xml(_assign(1, "_", _send_print(
            _send_as_string('<literal class="True" value="true"/>')
        )))
        assert _run(xml) == "true\n"

    @pytest.mark.xfail(reason="asString on True/False not yet implemented")
    def test_false_as_string_print(self):
        """(false asString) print  →  'false'"""
        xml = _make_xml(_assign(1, "_", _send_print(
            _send_as_string('<literal class="False" value="false"/>')
        )))
        assert _run(xml) == "false\n"

    @pytest.mark.xfail(reason="asString on Nil not yet implemented")
    def test_nil_as_string_print(self):
        """(nil asString) print  →  'nil'"""
        xml = _make_xml(_assign(1, "_", _send_print(
            _send_as_string('<literal class="Nil" value="nil"/>')
        )))
        assert _run(xml) == "nil\n"

    @pytest.mark.xfail(reason="asString on Integer not yet implemented")
    def test_as_string_result_is_string_printable(self):
        """asString result can be stored and printed later."""
        body = (
            _assign(1, "s", _send_as_string(_int_literal(123)))
            + _assign(2, "_", _send_print('<var name="s"/>'))
        )
        xml = _make_xml(body)
        assert _run(xml) == "123\n"

    @pytest.mark.xfail(reason="asString chaining not yet implemented")
    def test_chain_as_string_print_multiple(self):
        """Print multiple asString conversions in order."""
        body = (
            _assign(1, "_", _send_print(_send_as_string(_int_literal(1))))
            + _assign(2, "_", _send_print(_send_as_string(_int_literal(2))))
            + _assign(3, "_", _send_print(_send_as_string(_int_literal(3))))
        )
        xml = _make_xml(body)
        assert _run(xml) == "1\n2\n3\n"


# ---------------------------------------------------------------------------
# Static checks — missing Main / run
# ---------------------------------------------------------------------------

class TestStaticChecks:
    def test_missing_main_class(self):
        xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<program language="SOL26">
  <class name="NotMain" parent="Object">
    <method selector="run"><block arity="0"/></method>
  </class>
</program>"""
        interp = Interpreter()
        interp.current_program = Program.from_xml_tree(etree.fromstring(xml.encode()))  # type: ignore
        with pytest.raises(InterpreterError) as exc_info:
            interp.check_main()
        assert exc_info.value.error_code == ErrorCode.SEM_MAIN

    def test_missing_run_method(self):
        xml = """\
<?xml version="1.0" encoding="UTF-8"?>
<program language="SOL26">
  <class name="Main" parent="Object">
    <method selector="other"><block arity="0"/></method>
  </class>
</program>"""
        interp = Interpreter()
        interp.current_program = Program.from_xml_tree(etree.fromstring(xml.encode()))  # type: ignore
        with pytest.raises(InterpreterError) as exc_info:
            interp.check_main()
        assert exc_info.value.error_code == ErrorCode.SEM_MAIN


# ---------------------------------------------------------------------------
# Advanced: keyword messages  (m: with one argument)
# These test class A : Object { m: [ :x | _ := x print. ] }
# ---------------------------------------------------------------------------

# XML building helpers for advanced constructs

def _param(name: str, order: int) -> str:
    return f'<parameter name="{name}" order="{order}"/>'


def _arg(order: int, expr_inner: str) -> str:
    return f'<arg order="{order}"><expr>{expr_inner}</expr></arg>'


def _send(selector: str, receiver_inner: str, *args: str) -> str:
    """Build a <send> with an optional list of <arg> children."""
    args_xml = "".join(args)
    return f'<send selector="{selector}"><expr>{receiver_inner}</expr>{args_xml}</send>'


def _method(selector: str, arity: int, params_xml: str, assigns_xml: str) -> str:
    return f"""
    <method selector="{selector}">
      <block arity="{arity}">
        {params_xml}
        {assigns_xml}
      </block>
    </method>"""


def _class(name: str, parent: str, methods_xml: str) -> str:
    return f'<class name="{name}" parent="{parent}">{methods_xml}</class>'


def _full_xml(*class_defs: str) -> str:
    classes = "\n".join(class_defs)
    return f'<?xml version="1.0" encoding="UTF-8"?><program language="SOL26">{classes}</program>'


class TestKeywordMessage:
    """
    class A : Object { m: [ :x | _ := x print. ] }
    Main.run sends m: with a String argument to an A instance.
    Expected output: the argument string.
    """

    @pytest.mark.xfail(reason="Keyword message dispatch not yet implemented")
    def test_keyword_message_prints_argument(self):
        # A.m: prints its argument x
        class_a = _class("A", "Object", _method(
            "m:", 1,
            _param("x", 1),
            _assign(1, "_", _send("print", '<var name="x"/>')),
        ))
        # Main.run: creates an A instance, sends m: 'hello' to it
        class_literal_a = '<literal class="class" value="A"/>'
        a_new = _send("new", class_literal_a)
        send_m = _send("m:", a_new, _arg(1, _str_literal("hello from m:")))
        class_main = _class("Main", "Object", _method(
            "run", 0, "",
            _assign(1, "_", send_m),
        ))
        xml = _full_xml(class_a, class_main)
        assert _run(xml) == "hello from m:\n"

    @pytest.mark.xfail(reason="Keyword message dispatch not yet implemented")
    def test_keyword_message_with_integer_arg_raises_sem_arity(self):
        """Passing an Integer to m: then calling print on it should raise SEM_ARITY."""
        class_a = _class("A", "Object", _method(
            "m:", 1,
            _param("x", 1),
            _assign(1, "_", _send("print", '<var name="x"/>')),
        ))
        class_literal_a = '<literal class="class" value="A"/>'
        a_new = _send("new", class_literal_a)
        send_m = _send("m:", a_new, _arg(1, _int_literal(99)))
        class_main = _class("Main", "Object", _method(
            "run", 0, "",
            _assign(1, "_", send_m),
        ))
        xml = _full_xml(class_a, class_main)
        with pytest.raises(InterpreterError) as exc_info:
            _run(xml)
        assert exc_info.value.error_code == ErrorCode.SEM_ARITY


# ---------------------------------------------------------------------------
# Advanced: self reference
# class A : Object { r [ | _ := self print. ] }
# If A has no print method and print is String-only → INT_DNU at runtime.
# But if we define print on A, it should call it.
# ---------------------------------------------------------------------------

class TestSelfReference:
    """
    class A : Object {
      r     [ | _ := self print. ]
      print [ | _ := 'I am A' print. ]
    }
    Main.run: (A new) r  →  prints 'I am A'
    """

    @pytest.mark.xfail(reason="self reference / method dispatch not yet implemented")
    def test_self_print_calls_own_print_method(self):
        class_a = _class("A", "Object",
            _method("r", 0, "", _assign(1, "_", _send("print", '<var name="self"/>')))
            + _method("print", 0, "", _assign(1, "_", _send("print", _str_literal("I am A"))))
        )
        class_literal_a = '<literal class="class" value="A"/>'
        a_new = _send("new", class_literal_a)
        class_main = _class("Main", "Object", _method(
            "run", 0, "",
            _assign(1, "_", _send("r", a_new)),
        ))
        xml = _full_xml(class_a, class_main)
        assert _run(xml) == "I am A\n"

    @pytest.mark.xfail(reason="self reference / method dispatch not yet implemented")
    def test_self_message_without_own_method_raises_int_dnu(self):
        """Sending print to self when the class has no print method → INT_DNU."""
        class_a = _class("A", "Object",
            _method("r", 0, "", _assign(1, "_", _send("print", '<var name="self"/>')))
        )
        class_literal_a = '<literal class="class" value="A"/>'
        a_new = _send("new", class_literal_a)
        class_main = _class("Main", "Object", _method(
            "run", 0, "",
            _assign(1, "_", _send("r", a_new)),
        ))
        xml = _full_xml(class_a, class_main)
        with pytest.raises(InterpreterError) as exc_info:
            _run(xml)
        assert exc_info.value.error_code == ErrorCode.INT_DNU


# ---------------------------------------------------------------------------
# Advanced: inheritance
# class B : A inherits m: from A without overriding it
# ---------------------------------------------------------------------------

class TestInheritance:
    """
    class A : Object { m: [ :x | _ := x print. ] }
    class B : A { }   ← no m:, inherits from A
    (B new) m: 'inherited'  →  prints 'inherited'
    """

    @pytest.mark.xfail(reason="Inheritance / method lookup not yet implemented")
    def test_inherited_keyword_method_is_called(self):
        class_a = _class("A", "Object", _method(
            "m:", 1, _param("x", 1),
            _assign(1, "_", _send("print", '<var name="x"/>')),
        ))
        class_b = _class("B", "A", "")  # B inherits A, adds nothing
        class_literal_b = '<literal class="class" value="B"/>'
        b_new = _send("new", class_literal_b)
        send_m = _send("m:", b_new, _arg(1, _str_literal("inherited")))
        class_main = _class("Main", "Object", _method(
            "run", 0, "",
            _assign(1, "_", send_m),
        ))
        xml = _full_xml(class_a, class_b, class_main)
        assert _run(xml) == "inherited\n"

    @pytest.mark.xfail(reason="Inheritance / method lookup not yet implemented")
    def test_subclass_overrides_method(self):
        """B overrides m: — B's version is called, not A's."""
        class_a = _class("A", "Object", _method(
            "m:", 1, _param("x", 1),
            _assign(1, "_", _send("print", _str_literal("from A"))),
        ))
        class_b = _class("B", "A", _method(
            "m:", 1, _param("x", 1),
            _assign(1, "_", _send("print", _str_literal("from B"))),
        ))
        class_literal_b = '<literal class="class" value="B"/>'
        b_new = _send("new", class_literal_b)
        send_m = _send("m:", b_new, _arg(1, _str_literal("ignored")))
        class_main = _class("Main", "Object", _method(
            "run", 0, "",
            _assign(1, "_", send_m),
        ))
        xml = _full_xml(class_a, class_b, class_main)
        assert _run(xml) == "from B\n"


# ---------------------------------------------------------------------------
# Advanced: super
# class B : A { m: [ :x | _ := super m: 'ahoj'. _ := x print. ] }
# super m: 'ahoj'  uses A's m:, prints 'ahoj', then x print prints the argument
# ---------------------------------------------------------------------------

class TestSuperCall:
    """
    class A : Object { m: [ :x | _ := x print. ] }
    class B : A {
      m: [ :x | _ := super m: 'ahoj'. _ := x print. ]
    }
    (B new) m: 'world'  →  prints 'ahoj' then 'world'
    """

    @pytest.mark.xfail(reason="super not yet implemented")
    def test_super_calls_parent_method(self):
        class_a = _class("A", "Object", _method(
            "m:", 1, _param("x", 1),
            _assign(1, "_", _send("print", '<var name="x"/>')),
        ))
        # B.m: first calls super m: 'ahoj' (prints 'ahoj'), then prints x
        super_m_ahoj = _send("m:", '<var name="super"/>', _arg(1, _str_literal("ahoj")))
        class_b = _class("B", "A", _method(
            "m:", 1, _param("x", 1),
            _assign(1, "_", super_m_ahoj)
            + _assign(2, "_", _send("print", '<var name="x"/>')),
        ))
        class_literal_b = '<literal class="class" value="B"/>'
        b_new = _send("new", class_literal_b)
        send_m = _send("m:", b_new, _arg(1, _str_literal("world")))
        class_main = _class("Main", "Object", _method(
            "run", 0, "",
            _assign(1, "_", send_m),
        ))
        xml = _full_xml(class_a, class_b, class_main)
        assert _run(xml) == "ahoj\nworld\n"


# ---------------------------------------------------------------------------
# Advanced: full class hierarchy from user example (A, B, C)
# C.u calls self m: super
#   → B.m: is called (B inherits from A, overrides m:)
#   → super m: 'ahoj' calls A.m: → prints 'ahoj'
#   → x print where x is C instance → C.print → prints 'bar'
# Final output: 'ahoj\nbar\n'
# ---------------------------------------------------------------------------

class TestFullClassHierarchy:
    """
    class A : Object { m: [ :x | _ := x print. ] }
    class B : A     { m: [ :x | _ := super m: 'ahoj'. _ := x print. ] }
    class C : B     { u [ | _ := self m: super. ] print [ | _ := 'bar' print. ] }
    class Main : Object { run [ | _ := (C new) u. ] }
    Expected output: ahoj\nbar\n
    """

    @pytest.mark.xfail(reason="Multiple features not yet implemented: "
                               "self, super, class instantiation, inheritance, "
                               "keyword messages, custom print method")
    def test_full_hierarchy_output(self):
        class_a = _class("A", "Object", _method(
            "m:", 1, _param("x", 1),
            _assign(1, "_", _send("print", '<var name="x"/>')),
        ))
        super_m_ahoj = _send("m:", '<var name="super"/>', _arg(1, _str_literal("ahoj")))
        class_b = _class("B", "A", _method(
            "m:", 1, _param("x", 1),
            _assign(1, "_", super_m_ahoj)
            + _assign(2, "_", _send("print", '<var name="x"/>')),
        ))
        # C.u: self m: super  → sends m: to self (C instance) with super as argument
        self_m_super = _send("m:", '<var name="self"/>', _arg(1, '<var name="super"/>'))
        # C.print: 'bar' print
        class_c = _class("C", "B",
            _method("u", 0, "", _assign(1, "_", self_m_super))
            + _method("print", 0, "", _assign(1, "_", _send("print", _str_literal("bar")))),
        )
        class_literal_c = '<literal class="class" value="C"/>'
        c_new = _send("new", class_literal_c)
        class_main = _class("Main", "Object", _method(
            "run", 0, "",
            _assign(1, "_", _send("u", c_new)),
        ))
        xml = _full_xml(class_a, class_b, class_c, class_main)
        assert _run(xml) == "ahoj\nbar\n"


# ---------------------------------------------------------------------------
# identicalTo: — object identity
# ---------------------------------------------------------------------------


class TestIdenticalTo:
    @pytest.mark.xfail(reason="identicalTo: not yet implemented")
    def test_same_variable_is_identical(self):
        """x := 'hi'. (x identicalTo: x) asString print  →  'true'"""
        body = (
            _assign(1, "x", _str_literal("hi"))
            + _assign(2, "_", _send_print(_send_as_string(
                _send_msg("identicalTo:", _var("x"), _var("x"))
            )))
        )
        xml = _make_xml(body)
        assert _run(xml) == "true\n"

    @pytest.mark.xfail(reason="identicalTo: not yet implemented")
    def test_different_literals_not_identical(self):
        """Two separate integer literals are not necessarily identical."""
        body = _assign(1, "_", _send_print(_send_as_string(
            _send_msg("identicalTo:", _int_literal(1), _int_literal(2))
        )))
        xml = _make_xml(body)
        assert _run(xml) == "false\n"


# ---------------------------------------------------------------------------
# equalTo: — value equality
# ---------------------------------------------------------------------------


class TestEqualTo:
    @pytest.mark.xfail(reason="equalTo: on String not yet implemented")
    def test_equal_strings(self):
        """'abc' equalTo: 'abc'  →  true"""
        body = _assign(1, "_", _send_print(_send_as_string(
            _send_msg("equalTo:", _str_literal("abc"), _str_literal("abc"))
        )))
        xml = _make_xml(body)
        assert _run(xml) == "true\n"

    @pytest.mark.xfail(reason="equalTo: on String not yet implemented")
    def test_unequal_strings(self):
        """'abc' equalTo: 'xyz'  →  false"""
        body = _assign(1, "_", _send_print(_send_as_string(
            _send_msg("equalTo:", _str_literal("abc"), _str_literal("xyz"))
        )))
        xml = _make_xml(body)
        assert _run(xml) == "false\n"


# ---------------------------------------------------------------------------
# Integer minus:, divBy:
# ---------------------------------------------------------------------------


class TestIntegerMinusDivBy:
    @pytest.mark.xfail(reason="minus: not yet implemented")
    def test_minus(self):
        """10 minus: 3  →  7"""
        body = _assign(1, "_", _send_print(_send_as_string(
            _send_msg("minus:", _int_literal(10), _int_literal(3))
        )))
        xml = _make_xml(body)
        assert _run(xml) == "7\n"

    @pytest.mark.xfail(reason="minus: not yet implemented")
    def test_minus_negative_result(self):
        """3 minus: 10  →  -7"""
        body = _assign(1, "_", _send_print(_send_as_string(
            _send_msg("minus:", _int_literal(3), _int_literal(10))
        )))
        xml = _make_xml(body)
        assert _run(xml) == "-7\n"

    @pytest.mark.xfail(reason="divBy: not yet implemented")
    def test_div_by(self):
        """10 divBy: 3  →  3  (integer division)"""
        body = _assign(1, "_", _send_print(_send_as_string(
            _send_msg("divBy:", _int_literal(10), _int_literal(3))
        )))
        xml = _make_xml(body)
        assert _run(xml) == "3\n"

    @pytest.mark.xfail(reason="divBy: zero not yet implemented")
    def test_div_by_zero_raises(self):
        """10 divBy: 0  →  INT_INVALID_ARG (53)"""
        body = _assign(1, "_", _send_msg("divBy:", _int_literal(10), _int_literal(0)))
        xml = _make_xml(body)
        with pytest.raises(InterpreterError) as exc_info:
            _run(xml)
        assert exc_info.value.error_code == ErrorCode.INT_INVALID_ARG


# ---------------------------------------------------------------------------
# String startsWith:endsBefore: and length
# ---------------------------------------------------------------------------


class TestStringSliceAndLength:
    @pytest.mark.xfail(reason="startsWith:endsBefore: not yet implemented")
    def test_substring_basic(self):
        """'hello' startsWith: 2 endsBefore: 4  →  'el'"""
        body = _assign(1, "_", _send_print(
            _send_msg("startsWith:endsBefore:", _str_literal("hello"),
                      _int_literal(2), _int_literal(4))
        ))
        xml = _make_xml(body)
        assert _run(xml) == "el\n"

    @pytest.mark.xfail(reason="startsWith:endsBefore: not yet implemented")
    def test_substring_end_beyond_length(self):
        """'hi' startsWith: 1 endsBefore: 99  →  'hi'"""
        body = _assign(1, "_", _send_print(
            _send_msg("startsWith:endsBefore:", _str_literal("hi"),
                      _int_literal(1), _int_literal(99))
        ))
        xml = _make_xml(body)
        assert _run(xml) == "hi\n"

    @pytest.mark.xfail(reason="startsWith:endsBefore: not yet implemented")
    def test_substring_zero_diff_returns_empty(self):
        """end - start <= 0  →  ''"""
        body = _assign(1, "_", _send_print(
            _send_msg("startsWith:endsBefore:", _str_literal("hello"),
                      _int_literal(3), _int_literal(3))
        ))
        xml = _make_xml(body)
        assert _run(xml) == "\n"

    @pytest.mark.xfail(reason="length not yet implemented")
    def test_string_length(self):
        """'hello' length  →  5"""
        body = _assign(1, "_", _send_print(_send_as_string(
            _send_msg("length", _str_literal("hello"))
        )))
        xml = _make_xml(body)
        assert _run(xml) == "5\n"

    @pytest.mark.xfail(reason="length not yet implemented")
    def test_empty_string_length(self):
        """'' length  →  0"""
        body = _assign(1, "_", _send_print(_send_as_string(
            _send_msg("length", _str_literal(""))
        )))
        xml = _make_xml(body)
        assert _run(xml) == "0\n"


# ---------------------------------------------------------------------------
# Type-checking messages — isNil, isBoolean, isString, isNumber, isBlock
# ---------------------------------------------------------------------------


class TestTypeChecks:
    @pytest.mark.xfail(reason="isNil not yet implemented")
    def test_nil_is_nil(self):
        """nil isNil asString print  →  'true'"""
        body = _assign(1, "_", _send_print(_send_as_string(
            _send_msg("isNil", _nil_literal())
        )))
        xml = _make_xml(body)
        assert _run(xml) == "true\n"

    @pytest.mark.xfail(reason="isNil not yet implemented")
    def test_string_is_not_nil(self):
        """'hi' isNil asString print  →  'false'"""
        body = _assign(1, "_", _send_print(_send_as_string(
            _send_msg("isNil", _str_literal("hi"))
        )))
        xml = _make_xml(body)
        assert _run(xml) == "false\n"

    @pytest.mark.xfail(reason="isBoolean not yet implemented")
    def test_true_is_boolean(self):
        """true isBoolean asString print  →  'true'"""
        body = _assign(1, "_", _send_print(_send_as_string(
            _send_msg("isBoolean", _true_literal())
        )))
        xml = _make_xml(body)
        assert _run(xml) == "true\n"

    @pytest.mark.xfail(reason="isBoolean not yet implemented")
    def test_integer_is_not_boolean(self):
        """42 isBoolean asString print  →  'false'"""
        body = _assign(1, "_", _send_print(_send_as_string(
            _send_msg("isBoolean", _int_literal(42))
        )))
        xml = _make_xml(body)
        assert _run(xml) == "false\n"

    @pytest.mark.xfail(reason="isString not yet implemented")
    def test_string_is_string(self):
        """'x' isString asString print  →  'true'"""
        body = _assign(1, "_", _send_print(_send_as_string(
            _send_msg("isString", _str_literal("x"))
        )))
        xml = _make_xml(body)
        assert _run(xml) == "true\n"

    @pytest.mark.xfail(reason="isNumber not yet implemented")
    def test_integer_is_number(self):
        """42 isNumber asString print  →  'true'"""
        body = _assign(1, "_", _send_print(_send_as_string(
            _send_msg("isNumber", _int_literal(42))
        )))
        xml = _make_xml(body)
        assert _run(xml) == "true\n"


# ---------------------------------------------------------------------------
# Boolean: not, and:, or:
# ---------------------------------------------------------------------------


class TestBooleanOperators:
    @pytest.mark.xfail(reason="Boolean not not yet implemented")
    def test_true_not(self):
        """true not asString print  →  'false'"""
        body = _assign(1, "_", _send_print(_send_as_string(
            _send_msg("not", _true_literal())
        )))
        xml = _make_xml(body)
        assert _run(xml) == "false\n"

    @pytest.mark.xfail(reason="Boolean not not yet implemented")
    def test_false_not(self):
        """false not asString print  →  'true'"""
        body = _assign(1, "_", _send_print(_send_as_string(
            _send_msg("not", _false_literal())
        )))
        xml = _make_xml(body)
        assert _run(xml) == "true\n"

    @pytest.mark.xfail(reason="Boolean and: not yet implemented")
    def test_true_and_true_block(self):
        """true and: [| _ := true. ]  →  block evaluated, returns true"""
        blk = _block(0, [], _assign(1, "_", _true_literal()))
        body = _assign(1, "_", _send_print(_send_as_string(
            _send_msg("and:", _true_literal(), blk)
        )))
        xml = _make_xml(body)
        assert _run(xml) == "true\n"

    @pytest.mark.xfail(reason="Boolean and: short-circuit not yet implemented")
    def test_false_and_block_not_evaluated(self):
        """false and: [block]  →  false, block never runs"""
        blk = _block(0, [], _assign(1, "_", _send_print(_str_literal("should-not-print"))))
        body = _assign(1, "_", _send_print(_send_as_string(
            _send_msg("and:", _false_literal(), blk)
        )))
        xml = _make_xml(body)
        assert _run(xml) == "false\n"

    @pytest.mark.xfail(reason="Boolean or: not yet implemented")
    def test_false_or_true_block(self):
        """false or: [| _ := true. ]  →  block evaluated, returns true"""
        blk = _block(0, [], _assign(1, "_", _true_literal()))
        body = _assign(1, "_", _send_print(_send_as_string(
            _send_msg("or:", _false_literal(), blk)
        )))
        xml = _make_xml(body)
        assert _run(xml) == "true\n"

    @pytest.mark.xfail(reason="Boolean or: short-circuit not yet implemented")
    def test_true_or_block_not_evaluated(self):
        """true or: [block]  →  true, block never runs"""
        blk = _block(0, [], _assign(1, "_", _send_print(_str_literal("should-not-print"))))
        body = _assign(1, "_", _send_print(_send_as_string(
            _send_msg("or:", _true_literal(), blk)
        )))
        xml = _make_xml(body)
        assert _run(xml) == "true\n"


# ---------------------------------------------------------------------------
# whileTrue: — loop
# ---------------------------------------------------------------------------


class TestWhileTrue:
    @pytest.mark.xfail(reason="whileTrue: not yet implemented")
    def test_while_true_counts_down(self):
        """Counts down from 3 to 1, printing each value."""
        body = """
        <assign order="1">
          <var name="r"/>
          <expr>
            <send selector="value:">
              <expr><var name="self"/></expr>
              <arg order="1"><expr><literal class="Integer" value="3"/></expr></arg>
            </send>
          </expr>
        </assign>
        <assign order="2">
          <var name="y"/>
          <expr>
            <send selector="whileTrue:">
              <expr>
                <block arity="0">
                  <assign order="1">
                    <var name="ret"/>
                    <expr>
                      <send selector="greaterThan:">
                        <expr><send selector="r"><expr><var name="self"/></expr></send></expr>
                        <arg order="1"><expr><literal class="Integer" value="0"/></expr></arg>
                      </send>
                    </expr>
                  </assign>
                </block>
              </expr>
              <arg order="1">
                <expr>
                  <block arity="0">
                    <assign order="1">
                      <var name="_"/>
                      <expr>
                        <send selector="print">
                          <expr>
                            <send selector="asString">
                              <expr><send selector="r"><expr><var name="self"/></expr></send></expr>
                            </send>
                          </expr>
                        </send>
                      </expr>
                    </assign>
                    <assign order="2">
                      <var name="r"/>
                      <expr>
                        <send selector="r:">
                          <expr><var name="self"/></expr>
                          <arg order="1">
                            <expr>
                              <send selector="minus:">
                                <expr><send selector="r"><expr><var name="self"/></expr></send></expr>
                                <arg order="1"><expr><literal class="Integer" value="1"/></expr></arg>
                              </send>
                            </expr>
                          </arg>
                        </send>
                      </expr>
                    </assign>
                  </block>
                </expr>
              </arg>
            </send>
          </expr>
        </assign>"""
        xml = _make_xml(body)
        assert _run(xml) == "3\n2\n1\n"


# ---------------------------------------------------------------------------
# timesRepeat: — loop with iteration counter
# ---------------------------------------------------------------------------


class TestTimesRepeat:
    @pytest.mark.xfail(reason="timesRepeat: not yet implemented")
    def test_times_repeat_prints_counter(self):
        """3 timesRepeat: [ :i | i asString print. ]  →  1\\n2\\n3\\n"""
        blk = _block(1, ["i"], _assign(1, "_", _send_print(_send_as_string(_var("i")))))
        body = _assign(1, "_", _send_msg("timesRepeat:", _int_literal(3), blk))
        xml = _make_xml(body)
        assert _run(xml) == "1\n2\n3\n"

    @pytest.mark.xfail(reason="timesRepeat: not yet implemented")
    def test_times_repeat_zero_does_nothing(self):
        """0 timesRepeat: [block]  →  nothing printed, returns nil"""
        blk = _block(1, ["i"], _assign(1, "_", _send_print(_str_literal("x"))))
        body = _assign(1, "_", _send_msg("timesRepeat:", _int_literal(0), blk))
        xml = _make_xml(body)
        assert _run(xml) == ""
