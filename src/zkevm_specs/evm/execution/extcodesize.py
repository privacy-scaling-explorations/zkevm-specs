from ...util import (
    EXTRA_GAS_COST_ACCOUNT_COLD_ACCESS,
    FQ,
    N_BYTES_ACCOUNT_ADDRESS,
    N_BYTES_U64,
    RLC,
)
from ..instruction import Instruction, Transition
from ..opcode import Opcode
from ..table import AccountFieldTag, CallContextFieldTag


def extcodesize(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.EXTCODESIZE)

    address = instruction.rlc_to_fq(instruction.stack_pop(), N_BYTES_ACCOUNT_ADDRESS)

    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)
    is_warm = instruction.add_account_to_access_list(tx_id, address, instruction.reversion_info())

    # Load account `exists` value from auxilary witness data.
    exists = instruction.curr.aux_data

    if exists == 1:
        code_hash = instruction.account_read(address, AccountFieldTag.CodeHash)
        code_size = instruction.bytecode_length(code_hash)
    else:  # exists == 0
        instruction.account_read(address, AccountFieldTag.NonExisting)
        code_size = RLC(0)

    instruction.constrain_equal(
        instruction.select(exists, code_size, FQ(0)),
        instruction.rlc_to_fq(instruction.stack_push(), N_BYTES_U64),
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(7),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.same(),
        dynamic_gas_cost=instruction.select(is_warm, FQ(0), FQ(EXTRA_GAS_COST_ACCOUNT_COLD_ACCESS)),
    )
