from zkevm_specs.evm.util.call_gadget import CallGadget
from ...util import FQ
from ..instruction import Instruction, Transition
from ..table import CallContextFieldTag
from ..opcode import Opcode


def gas_uint_overflow(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    instruction.constrain_equal(opcode, Opcode.CALL)

    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)

    # init CallGadget to handle stack vars.
    call = CallGadget(instruction, FQ(0), FQ(1), FQ(0), FQ(0))

    # Add callee to access list
    is_warm_access = instruction.read_account_to_access_list(tx_id, call.callee_address)

    # verify gas cost
    gas_cost = call.gas_cost(instruction, is_warm_access)

    # check gas cost is u64 overflow
    instruction.is_u64_overflow(gas_cost)

    # current call must be failed.
    instruction.constrain_equal(
        instruction.call_context_lookup(CallContextFieldTag.IsSuccess), FQ(0)
    )

    # state transition.
    if instruction.curr.is_root:
        # Do step state transition
        instruction.constrain_step_state_transition(
            rw_counter=Transition.delta(12),
            call_id=Transition.same(),
        )
    else:
        # when it is internal call, need to restore caller's state as finishing this call.
        # Restore caller state to next StepState
        instruction.step_state_transition_to_restored_context(
            rw_counter_delta=12,
            return_data_offset=FQ(0),
            return_data_length=FQ(0),
            gas_left=instruction.curr.gas_left,
        )
