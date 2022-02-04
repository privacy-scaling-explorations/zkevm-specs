from typing import Callable, Dict

from ..execution_state import ExecutionState

from .begin_tx import *
from .end_tx import *
from .end_block import *

# Opcode's successful cases
from .add import *
from .block_coinbase import *
from .block_timestamp import *
from .calldatasize import *
from .caller import *
from .callvalue import *
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
    ExecutionState.ADD: add,
    ExecutionState.CALLER: caller,
    ExecutionState.CALLVALUE: callvalue,
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
