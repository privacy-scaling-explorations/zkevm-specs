from dataclasses import dataclass
from typing import Tuple, List, Union, Set

from .util import (
    FQ,
    Word,
    WordOrValue,
    U64,
    U160,
    U256,
    linear_combine_bytes,
    PUBLIC_INPUTS_BLOCK_LEN as BLOCK_LEN,
    PUBLIC_INPUTS_EXTRA_LEN as EXTRA_LEN,
    PUBLIC_INPUTS_TX_LEN as TX_LEN,
    GAS_COST_TX_CALL_DATA_PER_NON_ZERO_BYTE,
    GAS_COST_TX_CALL_DATA_PER_ZERO_BYTE,
    Expression,
    is_circuit_code,
)
from .tx_circuit import Tag as TxTag
from .evm_circuit import (
    BlockContextFieldTag as BlockTag,
)
from eth_utils import keccak
from .evm_circuit.table import KeccakTableRow, lookup, TableRow


@dataclass
class BlockTableRow:
    value: WordOrValue


@dataclass
class TxTableRow:
    tx_id: FQ
    tag: FQ  # Fixed Column
    index: FQ
    value: WordOrValue


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
                RLC(bytes(reversed(input)), keccak_randomness, n_bytes=64).expr(),
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

    q_block_table: FQ
    q_tx_table: FQ

    q_digest_last: FQ
    q_bytes_last: FQ
    q_tx_table: FQ
    q_tx_calldata: FQ
    q_tx_calldata_start: FQ
    q_rpi_keccak_lookup: FQ
    q_rpi_value_start: FQ # Fixed Column
    q_digest_value_start: FQ # Fixed Column

    tx_id_inv: FQ  # (tx_tag - CallDataLength)^(-1) when q_tx_table = 1
    # tx_id^(-1) when q_tx_calldata = 1
    tx_value_lo_inv: FQ
    tx_id_diff_inv: FQ
    calldata_gas_cost: FQ
    is_final: FQ
    is_value_rlc: FQ

    rpi_bytes: FQ
    rpi_bytes_keccakrlc: FQ
    rpi_value_rlc: FQ
    rpi_digest_bytes: FQ
    rpi_digest_bytes_rlc: FQ
    rpi_digest_bytes_lc: FQ

    q_rpi_byte_enable: FQ
    q_digest_byte_enable: FQ

    block_table: BlockTableRow
    tx_table: TxTableRow
    keccak_table: KeccakTableRow

@dataclass
class PublicInputs:
    """Public Inputs of the PublicInputs circuit"""
    pi_keccak: WordOrValue

