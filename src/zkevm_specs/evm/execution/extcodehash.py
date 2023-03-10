from ...util import EXTRA_GAS_COST_ACCOUNT_COLD_ACCESS, FQ
from ..instruction import Instruction, Transition
from ..opcode import Opcode
from ..table import AccountFieldTag, CallContextFieldTag


def extcodehash(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.EXTCODEHASH)

    address = instruction.word_to_address(instruction.stack_pop())

    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId).value()
    is_warm = instruction.add_account_to_access_list(tx_id, address, instruction.reversion_info())

    # We already define code_hash to be 0 when the account doesn't exist.
    code_hash = instruction.account_read(address, AccountFieldTag.CodeHash)

    instruction.constrain_equal_word(
        code_hash,
        instruction.stack_push(),
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(7),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.same(),
        dynamic_gas_cost=instruction.select(is_warm, FQ(0), FQ(EXTRA_GAS_COST_ACCOUNT_COLD_ACCESS)),
    )
