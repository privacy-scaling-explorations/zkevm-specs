from zkevm_specs.util.arithmetic import RLC
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
    is_success: FQ

    gas: FQ
    callee_address: FQ
    value: FQ
    cd_offset: FQ
    cd_length: FQ
    rd_offset: FQ
    rd_length: FQ

    next_memory_size: FQ
    memory_expansion_gas_cost: FQ

    def __init__(self, instruction: Instruction, is_oog: FQ, is_call_or_callcode: FQ = FQ(0)):
        self.instruction = instruction

        # Lookup values from stack
        self.gas_rlc = self.instruction.stack_pop()
        callee_address_rlc = self.instruction.stack_pop()
        # For non-OOG case,
        # the third stack pop `value` is not present for both DELEGATECALL and
        # STATICCALL opcodes.
        self.value = (
            self.instruction.stack_pop() if is_oog + is_call_or_callcode == FQ(1) else RLC(0)
        )
        cd_offset_rlc = self.instruction.stack_pop()
        cd_length_rlc = self.instruction.stack_pop()
        rd_offset_rlc = self.instruction.stack_pop()
        rd_length_rlc = self.instruction.stack_pop()
        self.is_success = self.instruction.stack_push()

        if is_oog == FQ(1):
            self.instruction.constrain_zero(self.is_success)
        else:  # for CALL, CALLCODE, DELEGATECALL and STATICCALL
            # Verify is_success is a bool
            self.instruction.constrain_bool(self.is_success)
            self.gas = instruction.rlc_to_fq(self.gas_rlc, N_BYTES_GAS)

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

    def has_value(self) -> int:
        return 1 - self.instruction.is_zero(self.value)

    def is_call_succeeded(self) -> bool:
        return self.is_success.expr() == FQ(1)

    def gas_cost(self, is_warm_access: FQ, is_call: FQ, is_account_empty: FQ) -> FQ:
        return (
            self.instruction.select(
                is_warm_access, FQ(GAS_COST_WARM_ACCESS), FQ(GAS_COST_ACCOUNT_COLD_ACCESS)
            )
            + self.has_value()
            * (
                GAS_COST_CALL_WITH_VALUE
                # Only CALL opcode could invoke transfer to make empty account into non-empty.
                + is_call * is_account_empty * GAS_COST_NEW_ACCOUNT
            )
            + self.memory_expansion_gas_cost
        )

    def callee_gas_left(self, gas_cost: FQ) -> FQ:
        is_u64_gas = self.instruction.is_zero(
            self.instruction.sum(self.gas_rlc.le_bytes[N_BYTES_GAS:])
        )
        # Apply EIP 150.
        # Note that sufficient gas_left is checked implicitly by constant_divmod.
        gas_available = self.instruction.curr.gas_left - gas_cost
        one_64th_gas, _ = self.instruction.constant_divmod(gas_available, FQ(64), N_BYTES_GAS)
        all_but_one_64th_gas = gas_available - one_64th_gas
        return self.instruction.select(
            is_u64_gas,
            self.instruction.min(all_but_one_64th_gas, self.gas, N_BYTES_GAS),
            all_but_one_64th_gas,
        )
