from ...util import FQ
from ..instruction import Instruction, Transition
from ..table import CallContextFieldTag

# EndBlock is an execution state that constraints the following:
# 1. Once the EndBlock state is reached, there's no other execution states appearing until the end of the EVM Circuit.  In particular, after the first EndBlock, there will be no more lookups to the rw_table.
# 2. The number of meaningful entries (non-padding) in the rw_table match the rw_counter after the EndBlock state is processed.
#   - instruction.curr.rw_counter
# 3. The number of txs processed by the EVM Circuit match the number of txs in the TxTable
#    total_tx = instruction.call_context_lookup(CallContextFieldTag.TxId)

# Extra
# 4. We need to prove that the EndBlock state exists


def end_block(instruction: Instruction):
    if instruction.is_last_step:
        # Verify final step has tx_id identical to the tx amount in tx_table.
        total_tx = instruction.call_context_lookup(CallContextFieldTag.TxId)
        instruction.constrain_equal(
            total_tx,
            FQ(max([row.tx_id.expr().n for row in instruction.tables.tx_table])),
        )

        # Verify rw_counter counts to identical rw amount in rw_table to ensure
        # there is no malicious insertion.
        total_rw = instruction.curr.rw_counter + 1  # extra 1 from the tx_id lookup
        instruction.constrain_equal(
            total_rw,
            FQ(len(instruction.tables.rw_table)),
        )

        # TODO: lookup to rw_table to verify rw_counter
    else:
        # Propagate rw_counter and call_id all the way down
        instruction.constrain_step_state_transition(
            rw_counter=Transition.same(),
            call_id=Transition.same(),
        )

    rw_table_size = len(instruction.tables.rw_table)
    total_rw = instruction.curr.rw_counter + 1  # extra 1 from the tx_id lookup
    # Verify that there are at most total_rw meaningful entries in the rw_table
    instruction.rw_table_start_lookup(1)
    instruction.rw_table_start_lookup(rw_table_size - total_rw)
    # Since every lookup done in the EVM circuit must succeed and uses a unique
    # rw_counter, we know that at least there are total_rw meaningful entries
    # in the rw_table.
    # We conclude that the number of meaningful entries in the rw_table is total_rw.
