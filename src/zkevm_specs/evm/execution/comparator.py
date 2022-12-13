from ...util import FQ
from ..instruction import Instruction, Transition
from ..opcode import Opcode


def cmp(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    is_eq, is_gt = instruction.pair_select(opcode, Opcode.EQ, Opcode.GT)

    a = instruction.stack_pop()
    b = instruction.stack_pop()
    c = instruction.stack_push()

    print("limbs", a, b, c)
    # swap a and b if the opcode is GT
    (aa, bb) = (b, a) if is_gt == 1 else (a, b)

    # decode RLC to bytes for a and b
    a8s = aa.le_bytes
    b8s = bb.le_bytes
    c8s = c.le_bytes

    a_lo = instruction.bytes_to_fq(a8s[:16])
    a_hi = instruction.bytes_to_fq(a8s[16:])
    b_lo = instruction.bytes_to_fq(b8s[:16])
    b_hi = instruction.bytes_to_fq(b8s[16:])
    cc = instruction.bytes_to_fq(c8s[:31])

    # `a[0..16] <= b[0..16]`
    lt_lo, eq_lo = instruction.compare(a_lo, b_lo, 16)

    # `a[16..32] <= b[16..32]`
    lt_hi, eq_hi = instruction.compare(a_hi, b_hi, 16)

    lt = instruction.select(lt_hi, FQ(1), eq_hi * lt_lo)
    eq = eq_lo * eq_hi

    result = eq if is_eq == 1 else lt

    instruction.constrain_equal(
        cc,
        FQ(result),
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(3),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(1),
    )
