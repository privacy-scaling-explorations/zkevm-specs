from ...util import FQ
from ..instruction import Instruction, Transition
from ..table import CallContextFieldTag, TxTableRow, TxContextFieldTag
from typing import Set

# EndBlock is an execution state that constraints the following:
# 1. Once the EndBlock state is reached, there's no other execution states appearing until the end of the EVM Circuit.  In particular, after the first EndBlock, there will be no new lookups to the rw_table.
# 2. The number of meaningful entries (non-padding) in the rw_table match the rw_counter after the EndBlock state is processed.
# 3. The number of txs processed by the EVM Circuit match the number of txs in the TxTable
#    total_tx = instruction.call_context_lookup(CallContextFieldTag.TxId)

# As an extra point:
# 4. We need to prove that the EndBlock state exists

# We prove (1) by constraining the transition rule that after an EndBlock
# state, only an EndBlock state can follow.
#
# We prove (2) and (3) by proving that at least `MAX_COUNT - evm_circuit_count`
# padding elements exist in the rw table and tx table.  To achieve this, we do
# padding at the beginning of both tables with sequential indexes at
# `rw_counter` (in rw_table) or `tx_id` (in tx_table).
#
# We prove (4) in the circuit implementation by constraining that the last
# execution step at the end of the EVM circuit is an EndBlock.  When the number
# of steps is less than the EVM circuit height, we pad at the end with
# EndBlock.  This will require the EndBlock to have height = 1 in the circuit,
# which can be achieved after reducing the number of cells used in the state
# selector.

# Count the max number of txs that the TxTable can hold by counting rows of
# fixed fields + padding rows in the fixed fields section.
def get_tx_table_max_txs(table: Set[TxTableRow]) -> int:
    fixed_field_count = 0
    for row in table:
        if (row.field_tag != TxContextFieldTag.CallData) or (
            row.field_tag == TxContextFieldTag.Pad and row.tx_id != 0
        ):
            fixed_field_count += 1
    return fixed_field_count // TxContextFieldTag.TxSignHash


def end_block(instruction: Instruction):
    if instruction.is_last_step:
        # 1. Verify rw_counter counts to the same number of meaningful rows in
        # rw_table to ensure there is no malicious insertion.
        rw_table_size = len(instruction.tables.rw_table)
        total_rw = instruction.curr.rw_counter + 1  # extra 1 from the tx_id lookup
        # Verify that there are at most total_rw meaningful entries in the rw_table
        instruction.rw_table_start_lookup(FQ(1))
        instruction.rw_table_start_lookup(rw_table_size - total_rw)
        # Since every lookup done in the EVM circuit must succeed and uses a unique
        # rw_counter, we know that at least there are total_rw meaningful entries
        # in the rw_table.
        # We conclude that the number of meaningful entries in the rw_table is total_rw.

        # 2. Verify that final step as tx_id identical to the number of txs in
        # tx_table.
        tx_table_max_txs = get_tx_table_max_txs(instruction.tables.tx_table)
        total_tx = instruction.call_context_lookup(CallContextFieldTag.TxId)
        # Verify that there are at most total_txs meaningful entries in the tx_table
        instruction.tx_context_lookup(FQ(1), TxContextFieldTag.Pad)
        instruction.tx_context_lookup(
            FQ((tx_table_max_txs - total_tx.expr().n) * TxContextFieldTag.TxSignHash),
            TxContextFieldTag.Pad,
        )
        # Since every tx lookup done in the EVM circuit must succeed and uses a unique
        # tx_id, we know that at least there are total_tx meaningful txs
        # in the tx_table.
        # We conclude that the number of meaningful txs in the tx_table is total_tx.
    else:
        # Propagate rw_counter and call_id all the way down
        instruction.constrain_step_state_transition(
            rw_counter=Transition.same(),
            call_id=Transition.same(),
        )
