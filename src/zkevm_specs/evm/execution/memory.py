from ..instruction import Instruction, Transition
from ..opcode import Opcode
from ..table import RW, CallContextFieldTag
from ...util import FQ


def memory(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    address = instruction.stack_pop()

    is_mload = instruction.is_equal(opcode, Opcode.MLOAD)
    is_mstore8 = instruction.is_equal(opcode, Opcode.MSTORE8)
    is_store = FQ(1) - is_mload
    is_not_mstore8 = FQ(1) - is_mstore8

    value = instruction.stack_push() if is_mload == FQ(1) else instruction.stack_pop()

    src_id = instruction.call_context_lookup(CallContextFieldTag.TxId)
    memory_offset = instruction.curr.memory_size
    next_memory_size, memory_expansion_gas_cost = instruction.memory_expansion(
        memory_offset, address.expr() + FQ(32)
    )

    if is_mstore8 == FQ(1):
        instruction.memory_lookup(RW.Write if is_store == FQ(1) else RW.Read, address.expr())

    if is_not_mstore8 == FQ(1):
        for idx in range(32):
            instruction.memory_lookup(
                RW.Write if is_store == FQ(1) else RW.Read, memory_offset + idx, src_id
            )

    rw_counter_delta = 34
    stack_pointer_delta = 0 + is_store * -2

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(rw_counter_delta),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(stack_pointer_delta),
        memory_size=Transition.to(next_memory_size),
        dynamic_gas_cost=memory_expansion_gas_cost,
    )
