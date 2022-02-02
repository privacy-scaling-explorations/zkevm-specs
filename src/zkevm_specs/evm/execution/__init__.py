from typing import Callable, Dict

from ..execution_state import ExecutionState

from .begin_tx import *
from .end_tx import *
from .end_block import *
from .memory_copy import *

# Opcode's successful cases
from .add import *
from .block_coinbase import *
from .block_timestamp import *
from .calldatasize import *
from .caller import *
from .callvalue import *
from .calldatacopy import *
from .gas import *
from .jump import *
from .jumpi import *
from .push import *
from .slt_sgt import *
from .selfbalance import *


EXECUTION_STATE_IMPL: Dict[ExecutionState, Callable] = {
    ExecutionState.BeginTx: begin_tx,
    ExecutionState.EndTx: end_tx,
    ExecutionState.EndBlock: end_block,
    ExecutionState.CopyToMemory: copy_to_memory,
    ExecutionState.ADD: add,
    ExecutionState.CALLER: caller,
    ExecutionState.CALLVALUE: callvalue,
    ExecutionState.CALLDATACOPY: calldatacopy,
    ExecutionState.CALLDATASIZE: calldatasize,
    ExecutionState.COINBASE: coinbase,
    ExecutionState.TIMESTAMP: timestamp,
    ExecutionState.JUMP: jump,
    ExecutionState.JUMPI: jumpi,
    ExecutionState.PUSH: push,
    ExecutionState.SCMP: scmp,
    ExecutionState.GAS: gas,
    ExecutionState.SELFBALANCE: selfbalance,
}
