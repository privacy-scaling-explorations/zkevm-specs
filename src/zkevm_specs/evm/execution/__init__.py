from typing import Callable, Dict

from ..execution_state import ExecutionState

from .begin_tx import *

# Opcode's successful cases
from .add import *
from .jump import *
from .jumpi import *
from .push import *
from .block_coinbase import *
from .caller import *


EXECUTION_STATE_IMPL: Dict[ExecutionState, Callable] = {
    ExecutionState.BeginTx: begin_tx,
    ExecutionState.ADD: add,
    ExecutionState.CALLER: caller,
    ExecutionState.COINBASE: coinbase,
    ExecutionState.JUMP: jump,
    ExecutionState.JUMPI: jumpi,
    ExecutionState.PUSH: push,
}
