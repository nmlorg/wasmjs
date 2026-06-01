"""Tests for wasmjs.wasmjs."""

import types

import pytest

from wasmjs import wasmjs


def test_basic():
    """Quick smoke test."""

    js = wasmjs.WasmJS()
    assert js.eval('1 + 2') == 3
    assert js.eval('"hello" + "there"') == 'hellothere'
    assert js.eval('function test(a, b) { return a * b; }; test(2, 3);') == 6
    assert js.eval('({hello: 5});') == {'hello': 5}

    with pytest.raises(wasmjs.JSError, check=lambda e: e.name == 'SyntaxError'):
        js.eval('1 +')

    # Stub values are hidden.
    with pytest.raises(wasmjs.JSError, check=lambda e: e.name == 'ReferenceError'):
        js.eval('next_generator_id')

    # Local variables are not persisted.
    assert js.eval('let test_basic_num = 1000; test_basic_num;') == 1000
    with pytest.raises(wasmjs.JSError, check=lambda e: e.name == 'ReferenceError'):
        js.eval('test_basic_num')


def test_generator():
    """Verify that JS generators can be accessed like Python gens, but behave like JS gens."""

    js = wasmjs.WasmJS()
    js.eval("""
      globalThis.gengen = function*(a) {
        let b = yield `a=${a}`;
        let c = yield `b=${b}`;
        let d = yield `c=${c}`;
        return `d=${d}`;
      };
    """)

    # Implicit listification.
    assert js.eval('Array.from(gengen(5))') == ['a=5', 'b=undefined', 'c=undefined']
    assert list(js.eval('gengen(5)')) == ['a=5', 'b=null', 'c=null']

    # Manual running.
    assert js.eval("""
      let gen = gengen(10);
      let ret = [];
      ret.push(gen.next(999));
      ret.push(gen.next(20));
      ret.push(gen.next(30));
      ret.push(gen.next(40));
      ret.push(gen.next(999));
      JSON.stringify(ret);
    """) == """[
      {"value":"a=10","done":false},
      {"value":"b=20","done":false},
      {"value":"c=30","done":false},
      {"value":"d=40","done":true},
      {"done":true}
    ]""".replace(' ', '').replace('\n', '')

    susp = js.eval('gengen(10)')
    assert isinstance(susp, types.GeneratorType)
    assert susp.send(None) == 'a=10'
    assert susp.send(20) == 'b=20'
    assert susp.send(30) == 'c=30'
    with pytest.raises(StopIteration, check=lambda e: e.value == 'd=40'):
        susp.send(40)
    with pytest.raises(StopIteration, check=lambda e: e.value is None):
        susp.send(999)


def test_generator_edges():
    """Test a couple edge cases that tripped me up while designing this."""

    js = wasmjs.WasmJS()

    susp = js.eval('function* f() {}; f();')
    assert isinstance(susp, types.GeneratorType)
    assert list(susp) == []  # pylint: disable=use-implicit-booleaness-not-comparison

    susp = js.eval('function* f() { yield 1; }; f();')
    assert isinstance(susp, types.GeneratorType)
    assert list(susp) == [1]

    susp = js.eval('function* f() { yield 1; yield 2; }; f();')
    assert isinstance(susp, types.GeneratorType)
    assert list(susp) == [1, 2]


def test_generator_exceptions():
    """Test exception propagation."""

    js = wasmjs.WasmJS()

    susp = js.eval('function* f() { yield 1; yield bogus; }; f();')
    assert isinstance(susp, types.GeneratorType)
    assert next(susp) == 1
    with pytest.raises(wasmjs.JSError, check=lambda e: e.name == 'ReferenceError'):
        next(susp)
    with pytest.raises(StopIteration, check=lambda e: e.value is None):
        next(susp)


def test_generator_interweave():
    """Verify concurrent generators behave as expected."""

    js = wasmjs.WasmJS()

    fsusp, gsusp = js.eval("""
      let count = 0;
      function* f() { yield ++count; yield ++count; yield ++count; }
      function* g() { yield ++count; yield ++count; yield ++count; }
      [f(), g()];
    """)
    assert isinstance(fsusp, types.GeneratorType)
    assert isinstance(gsusp, types.GeneratorType)
    assert next(gsusp) == 1
    assert next(gsusp) == 2
    assert next(fsusp) == 3
    assert next(gsusp) == 4
    assert next(fsusp) == 5
    assert next(fsusp) == 6

    susp = js.eval("""
      let count = 0;
      function* f() { yield ++count; yield ++count; yield ++count; }
      function* g() { yield ++count; yield ++count; yield ++count; }
      function* h() { yield f(); yield g(); }
      h();
    """)
    assert isinstance(susp, types.GeneratorType)
    fsusp = next(susp)
    assert isinstance(fsusp, types.GeneratorType)
    assert next(fsusp) == 1
    gsusp = next(susp)
    assert isinstance(gsusp, types.GeneratorType)
    assert next(fsusp) == 2
    assert next(gsusp) == 3
    assert next(fsusp) == 4
    assert next(gsusp) == 5
    assert next(gsusp) == 6


def test_generator_poison():
    """Make sure things that look like how WasmJS transports generators don't confuse it."""

    js = wasmjs.WasmJS()

    assert js.eval("({'#': 1000, blah: 2000});") == {'#': 1000, 'blah': 2000}
    assert js.eval("({'#': {'value': 1000}, blah: 2000});") == {'#': {'value': 1000}, 'blah': 2000}
    assert js.eval("({'#': {type: 'generator', id: 1000}});") == {
        '#': {
            'type': 'generator',
            'id': 1000,
        },
    }


def test_internal_errors():
    """Document known traps generated by qjs."""

    # See https://github.com/quickjs-ng/quickjs/issues/1460.
    js = wasmjs.WasmJS()

    with pytest.raises(wasmjs.JSError):
        js.eval("JSON.parse('['.repeat(2940));")

    with pytest.raises(wasmjs.InterpreterError):
        js.eval("JSON.parse('['.repeat(2941));")
