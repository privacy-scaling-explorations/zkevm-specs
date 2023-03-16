from ...util import FQ
from ..instruction import Instruction, Transition
from ..opcode import Opcode


def scmp(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    is_sgt, _ = instruction.pair_select(opcode, Opcode.SGT, Opcode.SLT)

    a = instruction.stack_pop()
    b = instruction.stack_pop()
    c = instruction.stack_push()

    # swap a and b if the opcode is SGT
    aa = b if is_sgt == 1 else a
    bb = a if is_sgt == 1 else b

    # decode RLC to bytes for a and b
    a8s = aa.le_bytes
    b8s = bb.le_bytes
    c8s = c.le_bytes

    a_lo = instruction.bytes_to_fq(a8s[:16])
    a_hi = instruction.bytes_to_fq(a8s[16:])
    b_lo = instruction.bytes_to_fq(b8s[:16])
    b_hi = instruction.bytes_to_fq(b8s[16:])
    assert c8s[31] == 0
    cc = instruction.bytes_to_fq(c8s[:31])

    a_lt_b_lo, _ = instruction.compare(a_lo, b_lo, 16)
    a_lt_b_hi, a_eq_b_hi = instruction.compare(a_hi, b_hi, 16)

    a_lt_b = instruction.select(
        a_lt_b_hi, FQ(1), instruction.select(a_eq_b_hi * a_lt_b_lo, FQ(1), FQ(0))
    )

    # a < 0 and b >= 0 => a < b == true
    if a8s[31] >= 128 and b8s[31] < 128:
        instruction.constrain_equal(cc, FQ(1))
    # b < 0 and a >= 0 => a < b == false
    elif b8s[31] >= 128 and a8s[31] < 128:
        instruction.constrain_equal(cc, FQ(0))
    # (a < 0 and b < 0) or (a >= 0 and b >= 0)
    else:
        instruction.constrain_equal(cc, a_lt_b)

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(3),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(1),
    )
