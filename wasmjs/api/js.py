"""Utilities to make the qjs API a little simpler."""

import contextlib

from wasmjs import jsvalueutil


class API:
    """Utilities to make the qjs API a little simpler."""

    def __init__(self, inst):
        self._inst = inst

    def call_to_jsval(self, func_nanbox, *args, this_nanbox=0):
        """Return func_nanbox.call(this_nanbox, *args) as a JSValue."""

        with contextlib.ExitStack() as stack:
            jsval_nanboxes = []
            for arg in args:
                jsval = stack.enter_context(self.encode(arg))
                jsval_nanboxes.append(jsval.nanbox.to_bytes(8, 'little', signed=True))
            with self._inst.api.memutil.write_buf(b''.join(jsval_nanboxes)) as written_argv:
                jsval_nanbox = self._inst.api.qjs.JS_Call(func_nanbox, this_nanbox, len(args),
                                                          written_argv.offset)
        return jsvalueutil.JSValue(inst=self._inst, nanbox=jsval_nanbox)

    def encode(self, value):
        """Return value as a JSValue."""

        return jsvalueutil.JSValue.encode(self._inst, value)

    def eval_to_jsval(self, expr):
        """Return eval(expr) as a JSValue."""

        with self._inst.api.memutil.write_string(expr) as written:
            jsval_nanbox = self._inst.api.qjs.JS_Eval(written.offset, written.size - 1, 0, 0)
        return jsvalueutil.JSValue(inst=self._inst, nanbox=jsval_nanbox)
