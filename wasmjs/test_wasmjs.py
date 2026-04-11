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
