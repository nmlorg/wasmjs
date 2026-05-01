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


def test_call():
    """Test WasmJS._api.call_to_jsval."""

    api = wasmjs.WasmJS()._api  # pylint: disable=protected-access

    with api.eval_to_jsval(
            'function test(...args) { return JSON.stringify(args); }; test;') as test:
        with api.call_to_jsval(test.nanbox, 'x', 1, 2.3, True, None) as jsval:
            assert jsval.decode() == '["x",1,2.3,true,null]'
