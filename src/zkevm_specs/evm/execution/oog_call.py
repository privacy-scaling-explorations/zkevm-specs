from ...util import (
    FQ,
    N_BYTES_ACCOUNT_ADDRESS,
    EMPTY_CODE_HASH,
    GAS_COST_WARM_ACCESS,
    GAS_COST_ACCOUNT_COLD_ACCESS,
    GAS_COST_CALL_WITH_VALUE,
    GAS_COST_NEW_ACCOUNT,
)
from ..instruction import Instruction, Transition
from ..table import CallContextFieldTag, AccountFieldTag
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
    # Lookup values from stack
    instruction.stack_pop()
    callee_address_rlc = instruction.stack_pop()
    value = instruction.stack_pop()
    cd_offset_rlc = instruction.stack_pop()
    cd_length_rlc = instruction.stack_pop()
    rd_offset_rlc = instruction.stack_pop()
    rd_length_rlc = instruction.stack_pop()
    is_success = instruction.stack_push()
    instruction.constrain_zero(is_success)

    cd_offset, cd_length = instruction.memory_offset_and_length(cd_offset_rlc, cd_length_rlc)
    rd_offset, rd_length = instruction.memory_offset_and_length(rd_offset_rlc, rd_length_rlc)

    # Verify memory expansion
    next_memory_size, memory_expansion_gas_cost = instruction.memory_expansion_dynamic_length(
        cd_offset,
        cd_length,
        rd_offset,
        rd_length,
    )

    has_value = 1 - instruction.is_zero(value)
    callee_address = instruction.rlc_to_fq(callee_address_rlc, N_BYTES_ACCOUNT_ADDRESS)

    # TODO: handle PrecompiledContract oog cases

    # Add callee to access list
    is_warm_access = instruction.read_account_to_access_list(tx_id, callee_address)

    # lookup balance of callee
    callee_balance = instruction.account_read(callee_address, AccountFieldTag.Balance)
    # Verify gas cost
    callee_nonce = instruction.account_read(callee_address, AccountFieldTag.Nonce)
    callee_code_hash = instruction.account_read(callee_address, AccountFieldTag.CodeHash)

    is_empty_code_hash = instruction.is_equal(
        callee_code_hash, instruction.rlc_encode(EMPTY_CODE_HASH, 32)
    )
    is_account_empty = (
        instruction.is_zero(callee_nonce) * instruction.is_zero(callee_balance) * is_empty_code_hash
    )
    gas_cost = (
        instruction.select(
            is_warm_access, FQ(GAS_COST_WARM_ACCESS), FQ(GAS_COST_ACCOUNT_COLD_ACCESS)
        )
        + has_value * (GAS_COST_CALL_WITH_VALUE + is_account_empty * GAS_COST_NEW_ACCOUNT)
        + memory_expansion_gas_cost
    )

    # verify gas is insufficient or gas cost is overflow
    gas_not_enough, _ = instruction.compare(instruction.curr.gas_left, gas_cost, N_BYTES_GAS)
    gas_cost_overflow = instruction.is_u64_overflow(gas_cost)
    instruction.constrain_equal(gas_not_enough + gas_cost_overflow, FQ(1))

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
            rw_counter=Transition.delta(15),
            call_id=Transition.same(),
        )
    else:
        # when it is internal call, need to restore caller's state as finishing this call.
        # Restore caller state to next StepState
        instruction.step_state_transition_to_restored_context(
            rw_counter_delta=15,
            return_data_offset=FQ(0),
            return_data_length=FQ(0),
            gas_left=instruction.curr.gas_left,
        )