@is_circuit_code
def check_row(
    row: Row,
    row_next: Row,
    # TODO challenge API
    row_offset_block_table_value_hi: Row,
    row_offset_tx_table_tx_id: Row,
    row_offset_tx_table_index: Row,
    row_offset_tx_table_value_lo: Row,
    row_offset_tx_table_value_hi: Row,
    table: Set[TxCallDataGasCostAccRow],
    fixed_u16_table: Set[FixedU16Row],
):
    # TODO fix me
    byte_pow_base, evm_rand = FQ(256), FQ(256)
    q_bytes_last = row.q_bytes_last
    q_rpi_byte_enable = row.q_rpi_byte_enable
    # q_end = row.q_end
    row_offset_block_table_value_lo = row

    # gate 1 and gate 2 are compensation branch
    # 1: rpi_bytes_keccakrlc[last] = rpi_bytes[last]
    assert q_rpi_byte_enable * q_bytes_last * (row.rpi_bytes_keccakrlc - row.rpi_bytes) == FQ(0)

    # 2: rpi_bytes_keccakrlc[i] = keccak_rand * rpi_bytes_keccakrlc[i+1] + rpi_bytes[i]"
    # TODO how to represent NOT(selector) elegantly?
    assert q_rpi_byte_enable * (FQ(1) - q_bytes_last) * (row.rpi_bytes_keccakrlc - row_next.rpi_bytes_keccakrlc - row.rpi_bytes)

    # gate 3 and gate 4 are compensation branch
    # 3: rpi_value_rlc[i] = rpi_value_rlc[i+1] * (is_value_rlc[i] ? evm_rand : byte_pow_base )
    # + rpi_bytes[i]
    assert row.is_value_rlc in [0, 1]
    r = evm_rand if row.is_value_rlc == FQ(1) else byte_pow_base
    assert row.q_rpi_byte_enable*(FQ(1) -row.q_rpi_value_start)*(
        row.rpi_value_rlc - row_next.rpi_value_rlc * r - row.rpi_bytes
        ) == FQ(0)

    # 4. rpi_value_rlc[i] = rpi_bytes[i]
    assert row.q_rpi_byte_enable * row.q_rpi_value_start * (row.rpi_value_rlc - row.rpi_bytes) == FQ(0)

    # gate 5 and gate 6 are compensation branch
    # 5. rpi_digest_bytes_rlc[last] = rpi_digest_bytes[last]
    assert row.q_digest_byte_enable * row.q_digest_last * (row.rpi_digest_bytes_rlc - row.rpi_digest_bytes) == FQ(0)

    # 6. rpi_digest_bytes_rlc[i] = rpi_digest_bytes_rlc[i+1] * r + rpi_digest_bytes[i]
    assert row.q_digest_byte_enable * (FQ(1) - row.q_digest_last) * (
        row.rpi_digest_bytes_rlc - row_next.rpi_digest_bytes_rlc * evm_rand - row.rpi_digest_bytes_rlc
    ) == FQ(0)

    # gate 7 and gate 8 are compensation branch
    # 7. rpi_digest_bytes_lc[i] = rpi_digest_bytes[i]
    assert row.q_digest_byte_enable * (row.q_digest_value_start) * (
        row.rpi_digest_bytes_lc - row.rpi_digest_bytes
    ) == FQ(0)

    # 8. rpi_digest_bytes_lc[i] = rpi_digest_bytes_lc[i+1] * BYTE_POW_BASE + rpi_digest_bytes[i]
    assert row.q_digest_byte_enable * (FQ(1) - row.q_digest_value_start) * (
        row.rpi_digest_bytes_lc - row_next.rpi_digest_bytes_lc * byte_pow_base - row.rpi_digest_bytes
    )

    # 9. lookup rpi_bytes_keccakrlc against rpi_digest_bytes_rlc
    assert

    # NONEED 0.1 rand_rpi[i] == rand_rpi[j]
    ## assert q_not_end * row.rand_rpi == q_not_end * row_next.rand_rpi

    ## TODO how to represent block/tx table copy constraint?
    # 0.2 Block table -> value column match with raw_public_inputs at expected offset
    # assert (
    #     row.q_block_table * row.block_table.value.lo.expr()
    #     == row.q_block_table * row_offset_block_table_value_lo.raw_public_inputs
    # )
    # assert (
    #     row.q_block_table * row.block_table.value.hi.expr()
    #     == row.q_block_table * row_offset_block_table_value_hi.raw_public_inputs
    # )

    # 0.3 Tx table -> {tx_id, index, value} column match with raw_public_inputs at expected offset
    # id
    # assert (
    #     row.q_tx_table * row.tx_table.tx_id
    #     == row.q_tx_table * row_offset_tx_table_tx_id.raw_public_inputs
    # )
    # index
    # assert (
    #     row.q_tx_table * row.tx_table.index
    #     == row.q_tx_table * row_offset_tx_table_index.raw_public_inputs
    # )
    # value lo
    # assert (
    #     row.q_tx_table * row.tx_table.value.lo.expr()
    #     == row.q_tx_table * row_offset_tx_table_value_lo.raw_public_inputs
    # )
    # value hi
    # assert (
    #     row.q_tx_table * row.tx_table.value.hi.expr()
    #     == row.q_tx_table * row_offset_tx_table_value_hi.raw_public_inputs
    # )
    # call data lo
    # assert (
    #     row.q_tx_calldata * row.tx_table.value.lo.expr()
    #     == row.q_tx_calldata * row_offset_tx_table_value_lo.raw_public_inputs
    # )
    # call data hi
    # assert (
    #     row.q_tx_calldata * row.tx_table.value.hi.expr()
    #     == row.q_tx_calldata * row_offset_tx_table_value_hi.raw_public_inputs
    # )

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
        lookup(TxCallDataGasCostAccRow, table, query)


