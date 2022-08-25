from ..instruction import Instruction, Transition
from ...util.param import EXTRA_GAS_COST_ACCOUNT_COLD_ACCESS
from ...util import N_BYTES_MEMORY_ADDRESS, N_BYTES_ACCOUNT_ADDRESS, FQ
from ..table import AccountFieldTag, CallContextFieldTag, CopyDataTypeTag


def extcodecopy(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    address, memory_offset_word, code_offset, size_word = (
        instruction.rlc_to_fq(instruction.stack_pop(), N_BYTES_ACCOUNT_ADDRESS),
        instruction.stack_pop(),
        instruction.rlc_to_fq(instruction.stack_pop(), N_BYTES_MEMORY_ADDRESS),
        instruction.stack_pop(),
    )

    memory_offset, size = instruction.memory_offset_and_length(memory_offset_word, size_word)

    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)
    is_warm = instruction.add_account_to_access_list(tx_id, address, instruction.reversion_info())

    code_hash = instruction.account_read(address, AccountFieldTag.CodeHash)
    code_size = instruction.bytecode_length(code_hash)

    next_memory_size, memory_expansion_gas_cost = instruction.memory_expansion_dynamic_length(
        memory_offset, size
    )
    memory_copier_gas_cost = instruction.memory_copier_gas_cost(size, memory_expansion_gas_cost)

    gas_cost = memory_copier_gas_cost + instruction.select(
        is_warm, FQ(0), FQ(EXTRA_GAS_COST_ACCOUNT_COLD_ACCESS)
    )

    if instruction.is_zero(size) == FQ(0):
        copy_rwc_inc, _ = instruction.copy_lookup(
            code_hash,
            CopyDataTypeTag.Bytecode,
            instruction.curr.call_id,
            CopyDataTypeTag.Memory,
            code_offset,
            code_size,
            memory_offset,
            size,
            instruction.curr.rw_counter + instruction.rw_counter_offset,
        )
    else:
        copy_rwc_inc = FQ(0)

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(instruction.rw_counter_offset + copy_rwc_inc),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(4),
        memory_size=Transition.to(next_memory_size),
        dynamic_gas_cost=gas_cost,
    )
