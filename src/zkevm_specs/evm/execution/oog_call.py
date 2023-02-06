from zkevm_specs.evm.util.call_gadget import CallGadget
from ...util import FQ
from ..instruction import Instruction
from ..table import CallContextFieldTag
from ...util import N_BYTES_GAS
from ..opcode import Opcode


def oog_call(instruction: Instruction):
    # retrieve op code associated to oog call error
    opcode = instruction.opcode_lookup(True)
    # TODO: add CallCode etc.when handle ErrorOutOfGasCALLCODE in future implementation
    instruction.constrain_equal(opcode, Opcode.CALL)

    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)

    # init CallGadget to handle stack vars.
    call = CallGadget(instruction, FQ(0), FQ(1), FQ(0), FQ(0))

    # TODO: handle PrecompiledContract oog cases

    # Add callee to access list
    is_warm_access = instruction.read_account_to_access_list(tx_id, call.callee_address)

    # verify gas cost
    gas_cost = call.gas_cost(instruction, is_warm_access)

    # verify gas is insufficient
    gas_not_enough, _ = instruction.compare(instruction.curr.gas_left, gas_cost, N_BYTES_GAS)
    instruction.constrain_equal(gas_not_enough, FQ(1))

    instruction.constrain_error_state(12 + instruction.curr.reversible_write_counter.n)
