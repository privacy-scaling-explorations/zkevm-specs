from typing import Sequence

from ..encoding import LookupTable, U8, is_circuit_code, u256_to_u8s


class SignByteTable(LookupTable):
    """
    value: 8 bits 0..256
    sign: 8 bits (0, 0xFF)
    (2 columns and 2**8 rows)
    """

    def __init__(self):
        super().__init__(["value", "sign"])
        for v in range(0, 2**8):
            self.add_row(value=v, sign=(v >> 7) * 0xFF)


@is_circuit_code
def check_signextend(
    v8s: Sequence[U8],
    i8s: Sequence[U8],
    r8s: Sequence[U8],
    sign_byte: U8,
    selectors: Sequence[U8],
    sign_byte_table: SignByteTable,
):
    assert len(v8s) == len(i8s) == len(r8s) == 32
    assert len(selectors) == 31

    # Any index value >= 256 always returns the same value
    is_msb_sum_zero = sum(i8s[1:]) == 0
    # Check byte per byte to see if the byte was selected.
    # We're only directly checking the LSB byte
    # of the index here, so also make sure the byte
    # is only copied when index < 256.
    # There is no need to check the MSB, even if the MSB is selected
    # no bytes need to be changed (so this loops only up to 31).
    selected_byte = 0
    for i in range(31):
        is_selected = (i8s[0] == i) and is_msb_sum_zero
        selected_byte += v8s[i] * is_selected
        # Verify the selector
        assert is_selected + (selectors[i - 1] if i > 0 else 0) == selectors[i]

    # Lookup the sign byte which will be used for doing the extending
    assert sign_byte_table.lookup(value=selected_byte, sign=sign_byte)

    # Byte 0 always remains the same.
    # All other bytes need to be changed to the sign byte when the selector is enabled.
    # When a byte was selected all the **following** bytes need to be replaced,
    # (hence the `selectors[i-1]`).
    for i in range(0, 32):
        if i == 0:
            assert r8s[i] == v8s[i]
        else:
            assert r8s[i] == sign_byte if selectors[i - 1] else v8s[i]


def test_check_byte():
    pos_value = [0b01111111] * 32
    neg_value = [0b10000000] * 32

    pos_extend = 0
    neg_extend = 0xFF

    sign_byte_table = SignByteTable()

    for [value, sign_byte] in [[pos_value, pos_extend], [neg_value, neg_extend]]:
        for i in range(1024):
            i8s = u256_to_u8s(i)

            r8s = value[:]
            selectors = [0] * 31
            for j in range(32):
                if j > i:
                    r8s[j] = sign_byte
                    selectors[j - 1] = 1

            check_signextend(value, i8s, r8s, sign_byte if i < 31 else 0, selectors, sign_byte_table)
