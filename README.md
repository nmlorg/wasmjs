# wasmjs
Simple Python wrapper around [QuickJS-NG's `qjs-wasi-reactor.wasm`](https://pypi.org/project/qjs-wasi-reactor.wasm/).

# Quickstart
```bash
$ python -m venv my-project
$ source my-project/bin/activate
$ pip install wasmjs
$ python
>>> from wasmjs import wasmjs
>>> js = wasmjs.WasmJS()
>>> js.eval('1 + 2')
3
>>> js.eval('("hello" + "there").toUpperCase()')
'HELLOTHERE'
>>> js.eval('({one: 1, two: 2})')
{'one': 1, 'two': 2}
```

# Structure
`qjs-wasi-reactor.wasm` is essentially 3 build targets statically linked together:
* QuickJS-NG JavaScript library ([`JS_Eval`](https://github.com/search?q=repo%3Aquickjs-ng%2Fquickjs+%22JSValue+JS_Eval%28%22&type=code), etc.)
* QuickJS-NG `qjs` CLI tool ([`qjs_init`](https://github.com/search?q=repo%3Aquickjs-ng%2Fquickjs+%22qjs_init%28%22&type=code), etc.)
* [Bytecode Alliance `wasi-libc`](https://github.com/WebAssembly/wasi-libc) C standard library implementation (`malloc`, etc.)

The API bindings for each component are separated into:

* [`WasmFile`](https://github.com/nmlorg/wasmjs/blob/main/wasmjs/wasmfile.py)
  * `qjs-wasi-reactor.wasm` loader. Wraps [`wasmtime-py`](https://pypi.org/project/wasmtime/), which itself wraps [`Wasmtime`](https://github.com/bytecodealliance/wasmtime), which is a [WebAssembly](https://webassembly.org/) runtime.
* [`api.wasilibc`](https://github.com/nmlorg/wasmjs/blob/main/wasmjs/api/wasilibc.py)
  * `malloc` that changes the return type of `wasi-libc`'s `malloc` from an `int32` to a `uint32`, etc.
* [`api.memutil`](https://github.com/nmlorg/wasmjs/blob/main/wasmjs/api/memutil.py)
  * Convenience functions to get strings and other complex types into and out of the Wasm virtual machine.
* [`api.qjs`](https://github.com/nmlorg/wasmjs/blob/main/wasmjs/api/qjs.py)
  * `JS_Eval` that keeps track of the global context, etc.
* [`api.js`](https://github.com/nmlorg/wasmjs/blob/main/wasmjs/api/js.py)
  * Convenience functions to handle all of the multi-step `qjs` flows.
* [`jsvalueutil`](https://github.com/nmlorg/wasmjs/blob/main/wasmjs/jsvalueutil.py)
  * All of the logic needed to get data into and out of the JS virtual machine (inside the Wasm virtual machine).
* [`WasmJS`](https://github.com/nmlorg/wasmjs/blob/main/wasmjs/wasmjs.py)
  * Convenience layer to simplify all of the above.
