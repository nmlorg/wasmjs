"""Simple JS REPL."""

import argparse
import logging
import readline  # Infects input() at import. (pylint: disable=unused-import)

from wasmjs import wasmjs


def main():  # pylint: disable=missing-docstring
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    logging.basicConfig(
        format='%(asctime)s %(levelname)s %(threadName)s %(filename)s:%(lineno)s] %(message)s',
        level=args.verbose and logging.DEBUG or logging.INFO)

    try:
        js = wasmjs.WasmJS()
    except FileNotFoundError:
        print('Make sure https://github.com/quickjs-ng/quickjs/releases/download/v0.13.0/'
              'qjs-wasi-reactor.wasm is available in the current directory.')
        return

    while True:
        try:
            line = input('>>> ')
        except EOFError:
            print()
            break
        except KeyboardInterrupt:
            print()
            continue

        try:
            print(repr(js.eval(line)))
        except wasmjs.JSError as e:
            print('Exception:', e)


if __name__ == '__main__':
    main()
