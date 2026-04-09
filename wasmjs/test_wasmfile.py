"""Tests for wasmjs.wasmfile."""

from wasmjs import wasmfile

UNSET_DATA_SENTINEL = 0xf9
FREED_DATA_SENTINEL = 0xfa
FREED_HEADER_SENTINEL = 0xfbfc

STUB_MODULE = wasmfile.WasmFile(wasm=f"""
(module
  (memory (export "memory") 1)

  ;; int heap_end = 0;
  (global $heap_end (export "heap_end") (mut i32) (i32.const 0))

  ;; void *malloc(int size)
  (func $malloc (export "malloc") (param $size i32) (result i32)
    (local $header i32)
    (local $buf i32)

    ;; header = heap_end
    (local.set $header (global.get $heap_end))

    ;; buf = header + 2
    (local.set $buf (i32.add (local.get $header) (i32.const 2)))

    ;; heap_end = buf + size
    (global.set $heap_end (i32.add (local.get $buf) (local.get $size)))

    ;; *((uint16_t *)header) = size
    (i32.store16 (local.get $header) (local.get $size))

    ;; memset(buf, UNSET_DATA_SENTINEL, size)
    (memory.fill (local.get $buf) (i32.const {UNSET_DATA_SENTINEL}) (local.get $size))

    ;; return buf
    local.get $buf
  )

  ;; void free(void *buf)
  (func $free (export "free") (param $buf i32)
    (local $header i32)
    (local $size i32)

    ;; header = buf - 2
    (local.set $header (i32.sub (local.get $buf) (i32.const 2)))

    ;; size = *((uint16_t *)header)
    (local.set $size (i32.load16_u (local.get $header)))

    ;; memset(buf, FREED_DATA_SENTINEL, size)
    (memory.fill (local.get $buf) (i32.const {FREED_DATA_SENTINEL}) (local.get $size))

    ;; *((uint16_t *)header) = FREED_HEADER_SENTINEL
    (i32.store16 (local.get $header) (i32.const {FREED_HEADER_SENTINEL}))
  )
)
""")


def test_write_string():
    """Test _Instance.write_string."""

    def _allmem():
        return inst.exports.memory.read(0, inst.exports.heap_end())

    inst = STUB_MODULE.instantiate()
    assert _allmem() == b''
    with inst.write_string('hello') as hello:
        assert hello.offset == 2
        assert _allmem() == b'\x06\0hello\0'
        with inst.write_string('w\u2022rld') as world:
            assert world.offset == 10
            assert '\u2022'.encode('utf-8') == b'\xe2\x80\xa2'
            assert _allmem() == b'\x06\0hello\0\x08\0w\xe2\x80\xa2rld\0'
        assert _allmem() == b'\x06\0hello\0\xfc\xfb\xfa\xfa\xfa\xfa\xfa\xfa\xfa\xfa'
    assert _allmem() == b'\xfc\xfb\xfa\xfa\xfa\xfa\xfa\xfa\xfc\xfb\xfa\xfa\xfa\xfa\xfa\xfa\xfa\xfa'
