"""API for https://github.com/WebAssembly/wasi-libc."""


class API:  # pylint: disable=missing-function-docstring
    """API for https://github.com/WebAssembly/wasi-libc."""

    def __init__(self, inst):
        self._inst = inst

    def free(self, ptr):
        assert 0 <= ptr < 2**32
        self._inst.exports.free(ptr)

    def realloc(self, offset, size):
        assert 0 < size < 2**32
        offset = self._inst.exports.realloc(offset, size)
        if offset < 0:
            offset += 2**32
        return offset
