from zkevm_specs.evm_circuit.table import CallContextFieldTag, RW
from zkevm_specs.util.param import N_BYTES_MEMORY_ADDRESS
from ..instruction import Instruction
from ..opcode import Opcode


def error_return_data_out_of_bound(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.RETURNDATACOPY)

    # skip first stack value, `memOffset`
    data_offset = instruction.word_to_fq(instruction.stack_lookup(1), N_BYTES_MEMORY_ADDRESS)
    length = instruction.word_to_fq(instruction.stack_lookup(2), N_BYTES_MEMORY_ADDRESS)

    # get the length of last callee's return data
    return_data_length = instruction.call_context_lookup(
        CallContextFieldTag.LastCalleeReturnDataLength, RW.Read
    )

    # verify if this call meets any one of error conditions
    end = data_offset + length
    is_data_offset_u64_overflow = instruction.is_u64_overflow(data_offset)
    is_end_u64_overflow = instruction.is_u64_overflow(end)
    is_end_over_return_data_len, _ = instruction.compare(return_data_length, end)

    instruction.constrain_not_zero(
        is_data_offset_u64_overflow + is_end_u64_overflow + is_end_over_return_data_len
    )

    instruction.constrain_error_state(
        instruction.rw_counter_offset + instruction.curr.reversible_write_counter
    )
