"""Simple utilities to get strings and other high-level data into/out of linear memory."""

import math

from wasmjs import lifecycle


class API:
    """Simple utilities to get strings and other high-level data into/out of linear memory."""

    max_reusable_alloc = 1024 * 1024

    def __init__(self, inst):
        self._inst = inst
        self._pool = []

    def reserve(self, size):
        """Reserve enough space for size bytes in linear memory."""

        if not self._pool:
            buf = WasmBuffer(self._inst)
        else:
            for i, buf in enumerate(self._pool):
                if buf.alloc_size >= size:
                    self._pool.pop(i)
                    break
            else:
                buf = self._pool.pop()
            buf.datalen = 0

        buf.reserved_size = size
        if buf.alloc_size < size:
            buf.resize(size)

        return buf

    def write_bytes(self, data):
        """Write data into linear memory."""

        buf = self.reserve(len(data))
        buf.write(data)
        return buf

    def write_string(self, s):
        """Write s as a UTF-8-encoded, nil-terminated string into linear memory."""

        return self.write_bytes(s.encode('utf-8') + b'\0')


class WasmBuffer(lifecycle.PythonOwnedObject):
    """A block of alloc_size bytes in Wasm linear memory."""

    def __init__(self, inst):
        super().__init__(inst=inst)
        self.offset = self.alloc_size = self.datalen = self.reserved_size = 0

    def read(self, datalen=None):
        """Read datalen bytes from linear memory."""

        if datalen is None:
            datalen = self.reserved_size
        return self.inst.exports.memory.read(self.offset, self.offset + datalen)

    def resize(self, alloc_size):
        """Reallocate this buffer to be [at least] alloc_size bytes."""

        assert alloc_size > 0
        alloc_size = int(2**math.ceil(math.log2(alloc_size)))
        offset = self.inst.api.wasilibc.realloc(self.offset, alloc_size)
        if not 0 < offset < 2**32 - alloc_size:
            raise MemoryError(f"realloc({self.offset}, {alloc_size}) returned {offset or 'NULL'}")
        self.offset = offset
        self.alloc_size = alloc_size
        if self.datalen > alloc_size:
            self.datalen = alloc_size
        if self.reserved_size > alloc_size:
            self.reserved_size = alloc_size

    def write(self, data):
        """Write data to linear memory."""

        if len(data) > self.alloc_size:
            self.resize(len(data))
        self.inst.exports.memory.write(data, self.offset)
        self.datalen = len(data)

    def close(self):
        if self.alloc_size > self.inst.api.memutil.max_reusable_alloc:
            self.inst.api.wasilibc.free(self.offset)
            self.__dict__.clear()
        else:
            pool = self.inst.api.memutil._pool  # pylint: disable=protected-access
            pool.append(self)
            pool.sort(key=lambda buf: (buf.alloc_size, buf.offset))
