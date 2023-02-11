from zkevm_specs.evm.util.call_gadget import CallGadget
from ...util import FQ
from ..instruction import Instruction, Transition
from ..table import CallContextFieldTag
from ..opcode import Opcode


def gas_uint_overflow(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    is_call = instruction.is_equal(opcode, Opcode.CALL)

    # memory size overflow flag.
    memory_size = instruction.call_context_lookup(CallContextFieldTag.MemorySize)
    is_memory_size_overflow = instruction.is_memory_overflow(memory_size)

    # call gas_cost overflow flag.
    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)
    call = CallGadget(instruction, FQ(0), FQ(1), FQ(0), FQ(0))
    is_warm_access = instruction.read_account_to_access_list(tx_id, call.callee_address)
    gas_cost = call.gas_cost(instruction, is_warm_access)
    is_call_gas_cost_overflow = is_call * instruction.is_u64_overflow(gas_cost)

    # verify gas uint overflow.
    is_overflow = (is_memory_size_overflow + is_call_gas_cost_overflow).n >= 1
    instruction.constrain_equal(FQ(is_overflow), FQ(1))

    # verify call failure.
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
