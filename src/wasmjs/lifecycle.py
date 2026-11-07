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


def run_at_generator_exit(gen, close):
    """Run close() iff gen is closed or discarded before throwing or returning."""

    subgen = _run_at_generator_exit_helper(gen, close)
    next(subgen)
    return subgen


def _run_at_generator_exit_helper(gen, close):
    try:
        yield
        return (yield from gen)
    except GeneratorExit:
        close()
        raise
