from typing import Callable, Dict

from ..execution_state import ExecutionState

from .begin_tx import *
from .end_tx import *
from .end_block import *
from .memory_copy import *
from .copy_to_log import *

# Opcode's successful cases
from .add_sub import *
from .block_coinbase import *
from .block_timestamp import *
from .block_number import *
from .call import *
from .calldatasize import *
from .caller import *
from .callvalue import *
from .calldatacopy import *
from .calldataload import *
from .gas import *
from .iszero import *
from .jump import *
from .jumpi import *
from .mul_div_mod import *
from .origin import *
from .push import *
from .slt_sgt import *
from .gas import *
from .gasprice import *
from .storage import *
from .selfbalance import *
from .extcodehash import *
from .log import *


EXECUTION_STATE_IMPL: Dict[ExecutionState, Callable] = {
    ExecutionState.BeginTx: begin_tx,
    ExecutionState.EndTx: end_tx,
    ExecutionState.EndBlock: end_block,
    ExecutionState.CopyToMemory: copy_to_memory,
    ExecutionState.ADD: add_sub,
    ExecutionState.MUL: mul_div_mod,
    ExecutionState.ORIGIN: origin,
    ExecutionState.CALLER: caller,
    ExecutionState.CALLVALUE: callvalue,
    ExecutionState.CALLDATACOPY: calldatacopy,
    ExecutionState.CALLDATALOAD: calldataload,
    ExecutionState.CALLDATASIZE: calldatasize,
    ExecutionState.COINBASE: coinbase,
    ExecutionState.TIMESTAMP: timestamp,
    ExecutionState.NUMBER: number,
    ExecutionState.JUMP: jump,
    ExecutionState.JUMPI: jumpi,
    ExecutionState.PUSH: push,
    ExecutionState.SCMP: scmp,
    ExecutionState.GAS: gas,
    ExecutionState.SLOAD: sload,
    ExecutionState.SSTORE: sstore,
    ExecutionState.SELFBALANCE: selfbalance,
    ExecutionState.GASPRICE: gasprice,
    ExecutionState.EXTCODEHASH: extcodehash,
    ExecutionState.CopyToLog: copy_to_log,
    ExecutionState.LOG: log,
    ExecutionState.CALL: call,
    ExecutionState.ISZERO: iszero,
}
