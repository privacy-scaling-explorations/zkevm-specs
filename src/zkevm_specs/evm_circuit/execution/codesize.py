from ...util import Word
from ..instruction import Instruction, Transition
from ..opcode import Opcode


def codesize(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.CODESIZE)

    code_size = instruction.bytecode_length(instruction.curr.code_hash)

    instruction.constrain_equal_word(Word.from_lo(code_size), instruction.stack_push())

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(1),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(-1),
    )
