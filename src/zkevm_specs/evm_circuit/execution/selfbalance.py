from ..instruction import Instruction, Transition
from ..table import AccountFieldTag, CallContextFieldTag
from ..opcode import Opcode


def selfbalance(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.SELFBALANCE)

    callee_address_word = instruction.call_context_lookup_word(CallContextFieldTag.CalleeAddress)
    callee_address = instruction.word_to_address(callee_address_word)
    balance = instruction.account_read_word(callee_address, AccountFieldTag.Balance)
    instruction.constrain_equal_word(instruction.stack_push(), balance)

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(3),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(-1),
    )
