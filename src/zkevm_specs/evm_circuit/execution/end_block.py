from ...util import FQ, N_BYTES_GAS
from ..instruction import Instruction, Transition
from ..table import (
    CallContextFieldTag,
    TxTableRow,
    TxContextFieldTag,
    BlockContextFieldTag,
    TxReceiptFieldTag,
)
from typing import Set

# EndBlock is an execution state that constraints the following:
# A. Once the EndBlock state is reached, there's no other execution states
# appearing until the end of the EVM Circuit.  In particular, after the first
# EndBlock, there will be no new lookups to the rw_table.
#
# B. The number of meaningful entries (non-padding) in the rw_table match the
# rw_counter after the EndBlock state is processed.
#
# C. The number of txs processed by the EVM Circuit match the number of txs in
# the TxTable
#
# As an extra point:
# D. We need to prove that at least one EndBlock state exists
#
# Also:
# E. We need to prove that CumulativeGasCost does not excee the gas limit
#
# We prove (A) by constraining the transition rule that after an EndBlock
# state, only an EndBlock state can follow.
#
# We prove (B) by proving that at least `MAX_RWS - total_rws` padding elements
# exist in the rw table.  To achieve this, we do padding at the beginning of
# the RwTable with a sequential index `rw_counter`.  The RwTable constraints
# that padding rows have sequential indexes, so by doing 2 lookups with
# rw_counter = {a, b} we know there are at least b-a padding rows.
#
# We prove (C) by showing that the transaction ID after the last one processed
# corresponds to a padding tx in the TxTable, which enforces that once a
# padding txs appears in the table, the rest will also be padding.  This way,
# we know that if a padding tx with tx_id exist, then at most there are tx_id-1
# non-padding txs.  In case we have exhausted the TxTable with txs, we won't
# have any padding txs; so we skip the lookup.
#
# We prove (D) in the circuit implementation by constraining that the last
# execution step at the end of the EVM circuit is an EndBlock.  When the number
# of steps is less than the EVM circuit height, we pad at the end with
# EndBlock.  This will require the EndBlock to have height = 1 in the circuit,
# which can be achieved after reducing the number of cells used in the state
# selector.
#
# We prove (E) by quering the block table for the gas limit and the rw table for
# the cumulative gas and ensuring CumulativeGasCost <= GasLimit.


# Count the max number of txs that the TxTable can hold by counting rows of
# type CallerAddress.
def get_tx_table_max_txs(table: Set[TxTableRow]) -> int:
    return len([row for row in table if row.field_tag == TxContextFieldTag.CallerAddress])


def end_block(instruction: Instruction):
    max_txs = get_tx_table_max_txs(instruction.tables.tx_table)
    max_rws = len(instruction.tables.rw_table)

    total_txs = FQ(
        len(
            [
                tx_row
                for tx_row in instruction.tables.tx_table
                if tx_row.field_tag == TxContextFieldTag.CallerAddress
                and tx_row.value.value().expr() != FQ(0)
            ]
        )
    )
    # total_valid_txs = total_txs - invalid_txs
    total_valid_txs = FQ(
        total_txs
        - len(
            [
                tx_row
                for tx_row in instruction.tables.tx_table
                if tx_row.field_tag == TxContextFieldTag.TxInvalid
                and tx_row.value.value().expr() == FQ(1)
            ]
        )
    )
    # Note that rw_counter starts at 1
    is_empty_block = instruction.is_zero(instruction.curr.rw_counter - 1)
    # If the block is not empty, we will do 1 call_context lookup
    total_rws = (1 - is_empty_block) * (instruction.curr.rw_counter - 1 + 2)

    if instruction.is_last_step:
        # 1. Constraint total_valid_txs witness values depending on the empty block case.
        if is_empty_block == FQ(1):
            # 1a. total_valid_txs is 0 in empty block
            instruction.constrain_equal(total_valid_txs, FQ(0))
        else:
            # 1b. total_txs matches the tx_id that corresponds to the final step.
            instruction.constrain_equal(
                instruction.call_context_lookup(CallContextFieldTag.TxId).value(), total_txs
            )
            # 4. Verify that CumulativeGasUsed does not exceed the block gas limit.
            gas_limit = instruction.block_context_lookup(BlockContextFieldTag.GasLimit).value()
            cumulative_gas = instruction.tx_receipt_read(
                total_txs,
                TxReceiptFieldTag.CumulativeGasUsed,
            )
            limit_exceeded, _ = instruction.compare(gas_limit, cumulative_gas, N_BYTES_GAS)
            instruction.constrain_equal(limit_exceeded, FQ(0))

        # 2. If total_txs == max_txs, we know we have covered all txs from the tx_table.
        # If not, we need to check that the rest of txs in the table are
        # padding.
        if total_txs != max_txs:
            # Verify that there are at most total_txs meaningful txs in the tx_table, by
            # showing that the Tx following the last processed one has
            # CallerAddress = 0x0 (which means padding tx).
            instruction.constrain_equal(
                instruction.tx_context_lookup(
                    FQ(total_txs + 1), TxContextFieldTag.CallerAddress
                ).value(),
                FQ(0),
            )
            # Since every tx lookup done in the EVM circuit must succeed and
            # uses a unique tx_id, we know that at least there are total_tx
            # meaningful txs in the tx_table. We conclude that the number of
            # meaningful txs in the tx_table is total_tx.

        # 3. Verify rw_counter counts to the same number of meaningful rows in
        # rw_table to ensure there is no malicious insertion.
        # Verify that there are at most total_rws meaningful entries in the rw_table
        instruction.rw_table_start_lookup(FQ(1))
        instruction.rw_table_start_lookup(max_rws - total_rws)
        # Since every lookup done in the EVM circuit must succeed and uses a unique
        # rw_counter, we know that at least there are total_rws meaningful entries
        # in the rw_table.
        # We conclude that the number of meaningful entries in the rw_table is total_rws.

        # TODO: Send fixed reward to coinbase according to the chain rules (See
        # https://github.com/privacy-scaling-explorations/zkevm-specs/issues/290)
    else:
        # Propagate rw_counter and call_id all the way down
        instruction.constrain_step_state_transition(
            rw_counter=Transition.same(),
            call_id=Transition.same(),
        )
