"""Tests for wasmjs.jsvalueutil."""

import math

from wasmjs import jsvalueutil
from wasmjs import wasmjs


def test_jsvalue():
    """Test all the [supported] types of JSValues."""

    js = wasmjs.WasmJS()

    tag = jsvalueutil.Tag
    table = [
        ('1 == 1', tag.BOOL, True),
        ('1 == 2', tag.BOOL, False),
        ('null', tag.NULL, None),
        ('globalThis.__undefined', tag.UNDEFINED, None),
        ('1 +', tag.EXCEPTION, None),
        ('"a string".toUpperCase()', tag.STRING, 'A STRING'),
        ('111 * 2', tag.INT, 222),
        ('-111 * 3', tag.INT, -333),
        ('111n * 4n', tag.SHORT_BIG_INT, 444),
        ('-111n * 5n', tag.SHORT_BIG_INT, -555),
        ('3 / 2', tag.FLOAT64, 1.5),
        ('-5 / 2', tag.FLOAT64, -2.5),
        ('5e-324', tag.FLOAT64, 5e-324),
        ('-5e-324', tag.FLOAT64, -5e-324),
        ('2e-324', tag.INT, 0),
        ('10 ** 100', tag.FLOAT64, 1e100),
        ('-(10 ** 101)', tag.FLOAT64, -1e101),
        ('10n ** 102n', tag.BIG_INT, 10**102),
        ('-(10n ** 103n)', tag.BIG_INT, -10**103),
        ('1 / 0', tag.FLOAT64, math.inf),
        ('-1 / 0', tag.FLOAT64, -math.inf),
        ('Math.sqrt(-4)', tag.FLOAT64, math.nan),
        ('new Array(1, 2, 3)', tag.OBJECT, [1, 2, 3]),
    ]

    for js_expr, tag, expected_val in table:
        with js._api.eval_to_jsval(js_expr) as jsval:  # pylint: disable=protected-access
            assert jsval.tag == tag
            actual_val = jsval.decode()
            if expected_val is math.nan:
                assert math.isnan(actual_val)
            else:
                assert actual_val == expected_val
