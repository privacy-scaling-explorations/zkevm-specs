from zkevm_specs.evm_circuit.table import RW
from zkevm_specs.util.param import (
    INVALID_FIRST_BYTE_CONTRACT_CODE,
    N_BYTES_MEMORY_ADDRESS,
)
from ...util import FQ
from ..instruction import Instruction
from ..opcode import Opcode


def error_invalid_creation_code(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    # opcode must be `RETURN`
    instruction.constrain_equal(opcode, Opcode.RETURN)

    # the call must be coming from CREATE or CREATE2
    instruction.constrain_equal(FQ(instruction.curr.is_create), FQ(1))

    # pop offset from stack only
    return_offset = instruction.word_to_fq(instruction.stack_pop(), N_BYTES_MEMORY_ADDRESS)

    # lookup the first byte of deployed bytecode from memory
    first_byte = instruction.memory_lookup(RW.Read, return_offset)

    # verify if the first byte is `0xEF`, which is introduced in EIP-3541
    instruction.constrain_equal(first_byte, FQ(INVALID_FIRST_BYTE_CONTRACT_CODE))

    instruction.constrain_error_state(
        instruction.rw_counter_offset + instruction.curr.reversible_write_counter
    )
