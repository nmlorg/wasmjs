"""Tests for wasmjs.jsvalueutil."""

import math

from wasmjs import jsvalueutil
from wasmjs import wasmjs


def test_jsvalue():  # pylint: disable=too-many-statements
    """Test all the [supported] types of JSValues."""

    js = wasmjs.WasmJS()

    # pylint: disable=protected-access

    with js._api.eval_to_jsval('1 == 1') as jsval:
        assert jsval.tag == jsvalueutil.Tag.BOOL
        assert jsval.decode() is True

    with js._api.eval_to_jsval('1 == 2') as jsval:
        assert jsval.tag == jsvalueutil.Tag.BOOL
        assert jsval.decode() is False

    with js._api.eval_to_jsval('null') as jsval:
        assert jsval.tag == jsvalueutil.Tag.NULL
        assert jsval.decode() is None

    with js._api.eval_to_jsval('globalThis.__undefined') as jsval:
        assert jsval.tag == jsvalueutil.Tag.UNDEFINED
        assert jsval.decode() is None

    with js._api.eval_to_jsval('1 +') as jsval:
        assert jsval.tag == jsvalueutil.Tag.EXCEPTION
        assert jsval.decode() is None

    with js._api.eval_to_jsval('"a string".toUpperCase()') as jsval:
        assert jsval.tag == jsvalueutil.Tag.STRING
        assert jsval.decode() == 'A STRING'

    with js._api.eval_to_jsval('111 * 2') as jsval:
        assert jsval.tag == jsvalueutil.Tag.INT
        # Since JS_TAG_INT is 0 (and the value is positive), the whole JSValue is just the int.
        assert jsval.nanbox == 222
        assert jsval.decode() == 222

    with js._api.eval_to_jsval('-111 * 3') as jsval:
        assert jsval.tag == jsvalueutil.Tag.INT
        assert jsval.decode() == -333

    with js._api.eval_to_jsval('111n * 4n') as jsval:
        assert jsval.tag == jsvalueutil.Tag.SHORT_BIG_INT
        assert jsval.decode() == 444

    with js._api.eval_to_jsval('-111n * 5n') as jsval:
        assert jsval.tag == jsvalueutil.Tag.SHORT_BIG_INT
        assert jsval.decode() == -555

    with js._api.eval_to_jsval('3 / 2') as jsval:
        assert jsval.tag == jsvalueutil.Tag.FLOAT64
        assert jsval.decode() == 1.5

    with js._api.eval_to_jsval('-5 / 2') as jsval:
        assert jsval.tag == jsvalueutil.Tag.FLOAT64
        assert jsval.decode() == -2.5

    with js._api.eval_to_jsval('3e-324') as jsval:
        assert jsval.tag == jsvalueutil.Tag.FLOAT64
        assert jsval.decode() == 3e-324

    with js._api.eval_to_jsval('-3e-324') as jsval:
        assert jsval.tag == jsvalueutil.Tag.FLOAT64
        assert jsval.decode() == -3e-324

    with js._api.eval_to_jsval('2e-324') as jsval:
        assert jsval.tag == jsvalueutil.Tag.INT
        assert jsval.decode() == 0

    with js._api.eval_to_jsval('10 ** 100') as jsval:
        assert jsval.tag == jsvalueutil.Tag.FLOAT64
        assert jsval.decode() == 1e100

    with js._api.eval_to_jsval('-(10 ** 101)') as jsval:
        assert jsval.tag == jsvalueutil.Tag.FLOAT64
        assert jsval.decode() == -1e101

    with js._api.eval_to_jsval('10n ** 102n') as jsval:
        assert jsval.tag == jsvalueutil.Tag.BIG_INT
        assert jsval.decode() == 10**102

    with js._api.eval_to_jsval('-(10n ** 103n)') as jsval:
        assert jsval.tag == jsvalueutil.Tag.BIG_INT
        assert jsval.decode() == -10**103

    with js._api.eval_to_jsval('1 / 0') as jsval:
        assert jsval.tag == jsvalueutil.Tag.FLOAT64
        assert jsval.decode() == math.inf

    with js._api.eval_to_jsval('-1 / 0') as jsval:
        assert jsval.tag == jsvalueutil.Tag.FLOAT64
        assert jsval.decode() == -math.inf

    with js._api.eval_to_jsval('Math.sqrt(-4)') as jsval:
        assert jsval.tag == jsvalueutil.Tag.FLOAT64
        assert math.isnan(jsval.decode())

    with js._api.eval_to_jsval('new Array(1, 2, 3)') as jsval:
        assert jsval.tag == jsvalueutil.Tag.OBJECT
        assert jsval.decode() == [1, 2, 3]
