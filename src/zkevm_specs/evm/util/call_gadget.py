from dataclasses import dataclass
from typing import Tuple
from zkevm_specs.evm.table import AccountFieldTag
from zkevm_specs.util.arithmetic import RLC
from zkevm_specs.util.hash import EMPTY_CODE_HASH
from zkevm_specs.util.param import (
    GAS_COST_ACCOUNT_COLD_ACCESS,
    GAS_COST_CALL_WITH_VALUE,
    GAS_COST_NEW_ACCOUNT,
    GAS_COST_WARM_ACCESS,
)
from ...util import (
    FQ,
    N_BYTES_ACCOUNT_ADDRESS,
    N_BYTES_GAS,
    RLC,
)
from ..instruction import Instruction


@dataclass
class CallStruct:

    gas: FQ
    callee_address: FQ
    value: RLC
    cd_offset: FQ
    cd_length: FQ
    rd_offset: FQ
    rd_length: FQ
    is_success: RLC

    is_u64_gas: FQ
    next_memory_size: FQ
    memory_expansion_gas_cost: FQ


def common_call_stack_pop(
    instruction: Instruction, is_oog: FQ, is_call_or_callcode: FQ = FQ(0)
) -> CallStruct:
    # Lookup values from stack
    gas_rlc = instruction.stack_pop()
    callee_address_rlc = instruction.stack_pop()
    # the third stack pop `value` is not present for both DELEGATECALL and
    # STATICCALL opcodes.
    value = instruction.stack_pop() if is_oog + is_call_or_callcode == FQ(1) else RLC(0)
    cd_offset_rlc = instruction.stack_pop()
    cd_length_rlc = instruction.stack_pop()
    rd_offset_rlc = instruction.stack_pop()
    rd_length_rlc = instruction.stack_pop()
    is_success = instruction.stack_push()

    if is_oog == FQ(1):
        instruction.constrain_zero(is_success)
        gas = FQ(0)
        is_u64_gas = FQ(0)
    else:  # for CALL, CALLCODE, DELEGATECALL and STATICCALL
        # Verify is_success is a bool
        instruction.constrain_bool(is_success)
        gas = instruction.rlc_to_fq(gas_rlc, N_BYTES_GAS)
        is_u64_gas = instruction.is_zero(instruction.sum(gas_rlc.le_bytes[N_BYTES_GAS:]))

    callee_address = instruction.rlc_to_fq(callee_address_rlc, N_BYTES_ACCOUNT_ADDRESS)
    cd_offset, cd_length = instruction.memory_offset_and_length(cd_offset_rlc, cd_length_rlc)
    rd_offset, rd_length = instruction.memory_offset_and_length(rd_offset_rlc, rd_length_rlc)
    # Verify memory expansion
    (next_memory_size, memory_expansion_gas_cost,) = instruction.memory_expansion_dynamic_length(
        cd_offset,
        cd_length,
        rd_offset,
        rd_length,
    )
    return CallStruct(
        gas,
        callee_address,
        value,
        cd_offset,
        cd_length,
        rd_offset,
        rd_length,
        is_success,
        is_u64_gas,
        next_memory_size,
        memory_expansion_gas_cost,
    )


def common_call_gas_cost(
    instruction: Instruction,
    has_value: FQ,
    memory_expansion_gas_cost: FQ,
    is_warm_access: FQ,
    is_account_empty: FQ,
) -> FQ:
    return (
        instruction.select(
            is_warm_access, FQ(GAS_COST_WARM_ACCESS), FQ(GAS_COST_ACCOUNT_COLD_ACCESS)
        )
        + has_value * (GAS_COST_CALL_WITH_VALUE + is_account_empty * GAS_COST_NEW_ACCOUNT)
        + memory_expansion_gas_cost
    )


def common_call_is_empty_code_hash(
    instruction: Instruction, callee_address: FQ, is_oog: FQ
) -> Tuple[FQ, FQ, RLC]:
    callee_code_hash = instruction.account_read(callee_address, AccountFieldTag.CodeHash)
    # Check callee account existence with code_hash != 0
    callee_exists = FQ(1) - instruction.is_zero(callee_code_hash)
    if is_oog + callee_exists == FQ(1):
        return (
            callee_exists,
            instruction.is_equal(callee_code_hash, instruction.rlc_encode(EMPTY_CODE_HASH, 32)),
            callee_code_hash,
        )
    else:  # for (CALL, CALLCODE, DELEGATECALL and STATICCALL) && callee_exists == 0
        # instruction.account_read(callee_address, AccountFieldTag.NonExisting)
        return callee_exists, FQ(1), RLC(0)
