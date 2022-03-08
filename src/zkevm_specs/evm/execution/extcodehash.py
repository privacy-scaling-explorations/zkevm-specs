from ..instruction import Instruction, Transition
from ..table import CallContextFieldTag, AccountFieldTag
from ..opcode import Opcode
from ...util.param import N_BYTES_MEMORY_ADDRESS
from ...util import keccak256


def extcodehash(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    address = instruction.stack_pop()

    call_id = instruction.call_context_lookup(CallContextFieldTag.TxId)
    is_warm = instruction.add_account_to_access_list(call_id, address)

    nonce = instruction.account_read(address, AccountFieldTag.Nonce)
    balance = instruction.account_read(address, AccountFieldTag.Balance)
    code_hash = instruction.account_read(address, AccountFieldTag.CodeHash)

    is_empty = nonce == 0 and balance == 0 and code_hash == int.from_bytes(keccak256(""), "big")

    instruction.constrain_equal(
        0 if is_empty else code_hash,
        instruction.stack_push(),
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(7),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(0),
        dynamic_gas_cost=0 if is_warm else COLD_ACCOUNT_ACCESS_COST - WARM_STORAGE_READ_COST,
    )
