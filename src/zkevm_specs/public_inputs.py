from dataclasses import dataclass
from typing import Tuple, List, Union

from .util import (
    FQ,
    U64,
    U160,
    U256,
    linear_combine,
    PUBLIC_INPUTS_BLOCK_LEN as BLOCK_LEN,
    PUBLIC_INPUTS_EXTRA_LEN as EXTRA_LEN,
    PUBLIC_INPUTS_TX_LEN as TX_LEN,
    GAS_COST_TX_CALL_DATA_PER_NON_ZERO_BYTE,
    GAS_COST_TX_CALL_DATA_PER_ZERO_BYTE,
)
from .encoding import is_circuit_code
from .tx import Tag as TxTag
from .evm import (
    BlockContextFieldTag as BlockTag,
)


@dataclass
class BlockTableRow:
    value: FQ


@dataclass
class TxTableRow:
    tx_id: FQ
    tag: FQ  # Fixed Column
    index: FQ
    value: FQ


@dataclass
class Row:
    """PublicInputs circuit row"""

    q_block_table: FQ  # Fixed Column
    block_table: BlockTableRow
    q_tx_table: FQ  # Fixed Column
    tx_table: TxTableRow

    raw_public_inputs: FQ
    rpi_rlc_acc: FQ  # raw_public_inputs accumulated RLC from bottom to top
    rand_rpi: FQ

    q_end: FQ  # Fixed Column


@dataclass
class PublicInputs:
    """Public Inputs of the PublicInputs circuit"""

    rand_rpi: FQ  # randomness used in the RLC of the raw_public_inputs
    rpi_rlc: FQ  # raw_public_inputs RLC encoded

    chain_id: FQ
    state_root: FQ
    state_root_prev: FQ


@is_circuit_code
def check_row(
    row: Row,
    row_next: Row,
    row_offset_tx_table_tx_id: Row,
    row_offset_tx_table_index: Row,
    row_offset_tx_table_value: Row,
):

    q_not_end = 1 - row.q_end

    # 0.0 rpi_rlc_acc[0] == RLC(raw_public_inputs, rand_rpi)
    assert (
        row.rpi_rlc_acc == q_not_end * row_next.rpi_rlc_acc * row.rand_rpi + row.raw_public_inputs
    )

    # 0.1 rand_rpi[i] == rand_rpi[j]
    assert q_not_end * row.rand_rpi == q_not_end * row_next.rand_rpi

    # 0.2 Block table -> value column match with raw_public_inputs at expected offset
    assert row.q_block_table * row.block_table.value == row.q_block_table * row.raw_public_inputs

    # 0.3 Tx table -> {tx_id, index, value} column match with raw_public_inputs at expected offset
    assert (
        row.q_tx_table * row.tx_table.tx_id
        == row.q_tx_table * row_offset_tx_table_tx_id.raw_public_inputs
    )
    assert (
        row.q_tx_table * row.tx_table.index
        == row.q_tx_table * row_offset_tx_table_index.raw_public_inputs
    )
    assert (
        row.q_tx_table * row.tx_table.value
        == row.q_tx_table * row_offset_tx_table_value.raw_public_inputs
    )


