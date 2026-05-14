"""Simple utilities to get strings and other high-level data into/out of linear memory."""

from wasmjs import lifecycle


class API:
    """Simple utilities to get strings and other high-level data into/out of linear memory."""

    def __init__(self, inst):
        self._inst = inst

    def write_buf(self, buf):
        """Write buf into linear memory."""

        return _HeapAllocatedObject(self._inst, buf)

    def write_string(self, s):
        """Write s as a UTF-8-encoded, nil-terminated string into linear memory."""

        return self.write_buf(s.encode('utf-8') + b'\0')

    def reserve_size_t(self):
        """Allocate enough space for a 32- or 64-bit size_t in linear memory."""

        return _SizeT(self._inst, b'\0' * self._inst.exports.memory.pointer_size)


class _HeapAllocatedObject(lifecycle.PythonOwnedObject):

    def __init__(self, inst, buf):
        self.size = len(buf)
        offset = inst.exports.malloc(self.size)
        if offset < 0:
            offset += 2**32
        if not 0 < offset < 2**32 - self.size:
            raise MemoryError(f"malloc({self.size}) returned {offset or 'NULL'}")
        super().__init__(inst=inst, offset=offset)
        inst.exports.memory.write(buf, offset)

    def close(self):
        self.inst.exports.free(self.offset)


class _SizeT(_HeapAllocatedObject):

    def to_int(self):
        """Read the size_t from linear memory and convert it to an int."""

        raw = self.inst.exports.memory.read(self.offset, self.offset + self.size)
        return int.from_bytes(raw, 'little')
