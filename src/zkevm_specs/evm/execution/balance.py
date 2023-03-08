from ...util import EXTRA_GAS_COST_ACCOUNT_COLD_ACCESS, FQ, N_BYTES_ACCOUNT_ADDRESS, RLC, Word
from ..instruction import Instruction, Transition
from ..opcode import Opcode
from ..table import AccountFieldTag, CallContextFieldTag


def balance(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.BALANCE)

    address = instruction.word_to_address(instruction.stack_pop())

    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId).value()
    is_warm = instruction.add_account_to_access_list(tx_id, address, instruction.reversion_info())

    # Check account existence with code_hash != 0
    exists = FQ(1) - instruction.is_zero_word(
        instruction.account_read(address, AccountFieldTag.CodeHash)
    )

    balance = instruction.account_read(address, AccountFieldTag.Balance) if exists == 1 else Word(0)

    instruction.constrain_equal_word(
        instruction.select(exists, balance, Word(0)),
        instruction.stack_push(),
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(7 + exists.n),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.same(),
        dynamic_gas_cost=instruction.select(is_warm, FQ(0), FQ(EXTRA_GAS_COST_ACCOUNT_COLD_ACCESS)),
    )
