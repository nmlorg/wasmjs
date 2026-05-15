"""See https://github.com/quickjs-ng/quickjs/blob/master/quickjs.h."""


class API:  # pylint: disable=invalid-name,missing-function-docstring
    """See https://github.com/quickjs-ng/quickjs/blob/master/quickjs.h."""

    def __init__(self, inst):
        self._inst = inst
        assert inst.exports.qjs_init() == 0
        self._ctx = inst.exports.qjs_get_context()

    def JS_Call(self, func_nanbox, this_nanbox, argc, argv_offset):
        return self._inst.exports.JS_Call(self._ctx, func_nanbox, this_nanbox, argc, argv_offset)

    def JS_Eval(self, input_offset, input_len, filename_offset, eval_flags):
        return self._inst.exports.JS_Eval(self._ctx, input_offset, input_len, filename_offset,
                                          eval_flags)

    def JS_FreeCString(self, cstr_offset):
        return self._inst.exports.JS_FreeCString(self._ctx, cstr_offset)

    def JS_FreeValue(self, jsval_nanbox):
        return self._inst.exports.JS_FreeValue(self._ctx, jsval_nanbox)

    def JS_JSONStringify(self, obj_nanbox, replacer_nanbox, space0_nanbox):
        return self._inst.exports.JS_JSONStringify(self._ctx, obj_nanbox, replacer_nanbox,
                                                   space0_nanbox)

    def JS_NewStringLen(self, str1_offset, len1):
        return self._inst.exports.JS_NewStringLen(self._ctx, str1_offset, len1)

    def JS_ToCStringLen2(self, sizet_offset, jsvalue_nanbox, cesu8):
        return self._inst.exports.JS_ToCStringLen2(self._ctx, sizet_offset, jsvalue_nanbox, cesu8)
