from ..instruction import Instruction, Transition
from ..opcode import Opcode

def scmp(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    is_sgt, _ = instruction.pair_select(opcode, Opcode.SGT, Opcode.LGT)

    a = instruction.stack_pop()
    b = instruction.stack_pop()
    c = instruction.stack_push()

    # decode RLC to bytes for a and b
    a8s = instruction.rlc_to_bytes(a, 32)
    b8s = instruction.rlc_to_bytes(b, 32)
    aa = instruction.bytes_to_int(a8s)
    bb = instruction.bytes_to_int(b8s)
    cc = instruction.bytes_to_int(instruction.rlc_to_bytes(c, 32))

    # c is the result and hence should be binary
    instruction.constrain_bool(cc)

    # a is positive and b is negative
    if a8s[0] < 128 and b8s[0] >= 128:
        instruction.constrain_equal(
            instruction.select(is_sgt, 1, 0),
            cc,
        )
    # b is negative and a is positive
    elif b8s[0] < 128 and a8s[0] >= 128:
        instruction.constrain_equal(
            instruction.select(is_sgt, 0, 1),
            cc,
        )
    # both a and b are of the same sign (positive/negative)
    else:
        instruction.constrain_equal(
            instruction.select(is_sgt, int(bb < aa), int(aa < bb)),
            cc,
        )

    instruction.constrain_same_context_state_transition(
        opcode,
        rw_counter=Transition.delta(3),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(1),
    )
