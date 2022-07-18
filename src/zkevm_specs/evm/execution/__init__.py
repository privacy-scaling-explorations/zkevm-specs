from typing import Callable, Dict

from ..execution_state import ExecutionState

from .begin_tx import *
from .end_tx import *
from .end_block import *

# Opcode's successful cases
from .add_sub import *
from .addmod import *
from .mulmod import *
from .block_ctx import *
from .call_ctx import *
from .calldatasize import *
from .caller import *
from .callvalue import *
from .calldatacopy import *
from .calldataload import *
from .codecopy import *
from .codesize import *
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
from .shr import shr
from .bitwise import not_opcode
from .sdiv_smod import sdiv_smod
from .stop import stop


EXECUTION_STATE_IMPL: Dict[ExecutionState, Callable] = {
    ExecutionState.BeginTx: begin_tx,
    ExecutionState.EndTx: end_tx,
    ExecutionState.EndBlock: end_block,
    ExecutionState.ADD: add_sub,
    ExecutionState.ADDMOD: addmod,
    ExecutionState.MULMOD: mulmod,
    ExecutionState.MUL: mul_div_mod,
    ExecutionState.NOT: not_opcode,
    ExecutionState.ORIGIN: origin,
    ExecutionState.CALLER: caller,
    ExecutionState.CALLVALUE: callvalue,
    ExecutionState.CALLDATACOPY: calldatacopy,
    ExecutionState.CALLDATALOAD: calldataload,
    ExecutionState.CALLDATASIZE: calldatasize,
    ExecutionState.CODECOPY: codecopy,
    ExecutionState.CODESIZE: codesize,
    ExecutionState.BlockCtx: blockctx,
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
    ExecutionState.LOG: log,
    ExecutionState.CALLCtx: call_ctx,
    ExecutionState.ISZERO: iszero,
    ExecutionState.SHR: shr,
    ExecutionState.SDIV_SMOD: sdiv_smod,
    ExecutionState.STOP: stop,
}
