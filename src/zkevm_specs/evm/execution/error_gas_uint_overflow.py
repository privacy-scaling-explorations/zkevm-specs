from zkevm_specs.evm.util.call_gadget import CallGadget
from ...util import (
    FQ,
    TxDataNonZeroGasEIP2028,
    MAX_U64,
    N_BYTES_U64,
    TxGas,
    TxGasContractCreation,
    TxDataZeroGas,
    # InitCodeWordGas,
)
from ..instruction import Instruction, Transition
from ..table import CallContextFieldTag
from ..opcode import Opcode


def error_gas_uint_overflow(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)

    is_call = instruction.is_equal(opcode, Opcode.CALL)
    is_create_flag = instruction.is_equal(opcode, Opcode.CREATE)
    is_create2_flag = instruction.is_equal(opcode, Opcode.CREATE2)
    is_create = is_create_flag + is_create2_flag

    # init overflow flag
    is_memory_size_overflow = (
        is_call_gas_cost_overflow
    ) = is_eip2028_overflow = is_non_zero_gas_overflow = is_eip3860_overflow = FQ(0)

    # memory size overflow flag.
    memory_size = instruction.call_context_lookup(CallContextFieldTag.MemorySize)
    is_memory_size_overflow = instruction.is_memory_overflow(memory_size)

    # call gas_cost overflow flag.
    # seems never overflow because of checking range inside of CallGadget
    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)
    call = CallGadget(instruction, FQ(0), FQ(1), FQ(0), FQ(0))
    is_warm_access = instruction.read_account_to_access_list(tx_id, call.callee_address)
    gas_cost = call.gas_cost(instruction, is_warm_access)
    is_call_gas_cost_overflow = is_call * instruction.is_u64_overflow(gas_cost)

    # intrinsic gas flag.
    calldata_offset = instruction.call_context_lookup(CallContextFieldTag.CallDataOffset)
    calldata_length = instruction.call_context_lookup(CallContextFieldTag.CallDataLength)
    data = [
        instruction.tx_calldata_lookup(tx_id, calldata_offset + FQ(idx))
        for idx in range(calldata_length.expr().n)
    ]
    dataLen = len(data)

    def non_zero_gas_constraints():
        # eip 2028
        nz = len([byte for byte in data if byte != 0])
        gas = TxGasContractCreation if is_create == FQ(1) else TxGas
        non_zero_gas = TxDataNonZeroGasEIP2028
        is_eip2028_overflow, _ = instruction.compare(
            FQ(((MAX_U64 - gas) // non_zero_gas)), FQ(nz), N_BYTES_U64
        )
        gas += nz * non_zero_gas

        # tx data zero gas overflow
        z = dataLen - nz
        zero_gas = TxDataZeroGas
        is_non_zero_gas_overflow, _ = instruction.compare(
            FQ(((MAX_U64 - gas) // zero_gas)), FQ(z), N_BYTES_U64
        )
        gas += z * zero_gas

        # eip 3860
        # if is_create:
        #     lenWords = dataLen // 32
        #     is_eip3860_overflow, _ = instruction.compare(
        #         FQ((MAX_U64 - gas) // InitCodeWordGas), FQ(lenWords), N_BYTES_U64
        #     )

    instruction.condition(FQ(dataLen > 0), non_zero_gas_constraints)

    # verify gas uint overflow.
    is_overflow = (
        is_memory_size_overflow
        + is_call_gas_cost_overflow
        + is_eip2028_overflow
        + is_non_zero_gas_overflow
        + is_eip3860_overflow
    )
    instruction.constrain_not_zero(FQ(is_overflow))

    # verify call failure.
    instruction.constrain_equal(
        instruction.call_context_lookup(CallContextFieldTag.IsSuccess), FQ(0)
    )

    # state transition.
    if instruction.curr.is_root:
        # Do step state transition
        instruction.constrain_step_state_transition(
            rw_counter=Transition.delta(12),
            call_id=Transition.same(),
        )
    else:
        # when it is internal call, need to restore caller's state as finishing this call.
        # Restore caller state to next StepState
        instruction.step_state_transition_to_restored_context(
            rw_counter_delta=12,
            return_data_offset=FQ(0),
            return_data_length=FQ(0),
            gas_left=instruction.curr.gas_left,
        )
