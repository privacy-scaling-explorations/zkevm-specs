from ..instruction import Instruction, Transition
from ..table import CallContextFieldTag, TxLogFieldTag, TxContextFieldTag, CopyDataTypeTag
from ..opcode import Opcode
from ..execution_state import ExecutionState
from ...util.param import GAS_COST_LOG, GAS_COST_LOGDATA
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
            instruction.tx_log_lookup(
                tx_id=tx_id, log_id=instruction.curr.log_id + 1, field_tag=TxLogFieldTag.Address
            ),
        )

    # constrain topics in stack & logs
    topic_selectors = [0] * 4
    topic_count = int(opcode) - Opcode.LOG0
    for i in range(4):
        if i < topic_count:
            topic_selectors[i] = 1
            topic = instruction.stack_pop()
            if instruction.is_zero(is_persistent) == 0:
                instruction.constrain_equal(
                    topic.expr(),
                    instruction.tx_log_lookup(
                        tx_id=tx_id,
                        log_id=instruction.curr.log_id + 1,
                        field_tag=TxLogFieldTag.Topic,
                        index=i,
                    ).expr(),
                )

    # TOPIC_COUNT == Non zero topic selector count
    assert sum(topic_selectors) == topic_count
    # `topic_selectors` order must be from 1 --> 0
    for i in range(0, 4):
        instruction.constrain_bool(FQ(topic_selectors[i]))
        if i > 0:
            diff = topic_selectors[i - 1] - topic_selectors[i]
            instruction.constrain_bool(FQ(diff))

    if instruction.is_zero(msize) == 0 and is_persistent == 1:
        copy_rwc_inc, _ = instruction.copy_lookup(
            instruction.curr.call_id,
            CopyDataTypeTag.Memory,
            tx_id,
            CopyDataTypeTag.TxLog,
            mstart,
            mstart + msize,
            FQ(0),
            msize,
            instruction.curr.rw_counter + instruction.rw_counter_offset,
            log_id=instruction.curr.log_id + 1,
        )
    else:
        copy_rwc_inc = FQ(0)

    # omit block number constraint even it is set within op code explicitly, because by default the circuit only handle
    # current block, otherwise, block context lookup is required.
    # calculate dynamic gas cost
    next_memory_size, memory_expansion_gas = instruction.memory_expansion_dynamic_length(
        mstart, msize
    )
    dynamic_gas = (
        GAS_COST_LOG
        + GAS_COST_LOG * (opcode - Opcode.LOG0)
        + GAS_COST_LOGDATA * msize
        + memory_expansion_gas
    )

    assert isinstance(is_persistent, FQ)
    instruction.step_state_transition_in_same_context(
        opcode,
        rw_counter=Transition.delta(instruction.rw_counter_offset + copy_rwc_inc),
        program_counter=Transition.delta(1),
        stack_pointer=Transition.delta(2 + opcode - Opcode.LOG0),
        dynamic_gas_cost=dynamic_gas,
        memory_size=Transition.to(next_memory_size),
        log_id=Transition.delta(is_persistent),
    )
