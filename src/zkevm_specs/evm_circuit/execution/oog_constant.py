from ...util import FQ
from ..instruction import Instruction, FixedTableTag
from ..opcode import Opcode
from ...util import N_BYTES_GAS


def oog_constant(instruction: Instruction):
    # retrieve op code associated to oog constant error
    opcode = instruction.opcode_lookup(True)
    const_gas_entry = instruction.fixed_lookup(
        FixedTableTag.OpcodeConstantGas, opcode, FQ(Opcode(opcode.expr().n).constant_gas_cost())
    )

    # check gas left is less than const gas required
    gas_not_enough, _ = instruction.compare(
        instruction.curr.gas_left, const_gas_entry.value1, N_BYTES_GAS
    )
    instruction.constrain_equal(gas_not_enough, FQ(1))

    instruction.constrain_error_state(1 + instruction.curr.reversible_write_counter.n)
