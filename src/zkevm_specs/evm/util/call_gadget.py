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


class CallGadget:
    IS_SUCCESS_CALL: FQ

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

    has_value: FQ
    callee_code_hash: FQ
    is_empty_code_hash: FQ

    def __init__(
        self,
        instruction: Instruction,
        is_success_call: FQ,
        is_call: FQ,
        is_callcode: FQ,
        is_delegatecall: FQ,
    ):
        self.instruction = instruction
        self.IS_SUCCESS_CALL = is_success_call

        # Lookup values from stack
        self.gas_rlc = self.instruction.stack_pop()
        callee_address_rlc = self.instruction.stack_pop()
        # For non-OOG case,
        # the third stack pop `value` is not present for both DELEGATECALL and
        # STATICCALL opcodes.
        self.value = self.instruction.stack_pop() if is_call + is_callcode == FQ(1) else RLC(0)
        cd_offset_rlc = self.instruction.stack_pop()
        cd_length_rlc = self.instruction.stack_pop()
        rd_offset_rlc = self.instruction.stack_pop()
        rd_length_rlc = self.instruction.stack_pop()
        self.is_success = self.instruction.stack_push()

        if self.IS_SUCCESS_CALL == FQ(1):
            # Verify is_success is a bool
            self.instruction.constrain_bool(self.is_success)
            self.gas = instruction.rlc_to_fq(self.gas_rlc, N_BYTES_GAS)
            self.is_u64_gas = instruction.is_zero(
                instruction.sum(self.gas_rlc.le_bytes[N_BYTES_GAS:])
            )
        else:
            self.instruction.constrain_zero(self.is_success)
            self.gas = FQ(0)
            self.is_u64_gas = FQ(0)

        self.has_value = FQ(0) if is_delegatecall == FQ(1) else 1 - instruction.is_zero(self.value)

        self.callee_address = instruction.rlc_to_fq(callee_address_rlc, N_BYTES_ACCOUNT_ADDRESS)
        self.cd_offset, self.cd_length = instruction.memory_offset_and_length(
            cd_offset_rlc, cd_length_rlc
        )
        self.rd_offset, self.rd_length = instruction.memory_offset_and_length(
            rd_offset_rlc, rd_length_rlc
        )
        # Verify memory expansion
        (
            self.next_memory_size,
            self.memory_expansion_gas_cost,
        ) = instruction.memory_expansion_dynamic_length(
            self.cd_offset,
            self.cd_length,
            self.rd_offset,
            self.rd_length,
        )

    def gas_cost(
        self,
        instruction: Instruction,
        is_warm_access: FQ,
        callee_exists: FQ,
        is_call: FQ = FQ(1),
    ) -> FQ:

        if callee_exists == 1:
            # Check callee account existence with code_hash != 0
            self.callee_code_hash = instruction.account_read(
                self.callee_address, AccountFieldTag.CodeHash
            )
            self.is_empty_code_hash = instruction.is_equal(
                self.callee_code_hash, instruction.rlc_encode(EMPTY_CODE_HASH, 32)
            )
        else:  # callee_exists == 0
            instruction.account_read(self.callee_address, AccountFieldTag.NonExisting)
            self.is_empty_code_hash = FQ(1)

        return (
            instruction.select(
                is_warm_access, FQ(GAS_COST_WARM_ACCESS), FQ(GAS_COST_ACCOUNT_COLD_ACCESS)
            )
            + self.has_value
            * (GAS_COST_CALL_WITH_VALUE + is_call * (1 - callee_exists) * GAS_COST_NEW_ACCOUNT)
            + self.memory_expansion_gas_cost
        )
