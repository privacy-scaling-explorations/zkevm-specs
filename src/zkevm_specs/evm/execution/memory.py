from ..instruction import Instruction, Transition
from ..opcode import Opcode
from ..table import RW
from ...util import FQ


def memory(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    address = instruction.stack_pop()
    value = instruction.stack_pop()

    is_mload = instruction.is_equal(opcode, Opcode.MLOAD)
    is_mstore8 = instruction.is_equal(opcode, Opcode.MSTORE8)
    is_store = FQ(1) - is_mload
    is_not_mstore8 = FQ(1) - is_mstore8

    next_memory_size, memory_expansion_gas_cost = instruction.memory_expansion(
        instruction.curr.memory_size, address + FQ(1) + (is_not_mstore8 * FQ(31))
    )

    instruction.stack_lookup(
        RW.Read if is_mload else RW.Write, instruction.curr.stack_pointer - is_mload
    )

    if is_mstore8:
        instruction.memory_lookup(RW.Write if is_store else RW.Read, address)

    if is_not_mstore8:
        for idx in range(32):
            instruction.memory_lookup(RW.Write if is_store else RW.Read, address + FQ(idx))

    rw_counter_delta = 34 + is_mstore8 * 3
    stack_pointer_delta = 0 + is_store * -2

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(instruction.rw_counter_offset + rw_counter_delta),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(stack_pointer_delta),
        memory_size=Transition.to(next_memory_size),
        dynamic_gas_cost=memory_expansion_gas_cost,
    )
