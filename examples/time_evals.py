"""Quick timing tests of different potential WasmJS.eval implementations."""

import inspect
import json
import logging
import re
import textwrap
import time

from wasmjs import wasmjs


class _Logger:
    _cases = []

    def __init_subclass__(cls):
        cls._cases.append(cls)


class _Base(wasmjs.WasmJS, _Logger):

    def __init__(self):
        super().__init__()
        if self._helper_expr:
            self._helper = self._inst.api.js.eval_to_jsval(self._helper_expr)

    _bootstrap = None
    _helper_expr = None

    def eval(self, expr):
        with self._inst.api.js.eval_to_jsval(expr) as jsval:
            return jsval.decode()


class _1(_Base):

    def eval(self, expr):
        with self._inst.api.js.eval_to_jsval(expr) as jsval:
            with jsval.to_json() as jsonval:
                return json.loads(jsonval.decode())


class _2(_Base):

    def eval(self, expr):
        with self._inst.api.js.eval_to_jsval(f'JSON.stringify({expr})') as jsval:
            return json.loads(jsval.decode())


class _3(_Base):

    def eval(self, expr):
        with self._inst.api.js.eval_to_jsval(f'eval({json.dumps(expr)})') as jsval:
            return jsval.decode()


class _4(_Base):

    def eval(self, expr):
        with self._inst.api.js.eval_to_jsval(f'eval({json.dumps(expr)})') as jsval:
            with jsval.to_json() as jsonval:
                return json.loads(jsonval.decode())


class _5(_Base):

    def eval(self, expr):
        with self._inst.api.js.eval_to_jsval(f'JSON.stringify(eval({json.dumps(expr)}))') as jsval:
            return json.loads(jsval.decode())


class _6(_Base):
    _bootstrap = 'globalThis.__eval_helper = src => eval(src);'

    def eval(self, expr):
        with self._inst.api.js.eval_to_jsval(f'__eval_helper({json.dumps(expr)})') as jsval:
            return jsval.decode()


class _7(_Base):
    _bootstrap = 'globalThis.__eval_helper = src => eval(src);'

    def eval(self, expr):
        with self._inst.api.js.eval_to_jsval(f'__eval_helper({json.dumps(expr)})') as jsval:
            with jsval.to_json() as jsonval:
                return json.loads(jsonval.decode())


class _8(_Base):
    _bootstrap = 'globalThis.__eval_helper = src => JSON.stringify(eval(src));'

    def eval(self, expr):
        with self._inst.api.js.eval_to_jsval(f'__eval_helper({json.dumps(expr)})') as jsval:
            return json.loads(jsval.decode())


class _9(_Base):
    _bootstrap = 'globalThis.__eval_helper = src => ({value: eval(src)});'

    def eval(self, expr):
        with self._inst.api.js.eval_to_jsval(f'__eval_helper({json.dumps(expr)})') as jsval:
            with jsval.to_json() as jsonval:
                return json.loads(jsonval.decode())['value']


class _10(_Base):
    _bootstrap = 'globalThis.__eval_helper = src => JSON.stringify({value: eval(src)});'

    def eval(self, expr):
        with self._inst.api.js.eval_to_jsval(f'__eval_helper({json.dumps(expr)})') as jsval:
            return json.loads(jsval.decode())['value']


class _11(_Base):
    _helper_expr = 'eval'

    def eval(self, expr):
        with self._inst.api.js.call_to_jsval(self._helper.nanbox, expr) as jsval:
            return jsval.decode()


class _12(_Base):
    _helper_expr = 'src => eval(src)'

    def eval(self, expr):
        with self._inst.api.js.call_to_jsval(self._helper.nanbox, expr) as jsval:
            return jsval.decode()


class _13(_Base):
    _helper_expr = 'src => eval(src)'

    def eval(self, expr):
        with self._inst.api.js.call_to_jsval(self._helper.nanbox, expr) as jsval:
            with jsval.to_json() as jsonval:
                return json.loads(jsonval.decode())


class _14(_Base):
    _helper_expr = 'src => JSON.stringify(eval(src))'

    def eval(self, expr):
        with self._inst.api.js.call_to_jsval(self._helper.nanbox, expr) as jsval:
            return json.loads(jsval.decode())


def main():  # pylint: disable=missing-function-docstring
    logging.basicConfig(format='%(asctime)s %(levelname)s %(filename)s:%(lineno)s] %(message)s',
                        level=logging.DEBUG)

    logging.info('Creating WasmJS (including compiling qjs-wasi-reactor.wasm).')
    wasmjs.WasmJS()

    expr = '1 + 2'
    num = 10000
    trials = []
    # pylint: disable=protected-access
    for cls in _Base._cases:
        source = textwrap.dedent('\n'.join(inspect.getsource(cls.eval).splitlines()[1:]))
        if cls._helper_expr:
            source = f'_helper = eval({repr(cls._helper_expr)})\n{source}'
        if cls._bootstrap:
            source = f'eval({repr(cls._bootstrap)})\n{source}'
        logging.info('Testing %s.', re.sub('\n[\n ]*', '; ', source.strip()).replace(':;', ':'))
        js = cls()
        start = time.time()
        for _ in range(num):
            assert js.eval(expr) == 3
        end = time.time()
        logging.info('=== %s', end - start)
        trials.append(((end - start) / num, source))

    for calltime, source in sorted(trials):
        for line in source.splitlines():
            print(f'- {line}')
        print(f'=== {int(1_000_000 * calltime)} \xb5s')


if __name__ == '__main__':
    main()
