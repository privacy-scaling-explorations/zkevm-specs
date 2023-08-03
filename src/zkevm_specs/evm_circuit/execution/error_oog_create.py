from zkevm_specs.evm_circuit.opcode import Opcode
from zkevm_specs.util.arithmetic import FQ, Word, WordOrValue
from zkevm_specs.util.hash import EMPTY_CODE_HASH
from zkevm_specs.util.param import (
    GAS_COST_COPY_SHA3,
    GAS_COST_CREATE,
    GAS_COST_CREATION_TX,
    GAS_COST_INITCODE_WORD,
    MAX_U64,
    N_BYTES_ACCOUNT_ADDRESS,
    N_BYTES_GAS,
    N_BYTES_MEMORY_ADDRESS,
    N_BYTES_MEMORY_WORD_SIZE,
    N_BYTES_STACK,
    N_BYTES_U64,
)
from ..instruction import Instruction, Transition
from ..table import RW, CallContextFieldTag, AccountFieldTag, CopyDataTypeTag, TxContextFieldTag


# if root:
#     gas_cost = TxGasContractCreation + tx_calldata_gas_cost (covered in uint64 overflow)
# else:
#     gas cost = GAS_COST_CREATE + memory expansion (moved from dynamic_mm_exp)
# if create2:
#     gas_cost += GAS_COST_COPY_SHA3 * memory_size
# gas_cost += initcode_cost(init_code) (covered in uint64 overflow if root)

# MAX_INITCODE_SIZE (moved to CREATE.py)


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

    (_, memory_expansion_gas_cost) = instruction.memory_expansion(offset, size)
    word_size, _ = instruction.constant_divmod(size + FQ(31), FQ(32), N_BYTES_MEMORY_WORD_SIZE)

    # gas cost
    # GAS_COST_INITCODE_WORD * word_size introduced in EIP-3860
    gas_cost = GAS_COST_CREATE + memory_expansion_gas_cost + GAS_COST_INITCODE_WORD * word_size

    # gas cost for SHA3 calculation if it's a CREATE2 opcode
    if is_create2 == FQ(1):
        gas_cost += GAS_COST_COPY_SHA3 * word_size

    instruction.constrain_error_state(
        instruction.rw_counter_offset + instruction.curr.reversible_write_counter
    )