@dataclass
class Witness:
    rows: List[Row]  # PublicInputs rows
    public_inputs: PublicInputs  # Public Inputs of the PublicInputs circuit
    calldata_gas_cost_table: Set[TxCallDataGasCostAccRow]


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
    table = witness.calldata_gas_cost_table

    # 1.0 rand_rpi copy constraint from public input to advice column
    assert rows[0].rand_rpi == witness.public_inputs.rand_rpi

    # 1.1 rpi_rlc copy constraint from public input to advice column
    assert rows[0].rpi_rlc_acc == witness.public_inputs.rpi_rlc

    # 1.2 chain_id copy constraint from public input to raw_public_inputs
    assert rows[BlockTag.ChainId].raw_public_inputs == witness.public_inputs.chain_id

    # 1.3 state_root copy constraint from public input to raw_public_inputs
    offset_extra = BLOCK_LEN + 2
    assert rows[offset_extra + 2].raw_public_inputs == witness.public_inputs.state_root.lo.expr()
    assert rows[offset_extra + 3].raw_public_inputs == witness.public_inputs.state_root.hi.expr()

    # 1.4 state_root_prev copy constraint from public input to raw_public_inputs
    assert (
        rows[offset_extra + 4].raw_public_inputs == witness.public_inputs.state_root_prev.lo.expr()
    )
    assert (
        rows[offset_extra + 5].raw_public_inputs == witness.public_inputs.state_root_prev.hi.expr()
    )

    fixed_u16_table = set([FixedU16Row(FQ(i)) for i in range(1 << 16)])
    for i in range(len(rows)):
        print("DBG", i)
        row = rows[i]
        row_next = rows[(i + 1) % len(rows)]
        # Offset in raw_public_inputs with block_table -> value.hi column
        tx_table_offset = BLOCK_LEN // 2 + 1
        row_offset_block_table_value_hi = rows[(i + tx_table_offset) % len(rows)]
        # Offset in raw_public_inputs with tx_table -> tx_id column
        tx_table_offset = BLOCK_LEN + 2 + EXTRA_LEN
        row_offset_tx_table_tx_id = rows[(i + tx_table_offset) % len(rows)]
        # Offset in raw_public_inputs with tx_table -> index column
        tx_table_len = TX_LEN * MAX_TXS + 1
        tx_table_offset += tx_table_len
        row_offset_tx_table_index = rows[(i + tx_table_offset) % len(rows)]
        # Offset in raw_public_inputs with tx_table -> value.lo column
        tx_table_offset += tx_table_len
        row_offset_tx_table_value_lo = rows[(i + tx_table_offset) % len(rows)]
        # Offset in raw_public_inputs with tx_table -> value.hi column
        tx_table_offset += tx_table_len + MAX_CALLDATA_BYTES
        row_offset_tx_table_value_hi = rows[(i + tx_table_offset) % len(rows)]

        check_row(
            row,
            row_next,
            row_offset_block_table_value_hi,
            row_offset_tx_table_tx_id,
            row_offset_tx_table_index,
            row_offset_tx_table_value_lo,
            row_offset_tx_table_value_hi,
            table,
            fixed_u16_table,
        )


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
        column.append(WordOrValue(FQ(self.tx_sign_hash)))  # TxSignHash
        return column

    def tx_table_tx_fields(self, index: int) -> Tuple[List[FQ], List[FQ], List[WordOrValue]]:
        """Return the tx table contents corresponding to this tx.  Contains fields and no calldata"""
        tx_id_col = [FQ(index + 1)] * TX_LEN
        index_col = [FQ(0)] * TX_LEN
        value_col = self.tx_table_value_column()
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


