"""API for https://github.com/WebAssembly/wasi-libc."""


class API:  # pylint: disable=missing-function-docstring
    """API for https://github.com/WebAssembly/wasi-libc."""

    def __init__(self, inst):
        self._inst = inst

    def free(self, ptr):
        assert 0 <= ptr < 2**32
        self._inst.exports.free(ptr)

    def malloc(self, size):
        assert 0 < size < 2**32
        offset = self._inst.exports.malloc(size)
        if offset < 0:
            offset += 2**32
        return offset
