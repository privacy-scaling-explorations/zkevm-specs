from ..instruction import Instruction, Transition
from ...util.param import EXTRA_GAS_COST_ACCOUNT_COLD_ACCESS
from ...util import FQ
from ..table import AccountFieldTag, CallContextFieldTag, CopyDataTypeTag


def extcodecopy(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    address = instruction.word_to_address(instruction.stack_pop())
    memory_offset_word = instruction.stack_pop()
    code_offset_word = instruction.stack_pop()
    size_word = instruction.stack_pop()

    code_offset = instruction.word_to_u64(code_offset_word)
    memory_offset, size = instruction.memory_offset_and_length(memory_offset_word, size_word)

    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId).value()
    is_warm = instruction.add_account_to_access_list(tx_id, address, instruction.reversion_info())

    code_hash = instruction.account_read(address, AccountFieldTag.CodeHash)
    # Check account existence with code_hash != 0
    exists = FQ(1) - instruction.is_zero_word(code_hash)
    if exists == 1:
        code_size = instruction.bytecode_length(code_hash)
    else:
        code_size = FQ(0)

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
        memory_word_size=Transition.to(next_memory_size),
        dynamic_gas_cost=gas_cost,
    )
