from typing import Sequence, Union


def assert_bool(value: Union[int, bool]):
    assert value in [0, 1]


def assert_addition(bytes_a: Sequence[int], bytes_b: Sequence[int], bytes_c: Sequence[int], carries: Sequence[int]):
    for idx, (a, b, c, carry) in enumerate(zip(bytes_a, bytes_b, bytes_c, carries)):
        assert carry * 256 + c == a + b + (0 if idx == 0 else carries[idx - 1])
