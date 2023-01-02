from ...util import FQ
from ..execution_state import ExecutionState
from ..instruction import Instruction, Transition
from ..table import CallContextFieldTag

SEPARATE_INVALID_OPCODES = [
    0x0C,
    0x0D,
    0x0E,
    0x0F,
    0x1E,
    0x1F,
    0x5C,
    0x5D,
    0x5E,
    0x5F,
    0xF6,
    0xF7,
    0xF8,
    0xF9,
    0xFB,
    0xFC,
    0xFE,
]

# Gadget for invalid opcodes. It verifies invalid bytes in any condition of:
# - `opcode > 0x20 && opcode < 0x30`
# - `opcode > 0x48 && opcode < 0x50`
# - `opcode > 0xA4 && opcode < 0xF0`
# - one of [`SEPARATE_INVALID_OPCODES`]
def invalid_opcode(instruction: Instruction):
    # Fixed lookup for invalid opcode.
    opcode = instruction.opcode_lookup(True)
    instruction.responsible_opcode_lookup(opcode)

    op_gt_20, _ = instruction.compare(FQ(0x20), opcode, 1)
    op_lt_30, _ = instruction.compare(opcode, FQ(0x30), 1)
    op_gt_48, _ = instruction.compare(FQ(0x48), opcode, 1)
    op_lt_50, _ = instruction.compare(opcode, FQ(0x50), 1)
    op_gt_a4, _ = instruction.compare(FQ(0xA4), opcode, 1)
    op_lt_f0, _ = instruction.compare(opcode, FQ(0xF0), 1)

    op_range_20_30 = op_gt_20.n and op_lt_30.n
    op_range_48_50 = op_gt_48.n and op_lt_50.n
    op_range_a4_f0 = op_gt_a4.n and op_lt_f0.n

    # Check separate byte set if no above condition is met.
    if 1 - (op_range_20_30 or op_range_48_50 or op_range_a4_f0):
        instruction.constrain_in(opcode, [FQ(i) for i in SEPARATE_INVALID_OPCODES])

    # Current call must be failed.
    is_success = instruction.call_context_lookup(CallContextFieldTag.IsSuccess)
    instruction.constrain_equal(is_success, FQ(0))

    # Go to EndTx only when is_root.
    is_to_end_tx = instruction.is_equal(instruction.next.execution_state, ExecutionState.EndTx)
    instruction.constrain_equal(FQ(instruction.curr.is_root), is_to_end_tx)

    # When it's a root call.
    if instruction.curr.is_root:
        # Do step state transition.
        instruction.constrain_step_state_transition(
            rw_counter=Transition.delta(1 + instruction.curr.reversible_write_counter),
            call_id=Transition.same(),
        )
    else:
        # When it is internal call, need to restore caller's state as finishing this call.
        # Restore caller state to next StepState.
        instruction.step_state_transition_to_restored_context(
            rw_counter_delta=1 + instruction.curr.reversible_write_counter.n,
            return_data_offset=FQ(0),
            return_data_length=FQ(0),
            gas_left=instruction.curr.gas_left,
        )
