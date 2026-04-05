"""Tests for wasmjs.wasmjs."""

import pytest

from wasmjs import wasmjs


def test_basic():
    """Quick smoke test."""

    js = wasmjs.WasmJS()
    assert js.eval('1 + 2') == 3
    assert js.eval('"hello" + "there"') == 'hellothere'
    assert js.eval('function test(a, b) { return a * b; }; test(2, 3);') == 6
    assert js.eval('({hello: 5});') == {'hello': 5}

    with pytest.raises(wasmjs.JSError):
        js.eval('1 +')


def test_jsvalue():
    """When sizeof(intptr_t) < sizeof(int128_t), QuickJS uses "NaN-boxed" int64s for JSValue."""

    js = wasmjs.WasmJS()

    # pylint: disable=protected-access
    with js._api.eval_to_jsval('"a string"') as jsval:
        assert jsval.tag == -7  # JS_TAG_STRING
        assert jsval.to_string() == 'a string'

    with js._api.eval_to_jsval('123') as jsval:
        assert jsval.tag == 0  # JS_TAG_INT
        assert jsval.stored_value == 123  # Integers are stored in the low 32 bits of the JSValue.
        assert jsval.nanbox == 123  # And, since JS_TAG_INT is 0, the whole JSValue is just the int.
        assert jsval.to_string() == '123'

    with js._api.eval_to_jsval('1 +') as jsval:
        assert jsval.tag == 6  # JS_TAG_EXCEPTION
        assert jsval.to_string() == ''  # Exceptions short-circuit in JS_ToStringInternal.
