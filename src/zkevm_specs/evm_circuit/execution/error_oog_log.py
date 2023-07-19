from zkevm_specs.util.param import GAS_COST_LOG, GAS_COST_LOGDATA, N_BYTES_MEMORY_ADDRESS
from ...util import FQ
from ..instruction import Instruction
from ..opcode import Opcode
from ...util import N_BYTES_GAS


def error_oog_log(instruction: Instruction):
    # retrieve op code associated to oog constant error
    opcode = instruction.opcode_lookup(True)
    # constrain op in [log0, log4] range
    instruction.range_lookup(opcode - Opcode.LOG0, 5)

    # pop `mstart`, `msize` from stack
    mstart = instruction.word_to_fq(instruction.stack_pop(), N_BYTES_MEMORY_ADDRESS)
    msize = instruction.word_to_fq(instruction.stack_pop(), N_BYTES_MEMORY_ADDRESS)

    # get total gas cost
    _, memory_expansion_gas = instruction.memory_expansion_dynamic_length(mstart, msize)
    gas_cost = (
        GAS_COST_LOG
        + GAS_COST_LOG * (opcode - Opcode.LOG0)
        + GAS_COST_LOGDATA * msize
        + memory_expansion_gas
    )

    # check gas left is less than total gas required
    gas_not_enough, _ = instruction.compare(instruction.curr.gas_left, gas_cost, N_BYTES_GAS)
    instruction.constrain_equal(gas_not_enough, FQ(1))

    instruction.constrain_error_state(instruction.rw_counter_offset + 1)
