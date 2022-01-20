from ..instruction import Instruction, Transition
from ..table import CallContextFieldTag


# TODO: Introduce constrain_instance to constrain the equality between witness
#       and public input, for total_tx and total_rw


def end_block(instruction: Instruction):
    if instruction.is_last_step:
        # Verify final step has tx_id identical to the tx amount in tx_table.
        total_tx = instruction.call_context_lookup(CallContextFieldTag.TxId)
        instruction.constrain_equal(
            total_tx,
            max([tx_id for tx_id, *_ in instruction.tables.tx_table]),
        )

        # Verify rw_counter counts to identical rw amount in rw_table to ensure
        # there is no malicious insertion.
        total_rw = instruction.curr.rw_counter + 1  # extra 1 from the tx_id lookup
        instruction.constrain_equal(
            total_rw,
            len(instruction.tables.rw_table),
        )
    else:
        # Propagate rw_counter and call_id all the way down
        instruction.constrain_step_state_transition(
            rw_counter=Transition.same(),
            call_id=Transition.same(),
        )
