from zkevm_specs.evm.util.call_gadget import CallGadget
from ...util import FQ
from ..instruction import Instruction, Transition
from ..table import CallContextFieldTag
from ..execution_state import ExecutionState
from ...util import N_BYTES_GAS
from ..opcode import Opcode


def oog_call(instruction: Instruction):
    # retrieve op code associated to oog call error
    opcode = instruction.opcode_lookup(True)
    # TODO: add CallCode etc.when handle ErrorOutOfGasCALLCODE in future implementation
    instruction.constrain_equal(opcode, Opcode.CALL)

    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)
    instruction.call_context_lookup(CallContextFieldTag.IsStatic)

    call = CallGadget(instruction, FQ(0), FQ(1), FQ(0), FQ(0))

    # TODO: handle PrecompiledContract oog cases

    # Add callee to access list``
    is_warm_access = instruction.read_account_to_access_list(tx_id, call.callee_address)

    # Load callee account `exists` value from auxilary witness data.
    callee_exists = instruction.curr.aux_data
    gas_cost = call.gas_cost(instruction, is_warm_access, callee_exists)

    # verify gas is insufficient
    gas_not_enough, _ = instruction.compare(instruction.curr.gas_left, gas_cost, N_BYTES_GAS)
    instruction.constrain_equal(gas_not_enough, FQ(1))

    # current call must be failed.
    instruction.constrain_equal(
        instruction.call_context_lookup(CallContextFieldTag.IsSuccess), FQ(0)
    )

    # Go to EndTx only when is_root
    is_to_end_tx = instruction.is_equal(instruction.next.execution_state, ExecutionState.EndTx)
    instruction.constrain_equal(FQ(instruction.curr.is_root), is_to_end_tx)

    # state transition.
    if instruction.curr.is_root:
        # Do step state transition
        instruction.constrain_step_state_transition(
            rw_counter=Transition.delta(14),
            call_id=Transition.same(),
        )
    else:
        # when it is internal call, need to restore caller's state as finishing this call.
        # Restore caller state to next StepState
        instruction.step_state_transition_to_restored_context(
            rw_counter_delta=14,
            return_data_offset=FQ(0),
            return_data_length=FQ(0),
            gas_left=instruction.curr.gas_left,
        )
