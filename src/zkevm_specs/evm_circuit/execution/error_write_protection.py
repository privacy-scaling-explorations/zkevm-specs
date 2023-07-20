from zkevm_specs.evm_circuit.table import RW, CallContextFieldTag

from ...util import FQ
from ..instruction import Instruction
from ..opcode import Opcode


# There are some op codes which modify state.
# There are `[SSTORE, CREATE, CREATE2, CALL, SELFDESTRUCT, LOG0, LOG1, LOG2, LOG3, LOG4]`.
# When execution call context is read only (static call) and internal call,
# these op codes running will encounter write protection error
def error_write_protection(instruction: Instruction):
    # retrieve op code associated to oog constant error
    opcode = instruction.opcode_lookup(True)
    (
        is_sstore,
        is_create,
        is_create2,
        is_call,
        is_selfdestruct,
        is_log0,
        is_log1,
        is_log2,
        is_log3,
        is_log4,
    ) = instruction.multiple_select(
        opcode,
        (
            Opcode.SSTORE,
            Opcode.CREATE,
            Opcode.CREATE2,
            Opcode.CALL,
            Opcode.SELFDESTRUCT,
            Opcode.LOG0,
            Opcode.LOG1,
            Opcode.LOG2,
            Opcode.LOG3,
            Opcode.LOG4,
        ),
    )

    # Spec 1. opcode must be [SSTORE, CREATE, CREATE2, CALL, SELFDESTRUCT, LOG0, LOG1, LOG2, LOG3, LOG4].
    instruction.constrain_equal(
        is_sstore
        + is_create
        + is_create2
        + is_call
        + is_selfdestruct
        + is_log0
        + is_log1
        + is_log2
        + is_log3
        + is_log4,
        FQ(1),
    )

    # Spec 2.
    # current call must be an internal call
    is_root = instruction.call_context_lookup(CallContextFieldTag.IsRoot)
    instruction.constrain_equal(is_root, FQ(0))
    # current call context must be readonly
    is_static = instruction.call_context_lookup(CallContextFieldTag.IsStatic)
    instruction.constrain_equal(is_static, FQ(1))

    # Spec 3. for `CALL` op code, `value` must be  non-zero
    if is_call == FQ(1):
        # the first 2 stacks are `gas`` and `callee_address` and the 3rd one is `value`
        value = instruction.stack_lookup(RW.Read, 2)
        instruction.constrain_not_zero_word(value)

    # There is one rw lookup in `constrain_error_state`
    instruction.constrain_error_state(instruction.rw_counter_offset + 1)