def public_data2witness(
    public_data: PublicData, MAX_TXS: int, MAX_CALLDATA_BYTES: int, rand_rpi: FQ
) -> Witness:
    # Layout of raw_public_inputs:
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

    # NOTE: Begin rlc calculation of raw_public_inputs.  This logic must be
    # implemented by the verifier.
    raw_public_inputs = []

    # Block table
    block_table_value_col = public_data.block_table_value_column()
    raw_public_inputs.extend([w.lo.expr() for w in block_table_value_col])  # start offset = 0
    raw_public_inputs.extend([w.hi.expr() for w in block_table_value_col])

    # Extra fields
    hash = Word(public_data.block.hash)
    raw_public_inputs.append(hash.lo.expr())  # start offset = BLOCK_LEN + 1 (for 0 row)
    raw_public_inputs.append(hash.hi.expr())
    state_root = Word(public_data.block.state_root)
    raw_public_inputs.append(state_root.lo.expr())
    raw_public_inputs.append(state_root.hi.expr())
    state_root_prev = Word(public_data.state_root_prev)
    raw_public_inputs.append(state_root_prev.lo.expr())
    raw_public_inputs.append(state_root_prev.hi.expr())

    # Tx Table
    tx_table = public_data.tx_table(MAX_TXS, MAX_CALLDATA_BYTES)
    tx_table_tx_fields = public_data.tx_table_tx_fields(MAX_TXS)
    tx_table_tx_calldata = public_data.tx_table_tx_calldata(MAX_CALLDATA_BYTES)
    raw_public_inputs.extend(
        [FQ(0)] + tx_table_tx_fields[0]
    )  # start offset = BLOCK_LEN + 2 + EXTRA_LEN
    raw_public_inputs.extend(
        [FQ(0)] + tx_table_tx_fields[1]
    )  # start offset += (TX_LEN * MAX_TXS + 1)
    raw_public_inputs.extend(
        [FQ(0)] + [w.lo.expr() for w in tx_table_tx_fields[2]]
    )  # start offset += (TX_LEN * MAX_TXS + 1)
    raw_public_inputs.extend(
        [w.lo.expr() for w in tx_table_tx_calldata[2]]
    )  # start offset += (TX_LEN * MAX_TXS + 1)
    raw_public_inputs.extend(
        [FQ(0)] + [w.hi.expr() for w in tx_table_tx_fields[2]]
    )  # start offset += (TX_LEN * MAX_TXS)
    raw_public_inputs.extend(
        [w.hi.expr() for w in tx_table_tx_calldata[2]]
    )  # start offset += MAX_CALLDATA_BYTES

    assert (
        len(raw_public_inputs)
        == BLOCK_LEN + 2 + EXTRA_LEN + 4 * (TX_LEN * MAX_TXS + 1) + 2 * MAX_CALLDATA_BYTES
    )
    rpi_rlc = linear_combine_bytes(raw_public_inputs, rand_rpi, range_check=False)
    # NOTE: End rlc calculation of raw_public_inputs.

    rpi_rlc_acc_col = [raw_public_inputs[-1]]
    for i in reversed(range(len(raw_public_inputs) - 1)):
        rpi_rlc_acc_col.append(rpi_rlc_acc_col[-1] * rand_rpi + raw_public_inputs[i])
    rpi_rlc_acc_col = list(reversed(rpi_rlc_acc_col))

    rows = []
    calldata_gas_cost_table = [TxCallDataGasCostAccRow(FQ(0), FQ(0), FQ(0))]
    for i in range(len(raw_public_inputs)):
        q_end = FQ(1) if i == len(raw_public_inputs) - 1 else FQ(0)
        q_not_end = FQ(1) - q_end
        block_row = BlockTableRow(WordOrValue(FQ(0)))

        q_block_table = FQ(0)
        if i < BLOCK_LEN // 2 + 1:
            q_block_table = FQ(1)
            assert i < len(block_table_value_col)
            block_row = BlockTableRow(block_table_value_col[i])

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
            tx_id = tx_table[0][i]
            index = tx_table[1][i]
            value = tx_table[2][i]
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
                    tx_id_next = tx_table[0][i + 1]
                tx_id_diff_inv = (tx_id_next - tx_id).inv()
                calldata_gas_cost = tx_table_tx_calldata[3][i - tx_table_len]
                is_final = tx_table_tx_calldata[4][i - tx_table_len]
                calldata_gas_cost_table.append(
                    TxCallDataGasCostAccRow(tx_id, is_final, calldata_gas_cost)
                )

            if i == tx_table_len:
                q_tx_calldata_start = FQ(1)
            tx_row = TxTableRow(tx_id, tag, index, value)

        row = Row(
            q_block_table,
            block_row,
            q_tx_table,
            q_tx_calldata,
            q_tx_calldata_start,
            tx_row,
            tx_id_inv,
            tx_value_lo_inv,
            tx_id_diff_inv,
            calldata_gas_cost,
            is_final,
            raw_public_inputs[i],
            rpi_rlc_acc_col[i],
            rand_rpi,
            q_end,
            q_not_end,
        )
        rows.append(row)

    public_inputs = PublicInputs(
        rand_rpi,
        rpi_rlc,
        FQ(public_data.chain_id),
        Word(public_data.block.state_root),
        Word(public_data.state_root_prev),
    )
    return Witness(rows, public_inputs, set(calldata_gas_cost_table))
