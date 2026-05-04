"""Quick timing tests of different potential WasmJS.eval implementations."""

import json
import logging
import re
import time

from wasmjs import wasmjs


class _Logger:
    _cases = []

    def __init_subclass__(cls):
        cls._cases.append(cls)


class Base(wasmjs.WasmJS, _Logger):
    """eval_to_jsval(expr)"""

    _bootstrap = ''

    def eval(self, expr):
        with self._api.eval_to_jsval(expr) as jsval:
            return jsval.decode()


# pylint: disable=function-redefined

class _(Base):
    """json.loads(JSONStringify(eval_to_jsval(expr)))"""

    def eval(self, expr):
        with self._api.eval_to_jsval(expr) as jsval:
            with jsval.to_json() as jsonval:
                return json.loads(jsonval.decode())


class _(Base):
    """s = f'JSON.stringify({expr})'
       json.loads(eval_to_jsval(s))
    """

    def eval(self, expr):
        with self._api.eval_to_jsval(f'JSON.stringify({expr})') as jsval:
            return json.loads(jsval.decode())


class _(Base):
    """s = f'eval({json.dumps(expr)})'
       eval_to_jsval(s)
    """

    def eval(self, expr):
        with self._api.eval_to_jsval(f'eval({json.dumps(expr)})') as jsval:
            return jsval.decode()


class _(Base):
    """s = f'eval({json.dumps(expr)})'
       json.loads(JSONStringify(eval_to_jsval(s))
    """

    def eval(self, expr):
        with self._api.eval_to_jsval(f'eval({json.dumps(expr)})') as jsval:
            with jsval.to_json() as jsonval:
                return json.loads(jsonval.decode())


class _(Base):
    """s = f'JSON.stringify(eval({json.dumps(expr)}))'
       json.loads(eval_to_jsval(s))
    """

    def eval(self, expr):
        with self._api.eval_to_jsval(f'JSON.stringify(eval({json.dumps(expr)}))') as jsval:
            return json.loads(jsval.decode())


class _(Base):
    """[__eval_helper = src => eval(src)]
       s = f'__eval_helper({json.dumps(expr)})'
       eval_to_jsval(s)
    """

    _bootstrap = 'globalThis.__eval_helper = src => eval(src);'

    def eval(self, expr):
        with self._api.eval_to_jsval(f'__eval_helper({json.dumps(expr)})') as jsval:
            return jsval.decode()


class _(Base):
    """[__eval_helper = src => eval(src)]
       s = f'__eval_helper({json.dumps(expr)})'
       json.loads(JSONStringify(eval_to_jsval(s)))
    """

    _bootstrap = 'globalThis.__eval_helper = src => eval(src);'

    def eval(self, expr):
        with self._api.eval_to_jsval(f'__eval_helper({json.dumps(expr)})') as jsval:
            with jsval.to_json() as jsonval:
                return json.loads(jsonval.decode())


class _(Base):
    """[__eval_helper = src => JSON.stringify(eval(src))]
       s = f'__eval_helper({json.dumps(expr)})'
       json.loads(eval_to_jsval(s))
    """

    _bootstrap = 'globalThis.__eval_helper = src => JSON.stringify(eval(src));'

    def eval(self, expr):
        with self._api.eval_to_jsval(f'__eval_helper({json.dumps(expr)})') as jsval:
            return json.loads(jsval.decode())


class _(Base):
    """[__eval_helper = src => ({value: eval(src)})]
       s = f'__eval_helper({json.dumps(expr)})'
       json.loads(JSONStringify(eval_to_jsval(s)))['value']
    """

    _bootstrap = 'globalThis.__eval_helper = src => ({value: eval(src)});'

    def eval(self, expr):
        with self._api.eval_to_jsval(f'__eval_helper({json.dumps(expr)})') as jsval:
            with jsval.to_json() as jsonval:
                return json.loads(jsonval.decode())['value']


class _(Base):
    """[__eval_helper = src => JSON.stringify({value: eval(src)})]
       s = f'__eval_helper({json.dumps(expr)})'
       json.loads(eval_to_jsval(s))['value']
    """

    _bootstrap = 'globalThis.__eval_helper = src => JSON.stringify({value: eval(src)});'

    def eval(self, expr):
        with self._api.eval_to_jsval(f'__eval_helper({json.dumps(expr)})') as jsval:
            return json.loads(jsval.decode())['value']


class _(Base):
    """_eval = [eval]
       call_to_jsval(_eval, expr)
    """

    def __init__(self):
        super().__init__()
        self._eval = self._api.eval_to_jsval('eval')

    def eval(self, expr):
        with self._api.call_to_jsval(self._eval.nanbox, expr) as jsval:
            return jsval.decode()


class _(Base):
    """_eval_helper = [src => eval(src)]
       call_to_jsval(_eval_helper, expr)
    """

    def __init__(self):
        super().__init__()
        self._eval_helper = self._api.eval_to_jsval('src => eval(src)')

    def eval(self, expr):
        with self._api.call_to_jsval(self._eval_helper.nanbox, expr) as jsval:
            return jsval.decode()


class _(Base):
    """_eval_helper = [src => eval(src)]
       json.loads(JSONStringify(call_to_jsval(_eval_helper, expr)))
    """

    def __init__(self):
        super().__init__()
        self._eval_helper = self._api.eval_to_jsval('src => eval(src)')

    def eval(self, expr):
        with self._api.call_to_jsval(self._eval_helper.nanbox, expr) as jsval:
            with jsval.to_json() as jsonval:
                return json.loads(jsonval.decode())


class _(Base):
    """_eval_helper = [src => JSON.stringify(eval(src))]
       json.loads(call_to_jsval(_eval_helper, expr))
    """

    def __init__(self):
        super().__init__()
        self._eval_helper = self._api.eval_to_jsval('src => JSON.stringify(eval(src))')

    def eval(self, expr):
        with self._api.call_to_jsval(self._eval_helper.nanbox, expr) as jsval:
            return json.loads(jsval.decode())


def main():  # pylint: disable=missing-function-docstring
    logging.basicConfig(format='%(asctime)s %(levelname)s %(filename)s:%(lineno)s] %(message)s',
                        level=logging.DEBUG)

    logging.info('Creating WasmJS (including compiling qjs-wasi-reactor.wasm).')
    wasmjs.WasmJS()

    expr = '1 + 2'
    num = 10000
    trials = []
    for cls in Base._cases:  # pylint: disable=protected-access
        logging.info('Testing %s.', re.sub('\n *', '; ', cls.__doc__.strip()))
        js = cls()
        start = time.time()
        for _ in range(num):
            assert js.eval(expr) == 3
        end = time.time()
        logging.info('=== %s', end - start)
        trials.append((end - start, cls.__doc__))

    for duration, doc in sorted(trials):
        for line in doc.strip().splitlines():
            print(f'- {line.strip()}')
        print(f'=== {int(1_000_000 * duration / num)} \xb5s')


if __name__ == '__main__':
    main()
