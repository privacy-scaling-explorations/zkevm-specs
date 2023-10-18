from typing import Tuple, Set
from .arithmetic import (
    FQ,
    RLC,
    Word,
)
from eth_utils import keccak


class KeccakTable:
    # The columns are: (is_enabled, input_rlc, input_len, output)
    table: Set[Tuple[FQ, FQ, FQ, Word]]

    def __init__(self):
        self.table = set()
        self.table.add((FQ(0), FQ(0), FQ(0), Word(0)))  # Add all 0s row

    def add(self, input: bytes, keccak_randomness: FQ):
        output = keccak(input)
        self.table.add(
            (
                FQ(1),
                RLC(input, keccak_randomness, n_bytes=64).expr(),
                FQ(len(input)),
                Word(output),
            )
        )

    def lookup(self, is_enabled: FQ, input_rlc: FQ, input_len: FQ, output: Word, assert_msg: str):
        assert (is_enabled, input_rlc, input_len, output) in self.table, (
            f"{assert_msg}: {(is_enabled, input_rlc, input_len, output)} "
            + "not found in the lookup table"
        )
