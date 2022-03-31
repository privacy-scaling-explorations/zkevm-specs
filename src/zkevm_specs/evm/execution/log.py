from ..instruction import Instruction, Transition
from ..table import CallContextFieldTag, TxLogFieldTag, TxContextFieldTag
from ..opcode import Opcode
from ..execution_state import ExecutionState
from ...util.param import GAS_COST_LOG
from ...util import FQ, cast_expr


def log(instruction: Instruction):
    opcode = instruction.opcode_lookup(True)
    # constrain op in [log0, log4] range
    instruction.range_lookup(opcode - Opcode.LOG0, 5)

    # pop `mstart`, `msize` from stack
    mstart = instruction.rlc_to_fq(instruction.stack_pop(), 8)
    msize = instruction.rlc_to_fq(instruction.stack_pop(), 8)

    # read tx id
    tx_id = instruction.call_context_lookup(CallContextFieldTag.TxId)
    # check not static call
    instruction.constrain_equal(
        FQ(0), instruction.call_context_lookup(CallContextFieldTag.IsStatic)
    )

    # check contract_address in CallContext & TxLog
    # use call context's  callee address as contract address

    contract_address = instruction.call_context_lookup(CallContextFieldTag.CalleeAddress)
    is_persistent = instruction.call_context_lookup(CallContextFieldTag.IsPersistent)
    if instruction.is_zero(is_persistent) == 0:
        instruction.constrain_equal(
            contract_address,
            instruction.tx_log_lookup(tx_id=tx_id, field_tag=TxLogFieldTag.Address),
        )

    # constrain topics in stack & logs
    is_topic_zeros = [1] * 4
    topic_count = int(opcode) - Opcode.LOG0
    for i in range(4):
        if i < topic_count:
            is_topic_zeros[i] = 0
            topic = instruction.stack_pop()
            if instruction.is_zero(is_persistent) == 0:
                instruction.constrain_equal(
                    topic.expr(),
                    instruction.tx_log_lookup(
                        tx_id=tx_id, field_tag=TxLogFieldTag.Topic, index=i
                    ).expr(),
                )

    # TOPIC_COUNT == Non zero topic count
    assert sum(is_topic_zeros) == 4 - topic_count
    # `is_topic_zeros` order must be from 0 --> 1
    for i in range(1, 4):
        diff = is_topic_zeros[i] - is_topic_zeros[i - 1]
        instruction.constrain_bool(FQ(diff))

    # check memory copy, should do in next step here
    # When length != 0, constrain the state in the next execution state CopyToLog
    if not instruction.is_zero(msize):
        assert instruction.next is not None
        instruction.constrain_equal(instruction.next.execution_state, ExecutionState.CopyToLog)
        next_aux = instruction.next.aux_data
        instruction.constrain_equal(next_aux.src_addr, mstart)
        instruction.constrain_equal(next_aux.src_addr_end, mstart + msize)
        instruction.constrain_equal(next_aux.bytes_left, msize)
        instruction.constrain_equal(next_aux.is_persistent, is_persistent)
        instruction.constrain_equal(next_aux.tx_id, tx_id)

    # omit block number constraint even it is set within op code explicitly, because by default the circuit only handle
    # current block, otherwise, block context lookup is required.
    # calculate dynamic gas cost
    next_memory_size, memory_expansion_gas = instruction.memory_expansion_dynamic_length(
        mstart, msize
    )
    dynamic_gas = GAS_COST_LOG * (opcode - Opcode.LOG0) + 8 * msize + memory_expansion_gas

    assert isinstance(is_persistent, FQ)
    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(instruction.rw_counter_offset),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(2 + opcode - Opcode.LOG0),
        state_write_counter=Transition.delta(1),
        dynamic_gas_cost=dynamic_gas,
        memory_size=Transition.to(next_memory_size),
        log_id=Transition.delta(is_persistent),
    )
