"""Simple lifecycle management."""


class PythonOwnedObject:
    """An object stored in linear memory but owned by Python."""

    def __init__(self, owner, offset):
        self._owner = owner
        self.offset = offset

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        del self.offset

    def close(self):
        """Call the object-specific deallocator."""

        raise NotImplementedError()  # pragma: no cover
