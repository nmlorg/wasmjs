"""Tests for wasmjs.jsvalueutil."""

import math

from wasmjs import jsvalueutil
from wasmjs import wasmjs


def test_jsvalue():
    """Test all the [supported] types of JSValues."""

    tag = jsvalueutil.Tag
    table = [
        ('1 == 1', tag.BOOL, True, 'true'),
        ('1 == 2', tag.BOOL, False, 'false'),
        ('null', tag.NULL, None, 'null'),
        ('globalThis.__undefined', tag.UNDEFINED, None, None),
        ('1 +', tag.EXCEPTION, None, None),
        ('"a string".toUpperCase()', tag.STRING, 'A STRING', 'A STRING'),
        ('111 * 2', tag.INT, 222, '222'),
        ('-111 * 3', tag.INT, -333, '-333'),
        ('111n * 4n', tag.SHORT_BIG_INT, 444, None),
        ('-111n * 5n', tag.SHORT_BIG_INT, -555, None),
        ('3 / 2', tag.FLOAT64, 1.5, '1.5'),
        ('-5 / 2', tag.FLOAT64, -2.5, '-2.5'),
        ('5e-324', tag.FLOAT64, 5e-324, '5e-324'),
        ('-5e-324', tag.FLOAT64, -5e-324, '-5e-324'),
        ('2e-324', tag.INT, 0, '0'),
        ('10 ** 100', tag.FLOAT64, 1e100, '1e+100'),
        ('-(10 ** 101)', tag.FLOAT64, -1e101, '-1e+101'),
        ('10n ** 102n', tag.BIG_INT, 10**102, '1' + '0' * 102),
        ('-(10n ** 103n)', tag.BIG_INT, -10**103, '-1' + '0' * 103),
        ('1 / 0', tag.FLOAT64, math.inf, 'Infinity'),
        ('-1 / 0', tag.FLOAT64, -math.inf, '-Infinity'),
        ('Math.sqrt(-4)', tag.FLOAT64, math.nan, 'NaN'),
        ('new Array(1, 2, 3)', tag.OBJECT, [1, 2, 3], '1,2,3'),
    ]

    api = wasmjs.WasmJS()._api  # pylint: disable=protected-access

    for js_expr, tag, expected_val, js_string in table:
        with api.eval_to_jsval(js_expr) as jsval:
            assert jsval.tag == tag
            actual_val = jsval.decode()
            if expected_val is math.nan:
                assert math.isnan(actual_val)
            else:
                assert actual_val == expected_val

        if js_string:
            with jsvalueutil.JSValue.encode(api, expected_val) as jsval:
                assert jsval.tag == tag, jsval.to_string()
                assert jsval.to_string() == js_string
