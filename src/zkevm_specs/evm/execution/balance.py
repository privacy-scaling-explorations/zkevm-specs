from ...util import EXTRA_GAS_COST_ACCOUNT_COLD_ACCESS, FQ, N_BYTES_ACCOUNT_ADDRESS, RLC
from ..instruction import Instruction, Transition
from ..opcode import Opcode
from ..table import AccountFieldTag, CallContextFieldTag


def balance(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    instruction.constrain_equal(opcode, Opcode.BALANCE)

    address = instruction.rlc_to_fq(instruction.stack_pop(), N_BYTES_ACCOUNT_ADDRESS)

    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)
    is_warm = instruction.add_account_to_access_list(tx_id, address, instruction.reversion_info())

    # Check account existence with code_hash != 0
    exists = FQ(1) - instruction.is_zero(
        instruction.account_read(address, AccountFieldTag.CodeHash)
    )

    balance = instruction.account_read(address, AccountFieldTag.Balance) if exists == 1 else RLC(0)

    instruction.constrain_equal(
        instruction.select(exists, balance.expr(), FQ(0)),
        instruction.stack_push(),
    )

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(7 + exists.n),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.same(),
        dynamic_gas_cost=instruction.select(is_warm, FQ(0), FQ(EXTRA_GAS_COST_ACCOUNT_COLD_ACCESS)),
    )