@dataclass
class Witness:
    rows: List[Row]  # PublicInputs rows
    public_inputs: PublicInputs  # Public Inputs of the PublicInputs circuit


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

    # 1.0 rand_rpi copy constraint from public input to advice column
    assert rows[0].rand_rpi == witness.public_inputs.rand_rpi

    # 1.1 rpi_rlc copy constraint from public input to advice column
    assert rows[0].rpi_rlc_acc == witness.public_inputs.rpi_rlc

    # 1.2 chain_id copy constraint from public input to raw_public_inputs
    assert rows[BlockTag.ChainId - 1].raw_public_inputs == witness.public_inputs.chain_id

    # 1.3 state_root copy constraint from public input to raw_public_inputs
    assert rows[BLOCK_LEN + 1].raw_public_inputs == witness.public_inputs.state_root

    # 1.4 state_root_prev copy constraint from public input to raw_public_inputs
    assert rows[BLOCK_LEN + 2].raw_public_inputs == witness.public_inputs.state_root_prev

    for i in range(len(rows)):
        row = rows[i]
        row_next = rows[(i + 1) % len(rows)]
        # Offset in raw_public_inputs with tx_table -> tx_id column
        tx_table_offset = BLOCK_LEN + EXTRA_LEN
        row_offset_tx_table_tx_id = rows[(i + tx_table_offset) % len(rows)]
        # Offset in raw_public_inputs with tx_table -> index column
        tx_table_offset += TX_LEN * MAX_TXS + MAX_CALLDATA_BYTES
        row_offset_tx_table_index = rows[(i + tx_table_offset) % len(rows)]
        # Offset in raw_public_inputs with tx_table -> value column
        tx_table_offset += TX_LEN * MAX_TXS + MAX_CALLDATA_BYTES
        row_offset_tx_table_value = rows[(i + tx_table_offset) % len(rows)]

        check_row(
            row,
            row_next,
            row_offset_tx_table_tx_id,
            row_offset_tx_table_index,
            row_offset_tx_table_value,
        )


@dataclass
class Block:
    """Block header"""

    hash: U256
    parent_hash: U256
    uncle_hash: U256
    coinbase: U160
    root: U256  # State Trie Root
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

    def tx_table_value_column(self) -> List[FQ]:
        """Return the tx table value column corresponding to this tx.  Contains fields and no calldata"""
        column = []
        column.append(FQ(self.nonce))  # Nonce
        column.append(FQ(self.gas))  # Gas
        column.append(FQ(self.gas_price))  # GasPrice
        column.append(FQ(self.from_addr))  # CallerAddress
        column.append(FQ(self.to_addr or 0))  # CalleeAddress
        column.append(FQ(1 if self.to_addr is None else 0))  # IsCreate
        column.append(FQ(self.value))  # Value
        column.append(FQ(len(self.data)))  # CallDataLength
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
        column.append(FQ(call_data_gas_cost))  # CallDataCost
        column.append(FQ(self.tx_sign_hash))  # TxSignHash
        return column

    def tx_table_tx_fields(self, index: int) -> Tuple[List[FQ], List[FQ], List[FQ]]:
        """Return the tx table contents corresponding to this tx.  Contains fields and no calldata"""
        tx_id_col = [FQ(index + 1)] * TX_LEN
        index_col = [FQ(0)] * TX_LEN
        value_col = self.tx_table_value_column()
        return (tx_id_col, index_col, value_col)


@dataclass
class PublicData:
    chain_id: U64
    block: Block
    block_prev_root: U256
    block_hashes: List[U256]  # 256 previous block hashes
    txs: List[Transaction]

    def block_table_value_column(self) -> List[FQ]:
        """Return the block table value column"""
        column = []
        column.append(FQ(self.block.coinbase))  # offset = 0
        column.append(FQ(self.block.gas_limit))
        column.append(FQ(self.block.number))
        column.append(FQ(self.block.time))
        column.append(FQ(self.block.difficulty))
        column.append(FQ(self.block.base_fee))
        column.append(FQ(self.chain_id))
        assert len(self.block_hashes) == 256
        for block_hash in self.block_hashes:
            column.append(FQ(block_hash))  # offset = 7
        return column

    def tx_table_tx_fields(self, MAX_TXS: int) -> Tuple[List[FQ], List[FQ], List[FQ]]:
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

    def tx_table_tx_calldata(self, MAX_CALLDATA_BYTES: int) -> Tuple[List[FQ], List[FQ], List[FQ]]:
        """Return the tx table, dynamic section with calldata"""
        tx_id_col = []
        index_col = []
        value_col = []
        for i, tx in enumerate(self.txs):
            for byte_index, byte in enumerate(tx.data):
                tx_id_col.append(FQ(i + 1))
                index_col.append(FQ(byte_index))
                value_col.append(FQ(byte))

        assert len(value_col) <= MAX_CALLDATA_BYTES
        calldata_padding = [FQ(0)] * (MAX_CALLDATA_BYTES - len(value_col))
        tx_id_col.extend(calldata_padding)
        index_col.extend(calldata_padding)
        value_col.extend(calldata_padding)

        return (tx_id_col, index_col, value_col)

    def tx_table(
        self, MAX_TXS: int, MAX_CALLDATA_BYTES: int
    ) -> Tuple[List[FQ], List[FQ], List[FQ]]:
        """Return the complete tx table"""
        tx_fields = self.tx_table_tx_fields(MAX_TXS)
        tx_calldata = self.tx_table_tx_calldata(MAX_CALLDATA_BYTES)
        return (
            tx_fields[0] + tx_calldata[0],
            tx_fields[1] + tx_calldata[1],
            tx_fields[2] + tx_calldata[2],
        )


