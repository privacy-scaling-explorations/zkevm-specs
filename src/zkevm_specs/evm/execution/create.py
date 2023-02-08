from ...util import (
    CALL_CREATE_DEPTH,
)
from ..instruction import Instruction
from ..table import CallContextFieldTag, AccountFieldTag


def create(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.responsible_opcode_lookup(opcode)

    value = instruction.stack_pop()
    offset = instruction.stack_pop()
    size = instruction.stack_pop()
    input = instruction.stack_pop()
    gas = instruction.stack_push()

    depth = instruction.call_context_lookup(CallContextFieldTag.Depth)
    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)
    tx_caller_address = instruction.call_context_lookup(CallContextFieldTag.CallerAddress)
    nonce, nonce_prev = instruction.account_write(tx_caller_address, AccountFieldTag.Nonce)
    contract_address = instruction.generate_contract_address(tx_caller_address, nonce_prev)

    # ErrDepth constraint
    instruction.range_lookup(depth, CALL_CREATE_DEPTH)

    # ErrNonceUintOverflow constraint
    (is_not_overflow, _) = instruction.compare(nonce, nonce_prev, 8)
    instruction.is_zero(is_not_overflow)

    # add contract address to access list
    instruction.add_account_to_access_list(tx_id, contract_address)

    # ErrContractAddressCollision constraint
    code_hash = instruction.account_read(contract_address, AccountFieldTag.CodeHash)
    instruction.is_zero(code_hash)

    # init contract state
    nonce, nonce_prev = instruction.account_write(contract_address, AccountFieldTag.Nonce)

    # transfer value from caller to contract address
    instruction.transfer(tx_caller_address, contract_address, value)
