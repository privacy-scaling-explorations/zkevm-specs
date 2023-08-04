from zkevm_specs.util.param import (
    GAS_COST_INITCODE_WORD,
    GAS_COST_TX_CALL_DATA_PER_NON_ZERO_BYTE,
    GAS_COST_TX_CALL_DATA_PER_ZERO_BYTE,
)
from ...util import (
    FQ,
    TxDataNonZeroGasEIP2028,
    MAX_U64,
    N_BYTES_U64,
    TxGas,
    TxGasContractCreation,
)
from ..instruction import Instruction
from ..table import CallContextFieldTag
from ..opcode import Opcode


def error_gas_uint_overflow(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    (
        is_call,
        _,
        is_delegatecall,
        is_staticcall,
        is_create_flag,
        is_create2_flag,
        is_calldatacopy,
        is_codecopy,
        is_extcodecopy,
        is_returndatacopy,
        is_log0,
        is_log1,
        is_log2,
        is_log3,
        is_log4,
        is_sha3,
        _,
        is_mload,
        is_mstore,
        is_mstore8,
        is_return,
        is_revert,
    ) = instruction.multiple_select(
        opcode,
        (
            Opcode.CALL,
            Opcode.CALLCODE,
            Opcode.DELEGATECALL,
            Opcode.STATICCALL,
            Opcode.CREATE,
            Opcode.CREATE2,
            Opcode.CALLDATACOPY,
            Opcode.CODECOPY,
            Opcode.EXTCODECOPY,
            Opcode.RETURNDATACOPY,
            Opcode.LOG0,
            Opcode.LOG1,
            Opcode.LOG2,
            Opcode.LOG3,
            Opcode.LOG4,
            Opcode.SHA3,
            Opcode.EXP,
            Opcode.MLOAD,
            Opcode.MSTORE,
            Opcode.MSTORE8,
            Opcode.RETURN,
            Opcode.REVERT,
        ),
    )
    is_create = is_create_flag + is_create2_flag
    is_dynamic_gas = (
        is_calldatacopy
        + is_codecopy
        + is_extcodecopy
        + is_returndatacopy
        + is_sha3
        + is_call
        + is_delegatecall
        + is_staticcall
        + is_create_flag
        + is_create2_flag
        + is_log0
        + is_log1
        + is_log2
        + is_log3
        + is_log4
        + is_mload
        + is_mstore
        + is_mstore8
        + is_return
        + is_revert
    )

    is_opcode_memory_size_overflow = (
        is_safe_mul_overflow
    ) = is_call_gas_cost_overflow = is_calldata_gas_overflow = is_initcode_gas_overflow = FQ(0)

    # IntrinsicGas
    # https://github.com/ethereum/go-ethereum/blob/b946b7a13b749c99979e312c83dce34cac8dd7b1/core/state_transition.go#L67
    calldata_length = instruction.call_context_lookup(CallContextFieldTag.CallDataLength)
    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)
    is_root = instruction.call_context_lookup(CallContextFieldTag.IsRoot)

    if is_root.expr() == FQ(1):
        data = [
            instruction.tx_calldata_lookup(tx_id, FQ(idx))
            for idx in range(0, calldata_length.expr().n)
        ]
        data_len = len(data)

        def transaction_data_gas_overflow() -> tuple[FQ, FQ]:
            # zero and non-zero bytes are priced differently
            nz = len([byte for byte in data if byte != 0])
            gas = TxGasContractCreation if is_create == FQ(1) else TxGas
            is_non_zero_calldata_gas_overflow, _ = instruction.compare(
                FQ(((MAX_U64 - gas) // TxDataNonZeroGasEIP2028)), FQ(nz), N_BYTES_U64
            )
            gas += nz * GAS_COST_TX_CALL_DATA_PER_NON_ZERO_BYTE

            # tx data zero gas overflow
            is_zero_calldata_gas_overflow = FQ(0)
            if is_non_zero_calldata_gas_overflow == FQ(0):
                z = data_len - nz
                is_zero_calldata_gas_overflow, _ = instruction.compare(
                    FQ(((MAX_U64 - gas) // GAS_COST_TX_CALL_DATA_PER_ZERO_BYTE)), FQ(z), N_BYTES_U64
                )
                gas += z * GAS_COST_TX_CALL_DATA_PER_ZERO_BYTE

            # EIP-3860, extra gas cost for init code
            is_initcode_gas_overflow = FQ(0)
            if is_create == FQ(1):
                len_words, _ = instruction.constant_divmod(data_len + FQ(31), FQ(32), N_BYTES_U64)
                is_initcode_gas_overflow, _ = instruction.compare(
                    FQ(((MAX_U64 - gas) // GAS_COST_INITCODE_WORD)), FQ(len_words), N_BYTES_U64
                )

            return (
                is_non_zero_calldata_gas_overflow + is_zero_calldata_gas_overflow,
                is_initcode_gas_overflow,
            )

        if data_len > 0:
            (
                is_calldata_gas_overflow,
                is_initcode_gas_overflow,
            ) = transaction_data_gas_overflow()

    # Run
    # https://github.com/ethereum/go-ethereum/blob/b946b7a13b749c99979e312c83dce34cac8dd7b1/core/vm/interpreter.go#L196
    def dynamic_gas_overflow() -> tuple[bool, bool]:
        (mem_size, is_opcode_memory_size_overflow) = instruction.memory_size(opcode)
        (_, is_safe_mul_overflow) = instruction.safe_mul(instruction.to_word_size(mem_size), 32)
        return (is_opcode_memory_size_overflow, is_safe_mul_overflow)

    if is_dynamic_gas:
        (is_opcode_memory_size_overflow, is_safe_mul_overflow) = dynamic_gas_overflow()

    # verify gas uint overflow.
    is_overflow = (
        is_opcode_memory_size_overflow
        + is_safe_mul_overflow
        + is_call_gas_cost_overflow
        + is_calldata_gas_overflow
        + is_initcode_gas_overflow
    )
    instruction.constrain_not_zero(FQ(is_overflow))

    instruction.constrain_error_state(instruction.rw_counter_offset)
