from zkevm_specs.util.param import N_BYTES_MEMORY_ADDRESS
from ...util import FQ
from ..instruction import Instruction
from ..opcode import Opcode
from ...util import N_BYTES_GAS


def error_oog_static_memory_expansion(instruction: Instruction):
    # retrieve op code associated to oog constant error
    opcode = instruction.opcode_lookup(True)
    is_mload, is_mstore, is_mstore8 = instruction.multiple_select(
        opcode, (Opcode.MLOAD, Opcode.MSTORE, Opcode.MSTORE8)
    )

    # Constrain opcode must be one of MLOAD, MSTORE or MSTORE8.
    instruction.constrain_equal(is_mload + is_mstore + is_mstore8, FQ(1))

    # pop `offset`
    offset = instruction.word_to_fq(instruction.stack_pop(), N_BYTES_MEMORY_ADDRESS)

    # get total gas cost
    constant_gas = FQ(3)
    size = 1 if is_mstore8 else 32
    _, memory_expansion_gas = instruction.memory_expansion_dynamic_length(offset, FQ(size))
    gas_cost = constant_gas + memory_expansion_gas

    # check gas left is less than total gas required
    insufficient_gas, _ = instruction.compare(instruction.curr.gas_left, gas_cost, N_BYTES_GAS)
    instruction.constrain_equal(insufficient_gas, FQ(1))

    instruction.constrain_error_state(
        instruction.rw_counter_offset + instruction.curr.reversible_write_counter + 1
    )
