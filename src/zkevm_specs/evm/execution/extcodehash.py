from ..instruction import Instruction, Transition
from ..table import CallContextFieldTag, AccountFieldTag
from ...util.param import EXTRA_GAS_COST_ACCOUNT_COLD_ACCESS
from ...util.hash import EMPTY_CODE_HASH
from ...util import FQ


def extcodehash(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    address = instruction.rlc_to_fq(instruction.stack_pop(), 20)

    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)
    is_warm = instruction.add_account_to_access_list(tx_id, address, instruction.reversion_info())

    nonce = instruction.account_read(address, AccountFieldTag.Nonce)
    balance = instruction.account_read(address, AccountFieldTag.Balance)
    code_hash = instruction.account_read(address, AccountFieldTag.CodeHash)

    is_empty = (
        instruction.is_zero(nonce)
        * instruction.is_zero(balance)
        * instruction.is_equal(code_hash, instruction.rlc_encode(EMPTY_CODE_HASH, 32))
    )

    instruction.constrain_equal(
        instruction.select(is_empty, FQ(0), code_hash.expr()),
        instruction.stack_push(),
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(9),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(0),
        dynamic_gas_cost=instruction.select(is_warm, FQ(0), FQ(EXTRA_GAS_COST_ACCOUNT_COLD_ACCESS)),
    )
