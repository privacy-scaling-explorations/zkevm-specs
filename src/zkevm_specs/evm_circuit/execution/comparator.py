from ...util import FQ, Word
from ..instruction import Instruction, Transition
from ..opcode import Opcode


def cmp(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    is_eq = instruction.is_equal(opcode, Opcode.EQ)
    is_gt = instruction.is_equal(opcode, Opcode.GT)

    a = instruction.stack_pop()
    b = instruction.stack_pop()
    c = instruction.stack_push()

    # swap a and b if the opcode is GT
    (aa, bb) = (b, a) if is_gt == 1 else (a, b)

    a_lo, a_hi = aa.to_lo_hi()
    b_lo, b_hi = bb.to_lo_hi()

    # `a[0..16] <= b[0..16]`
    lt_lo, eq_lo = instruction.compare(a_lo, b_lo, 16)

    # `a[16..32] <= b[16..32]`
    lt_hi, eq_hi = instruction.compare(a_hi, b_hi, 16)

    lt = instruction.select(lt_hi, FQ(1), eq_hi * lt_lo)
    eq = eq_lo * eq_hi

    result = eq if is_eq == 1 else lt

    instruction.constrain_equal_word(
        Word.from_lo(FQ(result)),
        c,
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(3),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(1),
    )
