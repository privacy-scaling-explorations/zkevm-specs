from zkevm_specs.evm_circuit.opcode import Opcode
from zkevm_specs.util.arithmetic import FQ
from zkevm_specs.util.param import (
    GAS_COST_COPY_SHA3,
    GAS_COST_CREATE,
    GAS_COST_CREATION_TX,
    GAS_COST_INITCODE_WORD,
    GAS_COST_TX_CALL_DATA_PER_NON_ZERO_BYTE,
    GAS_COST_TX_CALL_DATA_PER_ZERO_BYTE,
    MAX_INIT_CODE_SIZE,
    N_BYTES_GAS,
    N_BYTES_MEMORY_WORD_SIZE,
    N_BYTES_U64,
)
from ..instruction import Instruction
from ..table import RW, CallContextFieldTag


def error_oog_create(instruction: Instruction):
    # check opcode is CREATE or CREATE2
    opcode = instruction.opcode_lookup(True)
    is_create, is_create2 = instruction.pair_select(opcode, Opcode.CREATE, Opcode.CREATE2)

    # Constrain opcode must be CREATE or CREATE2.
    instruction.constrain_equal(is_create + is_create2, FQ(1))

    # First 3 stacks are `value`, `offset` and `size` but we don't need `value` here.
    offset_word = instruction.stack_lookup(RW.Read, 1)
    size_word = instruction.stack_lookup(RW.Read, 2)
    offset, size = instruction.memory_offset_and_length(offset_word, size_word)

    is_root = instruction.call_context_lookup(CallContextFieldTag.IsRoot)

    # gas cost calculation
    if is_root == FQ(1):
        tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)
        data = [instruction.tx_calldata_lookup(tx_id, FQ(idx)) for idx in range(0, size.n)]
        data_len = len(data)

        # gas cost, 16 gas per non-zero byte, 4 gas per zero byte
        gas_cost = GAS_COST_CREATION_TX
        nz = len([byte for byte in data if byte != 0])
        gas_cost += nz * GAS_COST_TX_CALL_DATA_PER_NON_ZERO_BYTE
        z = data_len - nz
        gas_cost += z * GAS_COST_TX_CALL_DATA_PER_ZERO_BYTE
    else:
        (_, memory_expansion_gas_cost) = instruction.memory_expansion(offset, size)
        gas_cost = GAS_COST_CREATE + memory_expansion_gas_cost

    # GAS_COST_INITCODE_WORD * word_size introduced in EIP-3860
    word_size, _ = instruction.constant_divmod(size + FQ(31), FQ(32), N_BYTES_MEMORY_WORD_SIZE)
    gas_cost += GAS_COST_INITCODE_WORD * word_size
    # gas cost for SHA3 calculation if it's a CREATE2 opcode
    if is_create2 == FQ(1):
        gas_cost += GAS_COST_COPY_SHA3 * word_size

    # ErrMaxInitCodeSizeExceeded
    is_exceed_max_initcode_size, _ = instruction.compare(FQ(MAX_INIT_CODE_SIZE), size, N_BYTES_U64)

    insufficient_gas, _ = instruction.compare(instruction.curr.gas_left, gas_cost, N_BYTES_GAS)

    instruction.constrain_not_zero(insufficient_gas + is_exceed_max_initcode_size)
    instruction.constrain_error_state(
        instruction.rw_counter_offset + instruction.curr.reversible_write_counter
    )
