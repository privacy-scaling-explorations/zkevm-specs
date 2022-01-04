from ..instruction import Instruction, Transition

# TODO:
# constraint op?
# combine to storage?
# check: is_sload = opcode == OP_SLOAD, is_sstore = 1 - is_sload?

def sload(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.SLOAD)

    address = instruction.stack_pop()
    value = instruction.stack_push()
    
    storage_value = instruction.storage_read(address)
    assert(value == storage_value) # TODO: ???

    # TDOO: deal with gas correctly
    instruction.constrain_same_context_state_transition(
        opcode,
        rw_counter=Transition.delta(3),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(0),
    )


def sstore(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.SSTORE)

    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)
    rw_counter_end_of_reversion = instruction.call_context_lookup(CallContextFieldTag.RWCounterEndOfReversion)
    is_persistent = instruction.call_context_lookup(CallContextFieldTag.IsPersistent)

    account_address = instruction.tx_lookup(tx_id, TxContextFieldTag.CalleeAddress)

    storage_slot = instruction.stack_pop()
    value = instruction.stack_pop()

    _ = self.add_storage_slot_to_access_list_with_reversion(
        account_address, storage_slot,
        is_persistent, rw_counter_end_of_reversion
    )

    # TDOO: deal with gas correctly

