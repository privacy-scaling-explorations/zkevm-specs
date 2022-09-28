from ...util import (FQ, N_BYTES_ACCOUNT_ADDRESS,EMPTY_CODE_HASH,
GAS_COST_WARM_ACCESS, GAS_COST_ACCOUNT_COLD_ACCESS,
GAS_COST_CALL_WITH_VALUE,
                     )
from ..instruction import Instruction, Transition, FixedTableTag
from ..table import CallContextFieldTag, AccountFieldTag
from ..execution_state import ExecutionState
from ..opcode import Opcode
from ...util import N_BYTES_GAS


def oog_call(instruction: Instruction):
    # retrieve op code associated to oog constant error
    opcode = instruction.opcode_lookup(True)
    callee_call_id = instruction.curr.rw_counter

    # Lookup values from stack
    gas_rlc = instruction.stack_pop()
    callee_address_rlc = instruction.stack_pop()
    value = instruction.stack_pop()
    cd_offset_rlc = instruction.stack_pop()
    cd_length_rlc = instruction.stack_pop()
    rd_offset_rlc = instruction.stack_pop()
    rd_length_rlc = instruction.stack_pop()
    is_success = instruction.stack_push()

    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)
    reversion_info = instruction.reversion_info()
    caller_address = instruction.call_context_lookup(CallContextFieldTag.CalleeAddress)
    is_static = instruction.call_context_lookup(CallContextFieldTag.IsStatic)
    # check gas left is less than const gas required
    gas_is_u64 = instruction.is_zero(instruction.sum(gas_rlc.le_bytes[N_BYTES_GAS:]))
    cd_offset, cd_length = instruction.memory_offset_and_length(cd_offset_rlc, cd_length_rlc)
    rd_offset, rd_length = instruction.memory_offset_and_length(rd_offset_rlc, rd_length_rlc)

    # Verify memory expansion
    next_memory_size, memory_expansion_gas_cost = instruction.memory_expansion_dynamic_length(
        cd_offset,
        cd_length,
        rd_offset,
        rd_length,
    )

    # Check not is_static if call has value
    has_value = 1 - instruction.is_zero(value)
    instruction.constrain_zero(has_value * is_static)
    callee_address = instruction.rlc_to_fq(callee_address_rlc, N_BYTES_ACCOUNT_ADDRESS)

    # Add callee to access list
    is_warm_access = instruction.add_account_to_access_list(tx_id, callee_address, reversion_info)
    callee_reversion_info = instruction.reversion_info(call_id=callee_call_id)

    # Verify gas cost
    callee_nonce = instruction.account_read(callee_address, AccountFieldTag.Nonce)
    callee_code_hash = instruction.account_read(callee_address, AccountFieldTag.CodeHash)
    # Verify transfer
    _, (_, callee_balance_prev) = instruction.transfer(
        caller_address, callee_address, value, callee_reversion_info
    )
    is_empty_code_hash = instruction.is_equal(
        callee_code_hash, instruction.rlc_encode(EMPTY_CODE_HASH, 32)
    )
    is_account_empty = (
        instruction.is_zero(callee_nonce)
        * instruction.is_zero(callee_balance_prev)
        * is_empty_code_hash
    )
    gas_cost = (
        instruction.select(
            is_warm_access, FQ(GAS_COST_WARM_ACCESS), FQ(GAS_COST_ACCOUNT_COLD_ACCESS)
        )
        + has_value * (GAS_COST_CALL_WITH_VALUE + is_account_empty * GAS_COST_NEW_ACCOUNT)
        + memory_expansion_gas_cost
    )

    # verify gas is insufficient
    # gas_not_enough, _ = instruction.compare(
    #     instruction.curr.gas_left, const_gas_entry.value1, N_BYTES_GAS
    # )
    # instruction.constrain_equal(gas_not_enough, FQ(1))

    # current call must be failed.
    is_success = instruction.call_context_lookup(CallContextFieldTag.IsSuccess)
    instruction.constrain_equal(is_success, FQ(0))
    is_persistent = instruction.call_context_lookup(CallContextFieldTag.IsPersistent)
    instruction.constrain_equal(is_persistent, FQ(0))

    # Go to EndTx only when is_root
    is_to_end_tx = instruction.is_equal(instruction.next.execution_state, ExecutionState.EndTx)
    instruction.constrain_equal(FQ(instruction.curr.is_root), is_to_end_tx)

   # TODO:  state transition.