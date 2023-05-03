from dataclasses import dataclass
from typing import Tuple, List, Union, Set
from zkevm_specs.util.arithmetic import bytes_to_fq

from zkevm_specs.util.param import N_BYTES_WORD

from .util import (
    FQ,
    Word,
    RLC,
    WordOrValue,
    U8,
    U64,
    U160,
    U256,
    PUBLIC_INPUTS_BLOCK_LEN as BLOCK_LEN,
    PUBLIC_INPUTS_TX_LEN as TX_LEN,
    GAS_COST_TX_CALL_DATA_PER_NON_ZERO_BYTE,
    GAS_COST_TX_CALL_DATA_PER_ZERO_BYTE,
    Expression,
    is_circuit_code,
)
from .tx_circuit import Tag as TxTag
from eth_utils import keccak
from .evm_circuit.table import KeccakTableRow, lookup, TableRow


@dataclass
class BlockTable:
    table: List[WordOrValue]

    def __init__(self):
        self.table = []

    def add(self, value: WordOrValue):
        self.table.append(value)


@dataclass
class TxTableRow:
    tx_id: FQ
    tag: FQ  # Fixed Column
    index: FQ
    value: WordOrValue


@dataclass
class TxTable:
    table: List[TxTableRow]

    def __init__(self):
        self.table = []

    def add(self, tx_id: FQ, tag: FQ, index: FQ, value: WordOrValue):
        self.table.append(TxTableRow(tx_id, tag, index, value))


@dataclass(frozen=True)
class TxCallDataGasCostAccRow(TableRow):
    tx_id: Expression
    is_final: FQ
    gas_cost_acc: FQ


@dataclass(frozen=True)
class FixedU16Row(TableRow):
    value: FQ


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
                RLC(bytes(reversed(input)), keccak_randomness, n_bytes=len(input)).expr(),
                FQ(len(input)),
                Word(output),
            )
        )

    def lookup(self, is_enabled: FQ, input_rlc: FQ, input_len: FQ, output: Word, assert_msg: str):
        assert (is_enabled, input_rlc, input_len, output) in self.table, (
            f"{assert_msg}: {(is_enabled, input_rlc, input_len, output)} "
            + "not found in the lookup table"
        )


@dataclass
class Row:
    """PublicInputs circuit row"""

    q_bytes_last: FQ
    q_tx_table: FQ
    q_tx_calldata: FQ
    q_tx_calldata_start: FQ
    q_rpi_keccak_lookup: FQ
    q_rpi_value_start: FQ  # Fixed Column

    tx_id_inv: FQ  # (tx_tag - CallDataLength)^(-1) when q_tx_table = 1
    # tx_id^(-1) when q_tx_calldata = 1
    tx_value_lo_inv: FQ
    tx_id_diff_inv: FQ
    calldata_gas_cost: FQ
    is_final: FQ

    rpi_bytes: FQ
    rpi_bytes_keccakrlc: FQ
    rpi_value_lc: FQ
    rpi_digest_word: Word

    q_rpi_byte_enable: FQ

    keccak_table: KeccakTableRow
    tx_table: TxTableRow


@dataclass
class PublicInputs:
    """Public Inputs of the PublicInputs circuit"""

    pi_keccak: Word

    # FIXME temporarily put state_root and pre_state_root here, since no table refer to those
    state_root: Word
    state_root_prev: Word


