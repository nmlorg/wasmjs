"""Simple wrapper around a single-file wasmtime module."""

import functools

import wasmtime

from wasmjs import lifecycle


class WasmFile:
    """Simple wrapper around a single-file wasmtime module."""

    def __init__(self, fname):
        config = wasmtime.Config()

        self.engine = wasmtime.Engine(config)

        self.module = wasmtime.Module.from_file(self.engine, fname)

        self.linker = wasmtime.Linker(self.engine)
        self.linker.define_wasi()

    def instantiate(self):
        """Create a runnable instance of this module."""

        return _Instance(self)


class _Instance:

    def __init__(self, wasmfile):
        wasi_config = wasmtime.WasiConfig()
        wasi_config.inherit_stdout()

        store = wasmtime.Store(wasmfile.engine)
        store.set_wasi(wasi_config)

        instance = wasmfile.linker.instantiate(store, wasmfile.module)

        self.exports = _Exports(store, instance)

    def write_string(self, s):
        """Write s as a UTF-8-encoded, nil-terminated string into linear memory."""

        return _HeapAllocatedObject(self, s.encode('utf-8') + b'\0')

    def reserve_size_t(self):
        """Allocate enough space for a 32- or 64-bit size_t in linear memory."""

        return _SizeT(self, b'\0' * self.exports.memory.pointer_size)  # pylint: disable=no-member


class _Exports:

    def __init__(self, store, instance):
        for k, v in instance.exports(store).items():
            if isinstance(v, wasmtime.Func):
                v = functools.partial(v, store)
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


class _HeapAllocatedObject(lifecycle.PythonOwnedObject):

    def __init__(self, inst, buf):
        self.size = len(buf)
        offset = inst.exports.malloc(self.size)
        super().__init__(inst, offset)
        inst.exports.memory.write(buf, offset)

    def close(self):
        self._owner.exports.free(self.offset)


class _SizeT(_HeapAllocatedObject):

    def to_int(self):
        """Read the size_t from linear memory and convert it to an int."""

        raw = self._owner.exports.memory.read(self.offset, self.offset + self.size)
        return int.from_bytes(raw, 'little')
