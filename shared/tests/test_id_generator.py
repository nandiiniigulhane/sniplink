import pytest
from shared.id_generator import encode_base62, decode_base62, COUNTER_START, BASE, BASE62_ALPHABET


def test_encode_zero():
    assert encode_base62(0) == "0"


def test_encode_one():
    assert encode_base62(1) == "1"


def test_encode_sixty_one():
    assert encode_base62(61) == "Z"


def test_encode_sixty_two():
    assert encode_base62(62) == "10"


def test_encode_large():
    encoded = encode_base62(COUNTER_START)
    assert len(encoded) >= 6


def test_decode_zero():
    assert decode_base62("0") == 0


def test_decode_abc():
    result = decode_base62("abc")
    assert result > 0


def test_roundtrip_small():
    for n in [0, 1, 10, 61, 62, 100, 1000]:
        assert decode_base62(encode_base62(n)) == n


def test_roundtrip_large():
    for n in [COUNTER_START, COUNTER_START + 1, 1234567890123]:
        assert decode_base62(encode_base62(n)) == n


def test_roundtrip_all_chars():
    for i, ch in enumerate(BASE62_ALPHABET):
        assert decode_base62(ch) == i


def test_encode_then_decode_idempotent():
    code = encode_base62(COUNTER_START)
    assert encode_base62(decode_base62(code)) == code


def test_decode_invalid_char_raises():
    with pytest.raises(ValueError):
        decode_base62("!")


def test_decode_hyphen_raises():
    with pytest.raises(ValueError):
        decode_base62("abc-123")


def test_decode_space_raises():
    with pytest.raises(ValueError):
        decode_base62("abc 123")


def test_base_constant():
    assert BASE == 62


def test_alphabet_length():
    assert len(BASE62_ALPHABET) == 62


def test_counter_start_gives_6_chars_min():
    assert len(encode_base62(COUNTER_START)) == 6
