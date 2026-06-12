"""Tests for wasmjs.lifecycle."""

import pytest

from wasmjs import lifecycle


def test_run_at_generator_exit():  # pylint: disable=too-many-statements
    """Verify that run_at_generator_exit only runs if the generator is interrupted."""

    def _gen(do_throw=False):
        nonlocal began
        began = True
        yield 1
        if do_throw:
            assert not do_throw
        yield 2
        return 3

    def _close():
        nonlocal closed
        closed = True

    # Never bound, never began, implicitly closed.
    began = closed = False
    lifecycle.run_at_generator_exit(_gen(), _close)
    assert not began and closed

    # Bound and then unbound, but never began, explicitly closed.
    began = closed = False
    x = lifecycle.run_at_generator_exit(_gen(), _close)
    assert not began and not closed
    x.close()
    assert not began and closed

    # Bound and then unbound, but never began, implicitly closed.
    began = closed = False
    x = lifecycle.run_at_generator_exit(_gen(), _close)
    assert not began and not closed
    x = None
    assert not began and closed

    # Began then explicitly closed.
    began = closed = False
    x = lifecycle.run_at_generator_exit(_gen(), _close)
    assert not began and not closed
    assert next(x) == 1
    assert began and not closed
    x.close()
    assert began and closed

    # Began then implicitly closed.
    began = closed = False
    x = lifecycle.run_at_generator_exit(_gen(), _close)
    assert not began and not closed
    assert next(x) == 1
    assert began and not closed
    x = None
    assert began and closed

    # Completed.
    began = closed = False
    x = lifecycle.run_at_generator_exit(_gen(), _close)
    assert not began and not closed
    assert next(x) == 1
    assert next(x) == 2
    with pytest.raises(StopIteration, check=lambda e: e.value == 3):
        next(x)
    x = None
    assert began and not closed

    # Unhandled exception.
    began = closed = False
    x = lifecycle.run_at_generator_exit(_gen(True), _close)
    assert not began and not closed
    assert next(x) == 1
    with pytest.raises(AssertionError):
        next(x)
    x = None
    assert began and not closed
