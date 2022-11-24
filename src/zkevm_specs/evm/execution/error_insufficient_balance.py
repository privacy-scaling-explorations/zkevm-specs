from ...util import FQ
from ..instruction import Instruction, Transition
from ..table import CallContextFieldTag, AccountFieldTag
from ..opcode import Opcode


def insufficient_balance(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    # TODO: add Create / Create2 in the future
    instruction.constrain_in(opcode, [FQ(Opcode.CALL), FQ(Opcode.CALLCODE)])
    # TODO: for create/create2 have different stack from Call, will handle it in the future
    # Lookup values from stack
    instruction.stack_pop()
    instruction.stack_pop()
    value_rlc = instruction.stack_pop()
    instruction.stack_pop()
    instruction.stack_pop()
    instruction.stack_pop()
    instruction.stack_pop()
    is_success_rlc = instruction.stack_push()
    # if is_success_rlc value is zero then decode RLC should also be zero
    instruction.constrain_zero(is_success_rlc)

    value = instruction.rlc_to_fq(value_rlc, 31)
    current_address = instruction.call_context_lookup(CallContextFieldTag.CalleeAddress)
    caller_balance_rlc = instruction.account_read(current_address, AccountFieldTag.Balance)
    caller_balance = instruction.rlc_to_fq(caller_balance_rlc, 31)
    # compare value and balance
    insufficient_balance, _ = instruction.compare(caller_balance, value, 31)

    instruction.constrain_equal(insufficient_balance, FQ(1))

    # Do step state transition
    instruction.constrain_step_state_transition(
        call_id=Transition.same(),
        rw_counter=Transition.delta(10),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(6),
        # TODO: handle gas_left
    )
