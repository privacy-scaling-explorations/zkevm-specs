from ..instruction import Instruction, Transition
from ..table import CallContextFieldTag, TxLogFieldTag, TxContextFieldTag
from ..opcode import Opcode
from ..execution_state import ExecutionState
from ...util.param import LOG_STATIC_GAS


def log(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    # constrain op in [log0, log4] range
    instruction.range_lookup(opcode - Opcode.LOG0, 5)

    # pop `mstart`, `msize` from stack
    mstart = instruction.rlc_to_fq_exact(instruction.stack_pop(), 8)
    msize = instruction.rlc_to_fq_exact(instruction.stack_pop(), 8)

    # check contract_address in CallContext & TxLog
    # use call context's  callee address as contract address
    contract_address = instruction.call_context_lookup(CallContextFieldTag.CalleeAddress)
    instruction.constrain_equal(contract_address, instruction.tx_log_lookup(TxLogFieldTag.Address))
    # check not static call
    instruction.constrain_equal(0, instruction.call_context_lookup(CallContextFieldTag.IsStatic))

    # constrain topics in stack & logs
    for i in range(int(opcode) - Opcode.LOG0):
        topic = instruction.stack_pop()
        instruction.constrain_equal(topic, instruction.tx_log_lookup(TxLogFieldTag.Topics, i))

    # check memory copy, should do in next step here
    # When length != 0, constrain the state in the next execution state CopyToLog
    if not instruction.is_zero(msize):
        instruction.constrain_equal(instruction.next.execution_state, ExecutionState.CopyToLog)
        next_aux = instruction.next.aux_data
        instruction.constrain_equal(next_aux.src_addr, mstart)
        instruction.constrain_equal(next_aux.src_addr_end, mstart + msize)
        instruction.constrain_equal(next_aux.bytes_left, msize)

    # omit block number constraint even it is set within op code explicitly, because by default the circuit only handle
    # current block, otherwise, block context lookup is required.
    # calculate dynamic gas cost
    next_memory_size, memory_expansion_gas = instruction.memory_expansion_dynamic_length(
        mstart, msize
    )
    dynamic_gas = LOG_STATIC_GAS * (opcode - Opcode.LOG0) + 8 * msize + memory_expansion_gas

    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(instruction.rw_counter_offset),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(2 + opcode - Opcode.LOG0),
        state_write_counter=Transition.delta(1),
        dynamic_gas_cost=dynamic_gas,
        memory_size=Transition.to(next_memory_size),
        log_index=Transition.delta(1),
    )