@is_circuit_code
def check_row(
    row: Row,
    row_next: Row,
    calldata_gas_cost_table: Set[TxCallDataGasCostAccRow],
    fixed_u16_table: Set[FixedU16Row],
    keccak_table: KeccakTable,
    circuit_len: FQ,
):
    q_bytes_last = row.q_bytes_last
    q_rpi_byte_enable = row.q_rpi_byte_enable

    # gate 1 and gate 2 are compensation branch
    # 1: rpi_bytes_keccakrlc[last] = rpi_bytes[last]
    assert q_rpi_byte_enable * q_bytes_last * (row.rpi_bytes_keccakrlc - row.rpi_bytes) == FQ(0)

    # 2: rpi_bytes_keccakrlc[i] = keccak_rand * rpi_bytes_keccakrlc[i+1] + rpi_bytes[i]"
    assert (
        q_rpi_byte_enable
        * (FQ(1) - q_bytes_last)
        * (row.rpi_bytes_keccakrlc - row_next.rpi_bytes_keccakrlc * keccak_rand - row.rpi_bytes)
    )

    # gate 3 and gate 4 are compensation branch
    # 3: rpi_value_lc[i] = rpi_value_lc[i+1] * byte_pow_base + rpi_bytes[i]
    assert row.q_rpi_byte_enable * (FQ(1) - row.q_rpi_value_start) * (
        row.rpi_value_lc - row_next.rpi_value_lc * byte_pow_base - row.rpi_bytes
    ) == FQ(0)

    # 4. rpi_value_lc[i] = rpi_bytes[i]
    assert row.q_rpi_byte_enable * row.q_rpi_value_start * (row.rpi_value_lc - row.rpi_bytes) == FQ(
        0
    )

    # 5. lookup rpi_bytes_keccakrlc against rpi_digest_word
    keccak_table.lookup(
        row.q_rpi_keccak_lookup,
        row.q_rpi_keccak_lookup * row.rpi_bytes_keccakrlc,
        row.q_rpi_keccak_lookup * circuit_len,
        row.rpi_digest_word.select(row.q_rpi_keccak_lookup),
        "lookup not found",
    )

    zero = FQ(0)
    one = FQ(1)
    if row.q_tx_calldata != zero:
        assert row.tx_table.tx_id * (one - row.tx_id_inv * row.tx_table.tx_id) == zero
        assert (
            row.tx_table.value.lo.expr()
            * (one - row.tx_value_lo_inv * row.tx_table.value.lo.expr())
            == zero
        )
        assert (row_next.tx_table.tx_id - row.tx_table.tx_id) * (
            one - row.tx_id_diff_inv * (row_next.tx_table.tx_id - row.tx_table.tx_id)
        ) == zero
        is_tx_id_nonzero = row.tx_table.tx_id * row.tx_id_inv
        is_tx_id_next_nonzero = row_next.tx_table.tx_id * row_next.tx_id_inv
        is_tx_id_zero = one - is_tx_id_nonzero
        is_tx_id_next_zero = one - is_tx_id_next_nonzero
        tx_id_not_equal_to_next = (
            row_next.tx_table.tx_id - row.tx_table.tx_id
        ) * row.tx_id_diff_inv
        tx_id_equal_to_next = one - tx_id_not_equal_to_next

        is_byte_nonzero = row.tx_table.value.lo.expr() * row.tx_value_lo_inv
        is_byte_next_nonzero = row_next.tx_table.value.lo.expr() * row_next.tx_value_lo_inv
        is_byte_zero = one - is_byte_nonzero
        is_byte_next_zero = one - is_byte_next_nonzero

        default_calldata_row_constraints = [
            is_tx_id_zero * row.tx_table.tx_id,
            is_tx_id_zero * row_next.tx_table.tx_id,
            is_tx_id_zero * row.is_final,
            is_tx_id_zero * row.calldata_gas_cost,
        ]

        for cons in default_calldata_row_constraints:
            assert cons == zero

        gas_cost = (
            FQ(GAS_COST_TX_CALL_DATA_PER_NON_ZERO_BYTE) * is_byte_nonzero
            + FQ(GAS_COST_TX_CALL_DATA_PER_ZERO_BYTE) * is_byte_zero
        )
        gas_cost_next = (
            FQ(GAS_COST_TX_CALL_DATA_PER_NON_ZERO_BYTE) * is_byte_next_nonzero
            + FQ(GAS_COST_TX_CALL_DATA_PER_ZERO_BYTE) * is_byte_next_zero
        )

        tx_id_diff_minus_one = row_next.tx_table.tx_id - row.tx_table.tx_id - one
        tx_id_diff_minus_one_query = {
            "value": tx_id_not_equal_to_next * is_tx_id_next_nonzero * tx_id_diff_minus_one
        }
        lookup(FixedU16Row, fixed_u16_table, tx_id_diff_minus_one_query)

        idx_of_same_tx_constraint = tx_id_equal_to_next * (
            row_next.tx_table.index - row.tx_table.index - one
        )
        idx_of_next_tx_constraint = (
            row_next.tx_table.tx_id - row.tx_table.tx_id
        ) * row_next.tx_table.index
        gas_cost_of_same_tx_constraint = tx_id_equal_to_next * (
            row_next.calldata_gas_cost - row.calldata_gas_cost - gas_cost_next
        )
        gas_cost_of_next_tx_constraint = (
            is_tx_id_next_nonzero
            * (row_next.tx_table.tx_id - row.tx_table.tx_id)
            * (row_next.calldata_gas_cost - gas_cost_next)
        )
        gas_cost_of_last_tx_constraint = is_tx_id_next_zero * row_next.calldata_gas_cost
        is_final_of_same_tx_constraint = tx_id_equal_to_next * row.is_final
        is_final_of_next_tx_constraint = (row_next.tx_table.tx_id - row.tx_table.tx_id) * (
            row.is_final - one
        )

        constraints = [
            is_tx_id_nonzero * idx_of_same_tx_constraint,
            is_tx_id_nonzero * idx_of_next_tx_constraint,
            is_tx_id_nonzero * gas_cost_of_same_tx_constraint,
            is_tx_id_nonzero * gas_cost_of_next_tx_constraint,
            is_tx_id_nonzero * gas_cost_of_last_tx_constraint,
            is_tx_id_nonzero * is_final_of_same_tx_constraint,
            is_tx_id_nonzero * is_final_of_next_tx_constraint,
        ]

        for cons_id, cons in enumerate(constraints):
            assert cons == zero

        assert row.q_tx_calldata_start * is_tx_id_nonzero * row.tx_table.index == zero
        assert (
            row.q_tx_calldata_start * is_tx_id_nonzero * (row.calldata_gas_cost - gas_cost) == zero
        )

    if row.q_tx_table != zero:
        row_is_cdl = row.tx_table.tag - FQ(TxTag.CallDataLength)
        assert row_is_cdl * (one - row.tx_id_inv * row_is_cdl) == zero
        assert (
            row.tx_table.value.lo.expr()
            * (one - row.tx_value_lo_inv * row.tx_table.value.lo.expr())
            == zero
        )

        is_calldata_length_row = one - row_is_cdl * row.tx_id_inv
        is_calldata_length_nonzero = row.tx_table.value.lo.expr() * row.tx_value_lo_inv
        is_calldata_length_zero = one - is_calldata_length_nonzero

        calldata_cost = row_next.tx_table.value.lo.expr()

        assert is_calldata_length_row * is_calldata_length_zero * calldata_cost == zero
        query_condition = is_calldata_length_row * is_calldata_length_nonzero
        query = {
            "tx_id": row.tx_table.tx_id * query_condition,
            "is_final": one * query_condition,
            "gas_cost_acc": calldata_cost * query_condition,
        }
        lookup(TxCallDataGasCostAccRow, calldata_gas_cost_table, query)