def public_data2witness(
    public_data: PublicData, MAX_TXS: int, MAX_CALLDATA_BYTES: int, rand_rpi: FQ
) -> Witness:
    # NOTE: Begin rlc calculation of raw_public_inputs.  This logic must be
    # implemented by the verifier.
    raw_public_inputs = []

    # Block table
    block_table_value_col = public_data.block_table_value_column()
    raw_public_inputs.extend(block_table_value_col)  # start offset = 0

    # Extra fields
    raw_public_inputs.append(FQ(public_data.block.hash))  # start offset = BLOCK_LEN
    raw_public_inputs.append(FQ(public_data.block.root))
    raw_public_inputs.append(FQ(public_data.block_prev_root))

    # Tx Table
    tx_table = public_data.tx_table(MAX_TXS, MAX_CALLDATA_BYTES)
    raw_public_inputs.extend(tx_table[0])  # start offset = BLOCK_LEN + EXTRA_LEN
    raw_public_inputs.extend(tx_table[1])  # start offset += (TX_LEN * MAX_TXS + MAX_CALLDATA_BYTES)
    raw_public_inputs.extend(tx_table[2])  # start offset += (TX_LEN * MAX_TXS + MAX_CALLDATA_BYTES)

    assert len(raw_public_inputs) == BLOCK_LEN + EXTRA_LEN + 3 * (
        TX_LEN * MAX_TXS + MAX_CALLDATA_BYTES
    )
    rpi_rlc = linear_combine(raw_public_inputs, rand_rpi, range_check=False)
    # NOTE: End rlc calculation of raw_public_inputs.

    rpi_rlc_acc_col = [raw_public_inputs[-1]]
    for i in reversed(range(len(raw_public_inputs) - 1)):
        rpi_rlc_acc_col.append(rpi_rlc_acc_col[-1] * rand_rpi + raw_public_inputs[i])
    rpi_rlc_acc_col = list(reversed(rpi_rlc_acc_col))

    rows = []
    for i in range(len(raw_public_inputs)):
        q_end = FQ(1) if i == len(raw_public_inputs) - 1 else FQ(0)
        block_row = BlockTableRow(FQ(0))
        q_block_table = FQ(0)
        if i < BLOCK_LEN:
            q_block_table = FQ(1)
            block_row = BlockTableRow(block_table_value_col[i])
        q_tx_table = FQ(0)
        tx_row = TxTableRow(FQ(0), FQ(0), FQ(0), FQ(0))
        if i < TX_LEN * MAX_TXS + MAX_CALLDATA_BYTES:
            q_tx_table = FQ(1)
            tx_id = tx_table[0][i]
            index = tx_table[1][i]
            value = tx_table[2][i]
            tag = FQ(TxTag.CallData)
            if i < TX_LEN * MAX_TXS:
                # Iterate over TxTag values (until TxTag.TxSignHash) in a cycle
                tag = FQ((i % TX_LEN) + 1)
            tx_row = TxTableRow(tx_id, tag, index, value)
        row = Row(
            q_block_table,
            block_row,
            q_tx_table,
            tx_row,
            raw_public_inputs[i],
            rpi_rlc_acc_col[i],
            rand_rpi,
            q_end,
        )
        rows.append(row)

    public_inputs = PublicInputs(
        rand_rpi,
        rpi_rlc,
        FQ(public_data.chain_id),
        FQ(public_data.block.root),
        FQ(public_data.block_prev_root),
    )
    return Witness(rows, public_inputs)
