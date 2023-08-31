from zkevm_specs.evm_circuit.util.call_gadget import CallGadget
from ...util import FQ
from ..instruction import Instruction
from ..table import CallContextFieldTag
from ...util import N_BYTES_GAS
from ..opcode import Opcode


# Handle the corresponding out of gas errors for CALL, CALLCODE, DELEGATECALL
# and STATICCALL opcodes.
def error_oog_call(instruction: Instruction):
    # retrieve op code associated to oog call error
    opcode = instruction.opcode_lookup(True)
    is_call, is_callcode, is_delegatecall, is_staticcall = instruction.multiple_select(
        opcode, (Opcode.CALL, Opcode.CALLCODE, Opcode.DELEGATECALL, Opcode.STATICCALL)
    )

    # Constrain opcode must be CALL, CALLCODE, DELEGATECALL or STATICCALL.
    instruction.constrain_equal(is_call + is_callcode + is_delegatecall + is_staticcall, FQ(1))

    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)

    # init CallGadget to handle stack vars.
    call = CallGadget(instruction, FQ(0), is_call, is_callcode, is_delegatecall, is_staticcall)

    # TODO: handle PrecompiledContract oog cases

    # Add callee to access list
    is_warm_access = instruction.read_account_to_access_list(tx_id, call.callee_address)

    # verify gas cost
    gas_cost = call.gas_cost(instruction, is_warm_access)

    # verify gas is insufficient
    gas_not_enough, _ = instruction.compare(instruction.curr.gas_left, gas_cost, N_BYTES_GAS)
    instruction.constrain_equal(gas_not_enough, FQ(1))

    # Both CALL and CALLCODE opcodes have an extra stack pop `value` relative to
    # DELEGATECALL and STATICCALL.
    instruction.constrain_error_state(
        instruction.rw_counter_offset + instruction.curr.reversible_write_counter
    )
