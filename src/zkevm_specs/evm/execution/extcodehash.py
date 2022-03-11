from ..instruction import Instruction, Transition
from ..table import CallContextFieldTag, AccountFieldTag
from ..opcode import Opcode
from ...util.param import EXTRA_GAS_COST_ACCOUNT_COLD_ACCESS, GAS_COST_WARM_ACCESS
from ...util import keccak256
from ...util.hash import EMPTY_CODE_HASH


def extcodehash(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    address = instruction.stack_pop()

    call_id = instruction.call_context_lookup(CallContextFieldTag.TxId)
    is_cold = instruction.add_account_to_access_list(call_id, address)

    nonce = instruction.account_read(address, AccountFieldTag.Nonce)
    balance = instruction.account_read(address, AccountFieldTag.Balance)
    code_hash = instruction.account_read(address, AccountFieldTag.CodeHash)

    is_empty = (
        instruction.is_zero(nonce)
        * instruction.is_zero(balance)
        * instruction.is_zero(code_hash - EMPTY_CODE_HASH)
    )

    instruction.constrain_equal(
        instruction.select(not instruction.is_zero(is_empty), 0, code_hash),
        instruction.stack_push(),
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(7),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(0),
        dynamic_gas_cost=is_cold * EXTRA_GAS_COST_ACCOUNT_COLD_ACCESS,
    )
