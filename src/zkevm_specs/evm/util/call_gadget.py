from zkevm_specs.evm.table import AccountFieldTag
from zkevm_specs.util.arithmetic import RLC, Word
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
    value: Word
    cd_offset: FQ
    cd_length: FQ
    rd_offset: FQ
    rd_length: FQ
    is_success: FQ

    is_u64_gas: FQ
    next_memory_size: FQ
    memory_expansion_gas_cost: FQ

    has_value: FQ
    callee_code_hash: Word
    is_empty_code_hash: FQ
    callee_not_exists: FQ

    def __init__(
        self,
        instruction: Instruction,
        is_success_call: FQ,
        is_call: FQ,
        is_callcode: FQ,
        is_delegatecall: FQ,
    ):
        self.IS_SUCCESS_CALL = is_success_call

        # Lookup values from stack
        gas = instruction.stack_pop()
        callee_address = instruction.stack_pop()
        # For non-OOG case,
        # the third stack pop `value` is not present for both DELEGATECALL and
        # STATICCALL opcodes.
        self.value = instruction.stack_pop() if is_call + is_callcode == FQ(1) else Word(0)
        cd_offset = instruction.stack_pop()
        cd_length = instruction.stack_pop()
        rd_offset = instruction.stack_pop()
        rd_length = instruction.stack_pop()
        result = instruction.stack_push()
        self.is_success = result.lo.expr()
        instruction.constrain_equal_word(Word((self.is_success, FQ(0))), result)

        if self.IS_SUCCESS_CALL == FQ(1):
            # Verify is_success is a bool
            instruction.constrain_bool(self.is_success)
            self.gas = instruction.word_to_fq(gas, N_BYTES_GAS)
            self.is_u64_gas = instruction.is_zero(
                instruction.sum(gas.to_le_bytes()[N_BYTES_GAS:])
            )
        else:
            instruction.constrain_zero(self.is_success)
        self.has_value = FQ(0) if is_delegatecall == FQ(1) else 1 - instruction.is_zero_word(self.value)

        self.callee_address = instruction.word_to_fq(callee_address, N_BYTES_ACCOUNT_ADDRESS)
        self.cd_offset, self.cd_length = instruction.memory_offset_and_length(
            cd_offset, cd_length
        )
        self.rd_offset, self.rd_length = instruction.memory_offset_and_length(
            rd_offset, rd_length
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

        # Check callee account existence with code_hash != 0
        self.callee_code_hash = instruction.account_read(
            self.callee_address, AccountFieldTag.CodeHash
        )
        self.is_empty_code_hash = instruction.is_equal_word(
            self.callee_code_hash, Word(EMPTY_CODE_HASH)
        )
        self.callee_not_exists = instruction.is_zero_word(self.callee_code_hash)

    def gas_cost(
        self,
        instruction: Instruction,
        is_warm_access: FQ,
        is_call: FQ = FQ(1),
    ) -> FQ:
        return (
            instruction.select(
                is_warm_access, FQ(GAS_COST_WARM_ACCESS), FQ(GAS_COST_ACCOUNT_COLD_ACCESS)
            )
            + self.has_value
            * (GAS_COST_CALL_WITH_VALUE + is_call * self.callee_not_exists * GAS_COST_NEW_ACCOUNT)
            + self.memory_expansion_gas_cost
        )
