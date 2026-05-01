"""All the logic needed to get data out of QuickJS."""

import ctypes
import enum
import json

from wasmjs import lifecycle


class Tag(enum.IntEnum):
    """The type of data represented by a JSValue."""

    FIRST = -9
    BIG_INT = -9
    SYMBOL = -8
    STRING = -7
    STRING_ROPE = -6
    MODULE = -3
    FUNCTION_BYTECODE = -2
    OBJECT = -1
    INT = 0
    BOOL = 1
    NULL = 2
    UNDEFINED = 3
    UNINITIALIZED = 4
    CATCH_OFFSET = 5
    EXCEPTION = 6
    SHORT_BIG_INT = 7
    FLOAT64 = 8


JS_FLOAT64_TAG_ADDEND = 0x7ff80000 - Tag.FIRST + 1
JS_FLOAT64_BIAS = JS_FLOAT64_TAG_ADDEND << 32


class JSValue(lifecycle.PythonOwnedObject):
    """A dynamically typed QuickJS object."""

    def __init__(self, *, api, nanbox=None, tag=None, int32=None):
        if nanbox is None:
            nanbox = tag << 32
            if int32:
                nanbox |= int32

        super().__init__(api=api, nanbox=nanbox)

    @classmethod
    def encode(cls, api, value):  # pylint: disable=too-many-return-statements
        """Encode the given value as a JSValue, storing it in linear memory if necessary."""

        if value is None:
            return cls(api=api, tag=Tag.NULL)
        if isinstance(value, bool):
            return cls(api=api, tag=Tag.BOOL, int32=int(value))
        if isinstance(value, int):
            if -2**31 <= value < 2**31:
                return cls(api=api, tag=Tag.INT, int32=value & ((1 << 32) - 1))
            if abs(value) < 2**53:
                return cls.encode(api, float(value))
            return api.eval_to_jsval(f'{value}n')
        if isinstance(value, float):
            return cls(api=api, nanbox=_Union64(f64=value).i64 - JS_FLOAT64_BIAS)
        if isinstance(value, str):
            with api.inst.write_string(value) as written:
                nanbox = api.lowlevel.NewStringLen(written.offset, written.size - 1)
            return cls(api=api, nanbox=nanbox)
        return api.eval_to_jsval(json.dumps(value))

    def decode(self):
        """Convert this to a Python data type, pulling from linear memory if necessary."""

        match self.tag:
            case Tag.BIG_INT:
                return int(self.to_string())
            case Tag.BOOL:
                return bool(self.nanbox & 1)
            case Tag.FLOAT64:
                return _Union64(i64=self.nanbox + JS_FLOAT64_BIAS).f64
            case Tag.OBJECT:
                return json.loads(self.to_json().to_string())
            case Tag.SHORT_BIG_INT | Tag.INT:
                return ctypes.c_int32(self.nanbox).value
            case Tag.STRING:
                return self.to_string()

    @property
    def tag(self):
        """The type of data represented by the JSValue."""

        tag = self.nanbox >> 32
        if Tag.FIRST <= tag < Tag.FLOAT64:
            return Tag(tag)
        return Tag.FLOAT64

    def to_cstr(self):
        """Return String(self.nanbox) as a C string."""

        with self.api.inst.reserve_size_t() as sizet:
            cstr_offset = self.api.lowlevel.ToCStringLen2(sizet.offset, self.nanbox, 0)
            return _CString(api=self.api, offset=cstr_offset, utf8_len=sizet.to_int())

    def to_json(self):
        """Return JSON.stringify(self.nanbox) as a JSValue."""

        jsonval_nanbox = self.api.lowlevel.JSONStringify(self.nanbox, 0, 0)
        return JSValue(api=self.api, nanbox=jsonval_nanbox)

    def to_string(self):
        """Return String(self.nanbox) as a Python string."""

        with self.to_cstr() as cstr:
            return cstr.to_string()

    def close(self):
        self.api.lowlevel.FreeValue(self.nanbox)


class _CString(lifecycle.PythonOwnedObject):

    def to_string(self):
        """Convert this C string to a Python string."""

        return self.api.inst.exports.memory.read(self.offset,
                                                 self.offset + self.utf8_len).decode('utf-8')

    def close(self):
        self.api.lowlevel.FreeCString(self.offset)


class _Union64(ctypes.Union):
    _fields_ = (
        ('f64', ctypes.c_double),
        ('i64', ctypes.c_int64),
    )
