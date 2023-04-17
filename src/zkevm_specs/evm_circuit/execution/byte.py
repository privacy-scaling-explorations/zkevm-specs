from ..instruction import Instruction, Transition
from ...util import FQ, Word


def byte(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    a = instruction.stack_pop()
    b = instruction.stack_pop()
    c = instruction.stack_push()

    index = a.to_le_bytes()
    value = b.to_le_bytes()

    # Any index >= 32 always returns all zeros
    is_msb_sum_zero = instruction.is_zero(FQ(sum(index[1:])))

    # Byte 0:
    # Check byte per byte if we need to copy the value
    # to result. We're only directly checking the LSB byte
    # of the index here, so also make sure the byte
    # is only copied when index < 32.
    is_byte_selected = [instruction.is_equal(FQ(index[0]), FQ(31 - idx)) for idx in range(32)]

    selected_byte = FQ(0)
    for cell, is_selected in zip(value, is_byte_selected):
        selected_byte += is_selected * is_msb_sum_zero * FQ(cell)

    instruction.constrain_equal_word(
        Word.from_lo(selected_byte),
        c,
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(3),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(1),
    )
