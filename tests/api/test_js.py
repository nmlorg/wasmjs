"""Tests for wasmjs.api.js."""

from wasmjs import jsvalueutil
from wasmjs import wasmjs


def test_eval():
    """Test eval_to_jsval."""

    inst = wasmjs.WasmJS()._inst  # pylint: disable=protected-access

    with inst.api.js.eval_to_jsval('1 + 2') as jsval:
        assert jsval.decode() == 3
    with inst.api.js.eval_to_jsval('"hello" + "there"') as jsval:
        assert jsval.decode() == 'hellothere'
    with inst.api.js.eval_to_jsval('function test(a, b) { return a * b; }; test(2, 3);') as jsval:
        assert jsval.decode() == 6
    with inst.api.js.eval_to_jsval('({hello: 5});') as jsval:
        assert jsval.decode() == {'hello': 5}
    with inst.api.js.eval_to_jsval('1 +') as jsval:
        assert jsval.tag == jsvalueutil.Tag.EXCEPTION


def test_call():
    """Test call_to_jsval."""

    inst = wasmjs.WasmJS()._inst  # pylint: disable=protected-access

    with inst.api.js.eval_to_jsval(
            'function test(...args) { return JSON.stringify(args); }; test;') as test:
        with inst.api.js.call_to_jsval(test.nanbox, 'x', 1, 2.3, True, None) as jsval:
            assert jsval.decode() == '["x",1,2.3,true,null]'