@dataclass
class Witness:
    rows: List[Row]  # PublicInputs rows
    public_inputs: PublicInputs  # Public Inputs of the PublicInputs circuit
    calldata_gas_cost_table: Set[TxCallDataGasCostAccRow]
    keccak_table: KeccakTable
    block_table: BlockTable
    tx_table: TxTable
    circuit_len: int
    copy_constrains: List[List[int]]


@is_circuit_code
def verify_circuit(
    witness: Witness,
    MAX_TXS: int,
    MAX_CALLDATA_BYTES: int,
) -> None:
    """
    Entry level circuit verification function
    """

    rows = witness.rows
    calldata_gas_cost_table = witness.calldata_gas_cost_table
    public_inputs = witness.public_inputs
    keccak_table = witness.keccak_table
    block_table = witness.block_table
    tx_table = witness.tx_table
    copy_constrains = witness.copy_constrains

    fixed_u16_table = set([FixedU16Row(FQ(i)) for i in range(1 << 16)])

    # copy constraint from public input to advice column
    assert rows[0].rpi_digest_word == public_inputs.pi_keccak

    # block constrains
    for i in range(BLOCK_LEN // 2 + 1):
        block_row = block_table.table[i]
        if block_row.is_word:
            lo = copy_constrains.pop(0)
            hi = copy_constrains.pop(0)
            assert block_row.lo.expr() == bytes_to_fq(lo)
            assert block_row.hi.expr() == bytes_to_fq(hi)
        else:
            lo = copy_constrains.pop(0)
            assert block_row.value() == bytes_to_fq(lo)

    lo = copy_constrains.pop(0)
    hi = copy_constrains.pop(0)
    assert public_inputs.state_root.lo.expr() == bytes_to_fq(lo)
    assert public_inputs.state_root.hi.expr() == bytes_to_fq(hi)

    lo = copy_constrains.pop(0)
    hi = copy_constrains.pop(0)
    assert public_inputs.state_root_prev.lo.expr() == bytes_to_fq(lo)
    assert public_inputs.state_root_prev.hi.expr() == bytes_to_fq(hi)

    # tx constrains
    tx_len = TX_LEN * MAX_TXS + 1
    for i in range(tx_len):
        row = tx_table.table[i]
        tx_id, index, value = row.tx_id, row.index, row.value
        lo = copy_constrains.pop(0)
        assert tx_id == bytes_to_fq(lo)
        lo = copy_constrains.pop(0)
        assert index == bytes_to_fq(lo)

        if value.is_word:
            lo = copy_constrains.pop(0)
            high = copy_constrains.pop(0)
            assert value.lo.expr() == bytes_to_fq(lo)
            assert value.hi.expr() == bytes_to_fq(high)
        else:
            lo = copy_constrains.pop(0)
            assert value.value() == bytes_to_fq(lo)

    # tx calldata constrains
    calldata_len = MAX_CALLDATA_BYTES
    for i in range(calldata_len):
        value = tx_table.table[tx_len + i].value
        if value.is_word:
            lo = copy_constrains.pop(0)
            high = copy_constrains.pop(0)
            assert value.lo.expr() == bytes_to_fq(lo)
            assert value.hi.expr() == bytes_to_fq(high)
        else:
            lo = copy_constrains.pop(0)
            assert value.value() == bytes_to_fq(lo)

    # check rows
    for i in range(len(rows)):
        row = rows[i]
        row_next = rows[(i + 1) % len(rows)]
        check_row(
            row,
            row_next,
            calldata_gas_cost_table,
            fixed_u16_table,
            keccak_table,
            witness.circuit_len,
        )

    # check copy/permutation constraints


@dataclass
class Block:
    """Block header"""

    hash: U256
    parent_hash: U256
    uncle_hash: U256
    coinbase: U160
    state_root: U256  # State Trie Root
    tx_hash: U256  # Txs Trie Root
    receipt_hash: U256  # Receipts Trie Root
    bloom: bytes  # 256 bytes
    difficulty: U256
    number: U64
    gas_limit: U64
    gas_used: U64
    time: U64
    extra: bytes  # NOTE: We assume this is always an empty byte array
    mix_digest: U256
    nonce: U64
    base_fee: U256  # NOTE: BaseFee was added by EIP-1559 and is ignored in legacy headers.


@dataclass
class Transaction:
    nonce: U64
    gas_price: U256
    gas: U64
    from_addr: U160
    to_addr: Union[None, U160]
    value: U256
    data: bytes
    tx_sign_hash: U256

    @classmethod
    def default(cls):
        return Transaction(U64(0), U256(0), U64(0), U160(0), U160(0), U256(0), bytes([]), U256(0))

    def tx_table_value_column(self) -> List[WordOrValue]:
        """Return the tx table value column corresponding to this tx.  Contains fields and no calldata"""
        column = []
        column.append(WordOrValue(FQ(self.nonce)))  # Nonce
        column.append(WordOrValue(FQ(self.gas)))  # Gas
        column.append(WordOrValue(Word(self.gas_price)))  # GasPrice
        column.append(WordOrValue(FQ(self.from_addr)))  # CallerAddress
        column.append(WordOrValue(FQ(self.to_addr or 0)))  # CalleeAddress
        column.append(WordOrValue(FQ(1 if self.to_addr is None else 0)))  # IsCreate
        column.append(WordOrValue(Word(self.value)))  # Value
        column.append(WordOrValue(FQ(len(self.data))))  # CallDataLength
        call_data_gas_cost = sum(
            [
                (
                    GAS_COST_TX_CALL_DATA_PER_ZERO_BYTE
                    if byte == 0
                    else GAS_COST_TX_CALL_DATA_PER_NON_ZERO_BYTE
                )
                for byte in self.data
            ]
        )
        column.append(WordOrValue(FQ(call_data_gas_cost)))  # CallDataCost
        column.append(WordOrValue(Word(self.tx_sign_hash)))  # TxSignHash
        return column

    def tx_table_raw_bytes_group(self, tx_id: int) -> List[List[int]]:
        raw_bytes_group = []
        self.append_raw_byte_with_id_index(
            raw_bytes_group, tx_id, self.nonce.to_bytes(8, "little")
        )  # Nonce
        self.append_raw_byte_with_id_index(
            raw_bytes_group, tx_id, self.gas.to_bytes(8, "little")
        )  # Gas Limit

        gas_price_lo, gas_price_hi = Word(self.gas_price).to_lo_hi()
        self.append_raw_byte_with_id_index(
            raw_bytes_group,
            tx_id,
            gas_price_lo.n.to_bytes(16, "little"),
            gas_price_hi.n.to_bytes(16, "little"),
        )  # GasPrice
        self.append_raw_byte_with_id_index(
            raw_bytes_group, tx_id, self.from_addr.to_bytes(20, "little")
        )  # CallerAddress
        self.append_raw_byte_with_id_index(
            raw_bytes_group, tx_id, (self.to_addr or U160(0)).to_bytes(20, "little")
        )  # CalleeAddress
        self.append_raw_byte_with_id_index(
            raw_bytes_group,
            tx_id,
            (U64(1) if self.to_addr is None else U64(0)).to_bytes(8, "little"),
        )  # IsCreate
        value_lo, value_hi = Word(self.value).to_lo_hi()
        self.append_raw_byte_with_id_index(
            raw_bytes_group,
            tx_id,
            value_lo.n.to_bytes(16, "little"),
            value_hi.n.to_bytes(16, "little"),
        )  # Value
        self.append_raw_byte_with_id_index(
            raw_bytes_group, tx_id, U64(len(self.data)).to_bytes(8, "little")
        )  # CallDataLength
        call_data_gas_cost = sum(
            [
                (
                    GAS_COST_TX_CALL_DATA_PER_ZERO_BYTE
                    if byte == 0
                    else GAS_COST_TX_CALL_DATA_PER_NON_ZERO_BYTE
                )
                for byte in self.data
            ]
        )
        self.append_raw_byte_with_id_index(
            raw_bytes_group, tx_id, U64(call_data_gas_cost).to_bytes(8, "little")
        )  # CallDataCost
        tx_sign_hash_lo, tx_sign_hash_hi = Word(self.tx_sign_hash).to_lo_hi()
        self.append_raw_byte_with_id_index(
            raw_bytes_group,
            tx_id,
            tx_sign_hash_lo.n.to_bytes(16, "little"),
            tx_sign_hash_hi.n.to_bytes(16, "little"),
        )  # TxSignHash
        return raw_bytes_group

    def append_raw_byte_with_id_index(
        self, raw_byte_value_col: List[int], tx_id: int, value_lo: bytes, value_hi: bytes = None
    ):
        raw_byte_value_col.append(U64(tx_id).to_bytes(8, "little"))
        raw_byte_value_col.append(U64(0).to_bytes(8, "little"))
        raw_byte_value_col.append(value_lo)
        if value_hi:
            raw_byte_value_col.append(value_hi)

    def tx_table_tx_fields(self, tx_id: int) -> Tuple[List[FQ], List[FQ], List[WordOrValue]]:
        """Return the tx table contents corresponding to this tx.  Contains fields and no calldata"""
        tx_id_col = [FQ(tx_id + 1)] * TX_LEN
        index_col = [FQ(0)] * TX_LEN
        value_col = self.tx_table_value_column()
        assert len(value_col) == TX_LEN
        return (tx_id_col, index_col, value_col)


@dataclass
class PublicData:
    chain_id: U64
    block: Block
    state_root_prev: U256
    block_hashes: List[U256]  # 256 previous block hashes
    txs: List[Transaction]

    def block_table_value_column(self) -> List[WordOrValue]:
        """Return the block table value column including the first 0 row"""
        column = []
        column.append(WordOrValue(FQ(0)))  # offset = 0
        column.append(WordOrValue(FQ(self.block.coinbase)))
        column.append(WordOrValue(FQ(self.block.gas_limit)))
        column.append(WordOrValue(FQ(self.block.number)))
        column.append(WordOrValue(FQ(self.block.time)))
        column.append(WordOrValue(Word(self.block.difficulty)))
        column.append(WordOrValue(Word(self.block.base_fee)))
        column.append(WordOrValue(FQ(self.chain_id)))
        assert len(self.block_hashes) == 256
        for block_hash in self.block_hashes:
            column.append(WordOrValue(Word(block_hash)))  # offset = 8
        return column

    def block_table_raw_bytes(self) -> List[int]:
        """Return the block table bytes, including first 0 row"""
        raw_block_value = []

        raw_block_value.append(U8(0).to_bytes(1, "little"))  # offset = 0
        raw_block_value.append(self.block.coinbase.to_bytes(20, "little"))
        raw_block_value.append(self.block.gas_limit.to_bytes(8, "little"))
        raw_block_value.append(self.block.number.to_bytes(8, "little"))
        raw_block_value.append(self.block.time.to_bytes(8, "little"))
        difficulty_lo, difficulty_hi = Word(self.block.difficulty).to_lo_hi()
        raw_block_value.append(difficulty_lo.n.to_bytes(16, "little"))
        raw_block_value.append(difficulty_hi.n.to_bytes(16, "little"))
        base_fee_lo, base_fee_hi = Word(self.block.base_fee).to_lo_hi()
        raw_block_value.append(base_fee_lo.n.to_bytes(16, "little"))
        raw_block_value.append(base_fee_hi.n.to_bytes(16, "little"))
        raw_block_value.append(self.chain_id.to_bytes(8, "little"))
        assert len(self.block_hashes) == 256
        for block_hash in self.block_hashes:
            block_hash_lo, block_hash_hi = Word(block_hash).to_lo_hi()
            raw_block_value.append(block_hash_lo.n.to_bytes(16, "little"))
            raw_block_value.append(block_hash_hi.n.to_bytes(16, "little"))
        return raw_block_value

    def tx_table_raw_bytes_group(self, MAX_TXS: int) -> List[List[int]]:
        """Return the tx table bytes, traverse in row oriented and including first 0 row"""
        raw_bytes_group = []
        assert len(self.txs) > 0
        assert len(self.txs) <= MAX_TXS
        raw_bytes_group.append(U64(0).to_bytes(8, "little"))  # empty id
        raw_bytes_group.append(U64(0).to_bytes(8, "little"))  # empty index
        raw_bytes_group.append(U8(0).to_bytes(1, "little"))  # empty value lo
        for i in range(MAX_TXS):
            tx = Transaction.default()
            if i < len(self.txs):
                tx = self.txs[i]
            raw_bytes_group.extend([group for group in tx.tx_table_raw_bytes_group(i + 1)])
        return raw_bytes_group

    def tx_table_calldata_raw_bytes_group(self, MAX_CALLDATA_BYTES: int) -> List[List[int]]:
        raw_bytes_group = []
        calldata_count = 0
        for i, tx in enumerate(self.txs):
            for byte_index, byte in enumerate(tx.data):
                raw_bytes_group.append(U8(byte).to_bytes(1, "little"))
                calldata_count += 1

        assert calldata_count <= MAX_CALLDATA_BYTES

        for _ in range(MAX_CALLDATA_BYTES - calldata_count):
            raw_bytes_group.append(U8(0).to_bytes(1, "little"))

        return raw_bytes_group

    def tx_table_tx_fields(self, MAX_TXS: int) -> Tuple[List[FQ], List[FQ], List[WordOrValue]]:
        """Return the tx table, static section with tx fields (no calldata)"""
        tx_id_col = []
        index_col = []
        value_col = []
        assert len(self.txs) <= MAX_TXS
        for i in range(MAX_TXS):
            tx = Transaction.default()
            if i < len(self.txs):
                tx = self.txs[i]

            (tx_id_col_i, index_col_i, value_col_i) = tx.tx_table_tx_fields(i)

            tx_id_col.extend(tx_id_col_i)
            index_col.extend(index_col_i)
            value_col.extend(value_col_i)

        return (tx_id_col, index_col, value_col)

    def tx_table_tx_calldata(
        self, MAX_CALLDATA_BYTES: int
    ) -> Tuple[List[FQ], List[FQ], List[WordOrValue], List[FQ], List[FQ]]:
        """Return the tx table, dynamic section with calldata"""
        tx_id_col = []
        index_col = []
        value_col = []
        gas_cost_col = []
        is_final_col = []
        for i, tx in enumerate(self.txs):
            gas_cost_acc = 0
            for byte_index, byte in enumerate(tx.data):
                tx_id_col.append(FQ(i + 1))
                index_col.append(FQ(byte_index))
                value_col.append(WordOrValue(FQ(byte)))
                if byte == 0:
                    gas_cost_acc += GAS_COST_TX_CALL_DATA_PER_ZERO_BYTE
                else:
                    gas_cost_acc += GAS_COST_TX_CALL_DATA_PER_NON_ZERO_BYTE
                if byte_index == len(tx.data) - 1:
                    is_final = 1
                else:
                    is_final = 0
                gas_cost_col.append(FQ(gas_cost_acc))
                is_final_col.append(FQ(is_final))

        assert len(value_col) <= MAX_CALLDATA_BYTES
        calldata_padding = [FQ(0)] * (MAX_CALLDATA_BYTES - len(value_col))
        tx_id_col.extend(calldata_padding)
        index_col.extend(calldata_padding)
        value_col.extend([WordOrValue(v) for v in calldata_padding])
        gas_cost_col.extend(calldata_padding)
        is_final_col.extend(calldata_padding)

        return (tx_id_col, index_col, value_col, gas_cost_col, is_final_col)

    def tx_table(
        self, MAX_TXS: int, MAX_CALLDATA_BYTES: int
    ) -> Tuple[List[FQ], List[FQ], List[WordOrValue]]:
        """Return the complete tx table including the initial 0 row"""
        tx_fields = self.tx_table_tx_fields(MAX_TXS)
        tx_calldata = self.tx_table_tx_calldata(MAX_CALLDATA_BYTES)
        return (
            [FQ(0)] + tx_fields[0] + tx_calldata[0],
            [FQ(0)] + tx_fields[1] + tx_calldata[1],
            [WordOrValue(FQ(0))] + tx_fields[2] + tx_calldata[2],
        )


N_BYTES_ONE = 1
N_BYTES_U64 = 8
N_BYTES_TX = 176
N_BYTES_BLOCK = 8308
N_BYTES_EXTRA_VALUE = N_BYTES_WORD + N_BYTES_WORD
byte_pow_base = FQ(255)
evm_rand = FQ(255)
keccak_rand = FQ(255)


def public_data2witness(
    public_data: PublicData, MAX_TXS: int, MAX_CALLDATA_BYTES: int, rand_rpi: FQ
) -> Witness:
    # TODO Layout of raw_public_inputs:
    #   # Block Table
    #   [0] + [block_table.value.lo] # BLOCK_LEN//2 + 1
    #   [0] + [block_table.value.hi] # BLOCK_LEN//2 + 1
    #   # Extra Fields
    #   [hash.lo, hash.hi] # 2
    #   [state_root.lo, state_root.hi] # 2
    #   [state_root_prev.lo, state_root_prev.hi] # 2
    #   # Tx Table
    #   [0] + [tx_table.id] # TX_LEN * MAX_TXS + 1
    #   [0] + [tx_table.index] # TX_LEN * MAX_TXS + 1
    #   [0] + [tx_table.value.lo] # TX_LEN * MAX_TXS + 1
    #   [tx_table.calldata.lo] # MAX_CALLDATA_BYTES
    #   [0] + [tx_table.value.hi] # TX_LEN * MAX_TXS + 1
    #   [tx_table.calldata.hi] # MAX_CALLDATA_BYTES

    rpi_bytes_group = []

    # Block table
    block_table_value_col = public_data.block_table_value_column()
    block_table_block_value = public_data.block_table_raw_bytes()
    rpi_bytes_group.extend(block_table_block_value)

    # Extra fields
    # rpi_bytes.extend(public_data.block.hash.to_bytes(32, 'little'))  # FIXME
    state_root_lo, state_root_hi = Word(public_data.block.state_root).to_lo_hi()
    rpi_bytes_group.append(state_root_lo.n.to_bytes(16, "little"))
    rpi_bytes_group.append(state_root_hi.n.to_bytes(16, "little"))
    state_root_prev_lo, state_root_prev_hi = Word(public_data.state_root_prev).to_lo_hi()
    rpi_bytes_group.append(state_root_prev_lo.n.to_bytes(16, "little"))
    rpi_bytes_group.append(state_root_prev_hi.n.to_bytes(16, "little"))
    assert flattern_len(rpi_bytes_group) == N_BYTES_ONE + N_BYTES_BLOCK + N_BYTES_EXTRA_VALUE

    # Tx Table
    tx_table_col_oriented = public_data.tx_table(MAX_TXS, MAX_CALLDATA_BYTES)
    (tx_id_col, tx_index_col, tx_value_col) = tx_table_col_oriented
    tx_table_tx_fields = public_data.tx_table_tx_fields(MAX_TXS)
    tx_table_tx_calldata = public_data.tx_table_tx_calldata(MAX_CALLDATA_BYTES)

    # traverse column tuple in row order
    tx_table_raw_bytes_group = public_data.tx_table_raw_bytes_group(MAX_TXS)
    rpi_bytes_group.extend(tx_table_raw_bytes_group)

    keccak_table = KeccakTable()
    block_table = BlockTable()
    tx_table = TxTable()
    assert flattern_len(rpi_bytes_group) == (
        N_BYTES_ONE  # empty block row
        + N_BYTES_BLOCK  # block
        + N_BYTES_EXTRA_VALUE  # extra value
        + N_BYTES_U64 * TX_LEN * MAX_TXS
        + N_BYTES_U64  # tx_id + first empty
        + N_BYTES_U64 * TX_LEN * MAX_TXS
        + N_BYTES_U64  # txindex + first empty
        + N_BYTES_TX * MAX_TXS
        + N_BYTES_ONE  # tx value
    )

    # Tx Calldata
    tx_table_calldata_raw_bytes_group = public_data.tx_table_calldata_raw_bytes_group(
        MAX_CALLDATA_BYTES
    )
    rpi_bytes_group.extend(tx_table_calldata_raw_bytes_group)

    circuit_len = (
        N_BYTES_ONE  # empty block row
        + N_BYTES_BLOCK  # block
        + N_BYTES_EXTRA_VALUE  # extra value
        + N_BYTES_U64 * TX_LEN * MAX_TXS
        + N_BYTES_U64  # tx_id + first empty
        + N_BYTES_U64 * TX_LEN * MAX_TXS
        + N_BYTES_U64  # txindex + first empty
        + N_BYTES_TX * MAX_TXS
        + N_BYTES_ONE  # tx value
        + MAX_CALLDATA_BYTES
    )
    assert flattern_len(rpi_bytes_group) == circuit_len

    rows: List[Row] = []
    calldata_gas_cost_table = [TxCallDataGasCostAccRow(FQ(0), FQ(0), FQ(0))]
    i = circuit_len - 1
    rpi_bytes_keccakrlc = []
    rpi_value_lc = []
    rpi_bytes = []

    for group in reversed(rpi_bytes_group):  # acc from big endian
        for byte_index, byte in enumerate(reversed(group)):
            rpi_bytes.append(byte)

            q_rpi_byte_enable = FQ(1)
            q_bytes_last = FQ(1) if len(rpi_bytes) == 1 else FQ(0)
            q_rpi_keccak_lookup = FQ(1) if i == 0 else FQ(0)  # keccak lookup happened in first row
            q_rpi_value_start = FQ(0)

            if i == circuit_len - 1:
                rpi_bytes_keccakrlc = [FQ(byte)]
            else:
                rpi_bytes_keccakrlc.append(FQ(rpi_bytes_keccakrlc[-1] * keccak_rand + byte))

            if byte_index == 0:
                q_rpi_value_start = FQ(1)
                rpi_value_lc.append(FQ(byte))
            else:
                rpi_value_lc.append(FQ(rpi_value_lc[-1] * byte_pow_base + byte))

            if i < BLOCK_LEN // 2 + 1:
                assert i < len(block_table_value_col)
                block_table.add(block_table_value_col[i])

            # FIXME: extra value not used in any place. Here add 2 copy constraint in block table just for aligment
            if i == BLOCK_LEN // 2 + 1:
                block_table.add(WordOrValue(Word(public_data.block.state_root)))
            if i == BLOCK_LEN // 2 + 2:
                block_table.add(WordOrValue(Word(public_data.state_root_prev)))

            q_tx_table = FQ(0)
            q_tx_calldata = FQ(0)
            q_tx_calldata_start = FQ(0)

            tx_id_inv = FQ(0)
            tx_value_lo_inv = FQ(0)
            tx_id_diff_inv = FQ(0)
            calldata_gas_cost = FQ(0)
            is_final = FQ(0)
            tx_row = TxTableRow(FQ(0), FQ(0), FQ(0), WordOrValue(FQ(0)))
            tx_table_len = TX_LEN * MAX_TXS + 1
            if i < tx_table_len + MAX_CALLDATA_BYTES:
                tx_id = tx_table_col_oriented[0][i]
                index = tx_table_col_oriented[1][i]
                value = tx_table_col_oriented[2][i]
                tag = FQ(TxTag.CallData)
                if i == 0:
                    tag = FQ(0)
                elif i < tx_table_len:
                    # Iterate over TxTag values (until TxTag.TxSignHash) in a cycle
                    tag = FQ((i % TX_LEN))
                    if i % TX_LEN == 0:
                        tag = FQ(TX_LEN)
                if i < tx_table_len:
                    q_tx_table = FQ(1)
                    tx_id_inv = (tag - FQ(TxTag.CallDataLength)).inv()
                    tx_value_lo_inv = value.lo.expr().inv()

                if i >= tx_table_len:
                    q_tx_calldata = FQ(1)
                    tx_id_inv = tx_id.inv()
                    tx_value_lo_inv = value.lo.expr().inv()
                    tx_id_next = FQ(0)
                    if i < tx_table_len + MAX_CALLDATA_BYTES - 1:
                        tx_id_next = tx_table_col_oriented[0][i + 1]
                    tx_id_diff_inv = (tx_id_next - tx_id).inv()
                    calldata_gas_cost = tx_table_tx_calldata[3][i - tx_table_len]
                    is_final = tx_table_tx_calldata[4][i - tx_table_len]
                    calldata_gas_cost_table.append(
                        TxCallDataGasCostAccRow(tx_id, is_final, calldata_gas_cost)
                    )

                if i == tx_table_len:
                    q_tx_calldata_start = FQ(1)
                tx_row = TxTableRow(tx_id, tag, index, value)
                tx_table.add(tx_id, tag, index, value)

            row = Row(
                q_bytes_last,
                q_tx_table,
                q_tx_calldata,
                q_tx_calldata_start,
                q_rpi_keccak_lookup,
                q_rpi_value_start,
                tx_id_inv,
                tx_value_lo_inv,
                tx_id_diff_inv,
                calldata_gas_cost,
                is_final,
                rpi_bytes[-1],
                rpi_bytes_keccakrlc[-1],
                rpi_value_lc[-1],
                Word(0),  # rpi_digest_word will be set below
                q_rpi_byte_enable,
                keccak_table,
                tx_row,
            )
            rows.append(row)
            i -= 1
    rows.reverse()
    output_digest = keccak(bytes(rpi_bytes))
    assert len(output_digest) == 32

    # keccak lookup happened on 0 row
    rows[0].rpi_digest_word = Word(output_digest)

    public_inputs = PublicInputs(
        pi_keccak=Word(output_digest),
        state_root=Word(public_data.block.state_root),
        state_root_prev=Word(public_data.state_root_prev),
    )
    keccak_table.add(bytes(rpi_bytes), keccak_rand)

    block_table.table.reverse()
    tx_table.table.reverse()
    return Witness(
        rows,
        public_inputs,
        set(calldata_gas_cost_table),
        keccak_table,
        block_table,
        tx_table,
        circuit_len,
        copy_constrains=rpi_bytes_group,
    )


def flattern_len(a: List[List]):
    return len([c for b in a for c in b])
