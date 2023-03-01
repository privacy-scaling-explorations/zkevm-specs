from ..instruction import Instruction, Transition
from zkevm_specs.util import FQ


def signextend(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    index = instruction.stack_pop()
    value = instruction.stack_pop()
    result = instruction.stack_push()

    is_msb_sum_zero = instruction.is_zero(FQ(sum(index.le_bytes[1:32])))
    sign_byte = (
        FQ((value.le_bytes[index.le_bytes[0]] >> 7) * 0xFF) if index.le_bytes[0] < 31 else FQ(0)
    )
    selectors = [FQ(index.expr() == FQ(i)) for i in range(31)]
    is_byte_selected = [FQ(index.le_bytes[0] == i) for i in range(31)]

    selected_byte = FQ(0)
    for i in range(31):
        is_selected = is_byte_selected[i] * is_msb_sum_zero
        selected_byte += value.le_bytes[i] * is_selected
        instruction.is_equal(is_selected + (selectors[i - 1] if i > 0 else FQ(0)), selectors[i])

    instruction.sign_byte_lookup(selected_byte, sign_byte)

    for idx in range(32):
        if idx == 0:
            instruction.is_equal(FQ(result.le_bytes[idx]), FQ(value.le_bytes[idx]))
        else:
            instruction.is_equal(
                FQ(result.le_bytes[idx]),
                sign_byte if selectors[idx - 1] == FQ(1) else FQ(value.le_bytes[idx]),
            )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(3),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(1),
    )
