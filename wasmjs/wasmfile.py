"""Simple wrapper around a single-file wasmtime module."""

import functools
import importlib

import wasmtime


class WasmFile:
    """Simple wrapper around a single-file wasmtime module."""

    def __init__(self, *, path=None, wasm=None):
        config = wasmtime.Config()

        self.engine = wasmtime.Engine(config)

        if wasm:
            self.module = wasmtime.Module(self.engine, wasm)
        else:
            self.module = wasmtime.Module.from_file(self.engine, path)  # pragma: no cover

        self.linker = wasmtime.Linker(self.engine)

        for symbol in self.module.imports:
            if symbol.module == 'wasi_snapshot_preview1':
                self.linker.define_wasi()
                self.needs_wasi = True
                break
        else:
            self.needs_wasi = False

    def instantiate(self):
        """Create a runnable instance of this module."""

        return _Instance(self)


class _Instance:

    def __init__(self, wasmfile):
        store = wasmtime.Store(wasmfile.engine)

        if wasmfile.needs_wasi:
            wasi_config = wasmtime.WasiConfig()
            wasi_config.inherit_stdout()
            store.set_wasi(wasi_config)

        instance = wasmfile.linker.instantiate(store, wasmfile.module)

        self.exports = _Exports(store, instance)
        self.api = _APILoader(self)


class _Exports:

    def __init__(self, store, instance):
        for k, v in instance.exports(store).items():
            if isinstance(v, wasmtime.Func):
                v = functools.partial(v, store)
            elif isinstance(v, wasmtime.Global):
                v = functools.partial(v.value, store)
            elif isinstance(v, wasmtime.Memory):
                v = _Memory(v, store)
            else:
                continue  # pragma: no cover
            setattr(self, k, v)


class _Memory:

    def __init__(self, memory, store):
        self.read = functools.partial(memory.read, store)
        self.write = functools.partial(memory.write, store)
        self.pointer_size = memory.type(store).is_64 and 8 or 4


class _APILoader:

    def __init__(self, inst):
        self._inst = inst

    def __getattr__(self, name):
        mod = importlib.import_module(f'wasmjs.api.{name}')
        apiinst = mod.API(self._inst)
        setattr(self, name, apiinst)
        return apiinst
