from ..instruction import Instruction, Transition
from zkevm_specs.util import FQ


def signextend(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    index = instruction.stack_pop()
    value = instruction.stack_pop()
    result = instruction.stack_push()

    index_le_bytes = index.to_le_bytes()
    value_le_bytes = value.to_le_bytes()
    result_le_bytes = result.to_le_bytes()

    # Any index value >= 256 always returns the same value
    is_msb_sum_zero = instruction.is_zero(FQ(sum(index_le_bytes[1:32])))
    sign_byte = (
        FQ((value_le_bytes[index_le_bytes[0].n].n >> 7) * 0xFF)
        if index_le_bytes[0].n < 31
        else FQ(0)
    )
    selectors = [FQ(index_le_bytes[0].n >= i) for i in range(31)]
    is_byte_selected = [FQ(index_le_bytes[0].n == i) for i in range(31)]

    # Check byte per byte to see if the byte was selected.
    # We're only directly checking the LSB byte
    # of the index here, so also make sure the byte
    # is only copied when index < 256.
    # There is no need to check the MSB, even if the MSB is selected
    # no bytes need to be changed (so this loops only up to 31).
    selected_byte = FQ(0)
    for i in range(31):
        is_selected = is_byte_selected[i] * is_msb_sum_zero
        selected_byte += value_le_bytes[i] * is_selected
        # Verify the selector
        instruction.is_equal(is_selected + (selectors[i - 1] if i > 0 else FQ(0)), selectors[i])

    # Lookup the sign byte which will be used for doing the extending
    instruction.sign_byte_lookup(selected_byte, sign_byte)

    # Byte 0 always remains the same.
    # All other bytes need to be changed to the sign byte when the selector is enabled.
    # When a byte was selected all the **following** bytes need to be replaced,
    # (hence the `selectors[i-1]`).
    for idx in range(32):
        if idx == 0:
            instruction.is_equal(FQ(result_le_bytes[idx]), FQ(value_le_bytes[idx]))
        else:
            instruction.is_equal(
                FQ(result_le_bytes[idx]),
                sign_byte if selectors[idx - 1] == FQ(1) else FQ(value_le_bytes[idx]),
            )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(3),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(1),
    )
