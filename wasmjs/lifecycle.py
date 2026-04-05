"""Simple lifecycle management."""


class PythonOwnedObject:
    """An object stored in linear memory but owned by Python."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def close(self):
        """Call the object-specific deallocator."""

        raise NotImplementedError()  # pragma: no cover
