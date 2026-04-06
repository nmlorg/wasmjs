"""Quick timing tests of different potential WasmJS.eval implementations."""

import json
import logging
import time

from wasmjs import wasmjs


def main():  # pylint: disable=missing-function-docstring
    # pylint: disable=duplicate-code,protected-access,too-many-statements
    logging.basicConfig(format='%(asctime)s %(levelname)s %(filename)s:%(lineno)s] %(message)s',
                        level=logging.DEBUG)

    expr = '1 + 2'
    num = 10000

    logging.info('Creating WasmJS (including compiling qjs-wasi-reactor.wasm).')
    js = wasmjs.WasmJS()

    logging.info('Creating WasmJS.')
    js = wasmjs.WasmJS()
    logging.info('Timing eval_to_jsval(expr).')
    start = time.time()
    for _ in range(num):
        with js._api.eval_to_jsval(expr) as jsval:
            data = jsval.to_string()
        assert data == '3'
    end = time.time()
    logging.info('%i iterations took %s seconds.', num, end - start)

    logging.info('Creating WasmJS.')
    js = wasmjs.WasmJS()
    eval_bootstrap = """
globalThis.__eval_json = function(src) {
  try {
    return JSON.stringify({ok: true, value: eval(src)});
  } catch (e) {
    return JSON.stringify({ok: false, error: String(e)});
  }
};
"""
    logging.info('Installing globalThis.__eval_json.')
    with js._api.eval_to_jsval(eval_bootstrap):
        pass
    logging.info("Timing eval_to_jsval(f'__eval_json({json.dumps(expr)})').")
    start = time.time()
    for _ in range(num):
        with js._api.eval_to_jsval(f'__eval_json({json.dumps(expr)})') as jsval:
            data = json.loads(jsval.to_string())
        assert data.get('value') == 3
    end = time.time()
    logging.info('%i iterations took %s seconds.', num, end - start)

    logging.info('Creating WasmJS.')
    js = wasmjs.WasmJS()
    eval_nostringify_bootstrap = """
globalThis.__eval_json_nostringify = function(src) {
  try {
    return {ok: true, value: eval(src)};
  } catch (e) {
    return {ok: false, error: String(e)};
  }
};
"""
    logging.info('Installing globalThis.__eval_json_nostringify.')
    with js._api.eval_to_jsval(eval_nostringify_bootstrap):
        pass
    logging.info("Timing eval_to_jsval(f'__eval_json_nostringify({json.dumps(expr)})').to_json().")
    start = time.time()
    for _ in range(num):
        with js._api.eval_to_jsval(f'__eval_json_nostringify({json.dumps(expr)})') as jsval:
            with jsval.to_json() as jsonval:
                data = json.loads(jsonval.to_string())
        assert data.get('value') == 3
    end = time.time()
    logging.info('%i iterations took %s seconds.', num, end - start)

    logging.info('Creating WasmJS.')
    js = wasmjs.WasmJS()
    call_bootstrap = """
function __eval_json(src) {
  try {
    return JSON.stringify({ok: true, value: eval(src)});
  } catch (e) {
    return JSON.stringify({ok: false, error: String(e)});
  }
}

__eval_json;
"""
    logging.info('Building eval_json callable.')
    eval_json = js._api.eval_to_jsval(call_bootstrap)
    logging.info('Timing call_to_jsval(eval_json.nanbox, expr).')
    start = time.time()
    for _ in range(num):
        with js._api.call_to_jsval(eval_json.nanbox, expr) as jsval:
            data = json.loads(jsval.to_string())
        assert data.get('value') == 3
    end = time.time()
    logging.info('%i iterations took %s seconds.', num, end - start)

    logging.info('Creating WasmJS.')
    js = wasmjs.WasmJS()
    logging.info('Timing eval_to_jsval(call_bootstrap); call_to_jsval(eval_json.nanbox, expr).')
    start = time.time()
    for _ in range(num):
        with js._api.eval_to_jsval(call_bootstrap) as eval_json:
            with js._api.call_to_jsval(eval_json.nanbox, expr) as jsval:
                data = json.loads(jsval.to_string())
        assert data.get('value') == 3
    end = time.time()
    logging.info('%i iterations took %s seconds.', num, end - start)


if __name__ == '__main__':
    main()
