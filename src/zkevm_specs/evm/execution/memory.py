from ..instruction import Instruction, Transition
from ..opcode import Opcode
from ..table import RW
from ...util import FQ


def memory(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    address = instruction.stack_pop()

    is_mload = instruction.is_equal(opcode, Opcode.MLOAD)
    is_mstore8 = instruction.is_equal(opcode, Opcode.MSTORE8)
    is_store = FQ(1) - is_mload
    is_not_mstore8 = FQ(1) - is_mstore8

    value = instruction.stack_push() if is_mload == FQ(1) else instruction.stack_pop()

    memory_offset = instruction.curr.memory_size
    next_memory_size, memory_expansion_gas_cost = instruction.memory_expansion(
        memory_offset, address.expr() + FQ(1) + (is_not_mstore8 * FQ(31))
    )

    if is_mstore8 == FQ(1):
        instruction.is_equal(
            instruction.memory_lookup(RW.Write, address.expr()), FQ(value.le_bytes[0])
        )

    if is_not_mstore8 == FQ(1):
        for idx in range(32):
            instruction.is_equal(
                instruction.memory_lookup(
                    RW.Write if is_store == FQ(1) else RW.Read, address.expr() + idx
                ),
                FQ(value.le_bytes[31 - idx]),
            )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(34 - (is_mstore8 * 31)),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(is_store * 2),
        memory_size=Transition.to(next_memory_size),
        dynamic_gas_cost=memory_expansion_gas_cost,
    )
