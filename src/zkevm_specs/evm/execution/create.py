from ...util import (
    EMPTY_CODE_HASH,
    FQ,
    GAS_COST_ACCOUNT_COLD_ACCESS,
    GAS_COST_CALL_WITH_VALUE,
    GAS_COST_NEW_ACCOUNT,
    GAS_COST_WARM_ACCESS,
    GAS_STIPEND_CALL_WITH_VALUE,
    N_BYTES_ACCOUNT_ADDRESS,
    N_BYTES_GAS,
    CALL_CREATE_DEPTH,
    RLC,
)
from ..instruction import Instruction, Transition
from ..opcode import Opcode
from ..table import RW, CallContextFieldTag, AccountFieldTag
from ..precompiled import PrecompiledAddress


def create(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    is_create, is_create2 = instruction.select(opcode, (Opcode.CREATE, Opcode.CREATE2))
    instruction.responsible_opcode_lookup(opcode)

    value = instruction.stack_pop()
    offset = instruction.stack_pop()
    size = instruction.stack_pop()
    input = instruction.stack_pop()
    gas = instruction.stack_push()

    depth = instruction.call_context_lookup(CallContextFieldTag.Depth)
    tx_caller_address = instruction.call_context_lookup(CallContextFieldTag.CallerAddress)
    nonce, nonce_prev = instruction.account_write(parent_caller_address, AccountFieldTag.Nonce)

    # ErrDepth constraint
    instruction.range_lookup(depth, CALL_CREATE_DEPTH)
    # ErrNonceUintOverflow constraint
    (is_not_overflow, _) = instruction.compare(nonce, nonce_prev, 8)
    instruction.is_zero(is_not_overflow)
    # ErrInsufficientBalance constraint
    gas_cost = (
        instruction.select(
            is_warm_access, FQ(GAS_COST_WARM_ACCESS), FQ(GAS_COST_ACCOUNT_COLD_ACCESS)
        )
        + has_value
        * (
            GAS_COST_CALL_WITH_VALUE
            # Only CALL opcode could invoke transfer to make empty account into non-empty.
            + is_call * (1 - callee_exists) * GAS_COST_NEW_ACCOUNT
        )
        + memory_expansion_gas_cost
    )
    # Apply EIP 150.
    # Note that sufficient gas_left is checked implicitly by constant_divmod.
    gas_available = instruction.curr.gas_left - gas_cost
    one_64th_gas, _ = instruction.constant_divmod(gas_available, FQ(64), N_BYTES_GAS)
    all_but_one_64th_gas = gas_available - one_64th_gas
    callee_gas_left = instruction.select(
        gas_is_u64,
        instruction.min(all_but_one_64th_gas, gas, N_BYTES_GAS),
        all_but_one_64th_gas,
    )
