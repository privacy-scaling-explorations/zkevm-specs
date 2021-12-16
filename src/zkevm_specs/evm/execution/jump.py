from ..instruction import Instruction, Transition
from ..opcode import Opcode


def jump(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    print(opcode)
    # Do not check 'dest' is within MaxCodeSize(24576) range in successful case
    # as byte code lookup can ensure it.
    dest = instruction.stack_pop()

    # Get `dest` raw value in max three bytes
    bytes = instruction.rlc_to_bytes(dest, 32)
    dest_value = instruction.bytes_to_int(bytes[:3])

    # bytes = instruction.rlc_to_bytes(dest, 32)[-3:][::-1]
    print(bytes)
    print(dest_value)

    pc_diff = dest_value - instruction.curr.program_counter
    #Verify `dest` is code within byte code table
    # assert Opcode.JUMPDEST == instruction.opcode_lookup_at(dest_value, True)
    code = instruction.opcode_lookup_at(dest_value, True)
    print(code)

    instruction.constrain_equal(
        Opcode.JUMPDEST,
        instruction.opcode_lookup_at(dest_value, True)
    )

    instruction.constrain_same_context_state_transition(
        opcode,
        rw_counter=Transition.delta(1),
        program_counter=Transition.delta(pc_diff),
        stack_pointer=Transition.delta(1),
    )
