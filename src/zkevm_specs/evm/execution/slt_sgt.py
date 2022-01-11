from ..instruction import Instruction, Transition
from ..opcode import Opcode

from zkevm_specs.encoding import U256, u256_to_u8s

def scmp(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    is_sgt, _ = instruction.pair_select(opcode, Opcode.SGT, Opcode.LGT)

    a = instruction.stack_pop()
    b = instruction.stack_pop()
    c = instruction.stack_push()

    a8s = u256_to_u8s(U256(a))
    b8s = u256_to_u8s(U256(b))
    c8s = u256_to_u8s(U256(c))

    # if both a and b are unsigned
    if a8s[0] < 128 and b8s[0] < 128:
        instruction.constrain_equal(
            instruction.select(is_sgt, b < a, a < b),
            c,
        )
    # only a is unsigned
    elif a8s[0] < 128:
        instruction.constrain_equal(
            instruction.select(is_sgt, 1, 0),
            c,
        )
    # only b is unsigned
    elif b8s[0] < 128:
        instruction.constrain_equal(
            instruction.select(is_sgt, 0, 1),
            c,
        )
    # both a and b are signed
    else:
        instruction.constrain_equal(
            instruction.select(is_sgt, a < b, b < a),
            c,
        )

    instruction.constrain_same_context_state_transition(
        opcode,
        rw_counter=Transition.delta(3),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(1),
    )
