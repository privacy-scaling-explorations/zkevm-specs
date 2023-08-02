from zkevm_specs.evm_circuit.table import CallContextFieldTag
from zkevm_specs.util.param import (
    GAS_COST_ACCOUNT_COLD_ACCESS,
    GAS_COST_WARM_ACCESS,
    N_BYTES_ACCOUNT_ADDRESS,
)
from ...util import FQ
from ..instruction import Instruction
from ..opcode import Opcode
from ...util import N_BYTES_GAS


def error_oog_account_access(instruction: Instruction):
    # retrieve op code associated to oog constant error
    opcode = instruction.opcode_lookup(True)
    (
        is_balance,
        is_ext_code_size,
        is_ext_code_hash,
    ) = instruction.multiple_select(
        opcode, (Opcode.BALANCE, Opcode.EXTCODESIZE, Opcode.EXTCODEHASH)
    )

    # Constrain opcode must be one of `BALANCE`, `EXTCODESIZE` and `EXTCODEHASH`.
    instruction.constrain_equal(is_balance + is_ext_code_size + is_ext_code_hash, FQ(1))

    # pop `address`
    address = instruction.word_to_fq(instruction.stack_pop(), N_BYTES_ACCOUNT_ADDRESS)

    # calculate gas_cost
    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)
    is_warm = instruction.read_account_to_access_list(tx_id, address)
    gas_cost = GAS_COST_WARM_ACCESS if is_warm == FQ(1) else GAS_COST_ACCOUNT_COLD_ACCESS

    # check gas left is less than total gas required
    insufficient_gas, _ = instruction.compare(instruction.curr.gas_left, FQ(gas_cost), N_BYTES_GAS)
    instruction.constrain_equal(insufficient_gas, FQ(1))

    instruction.constrain_error_state(
        instruction.rw_counter_offset + instruction.curr.reversible_write_counter
    )
