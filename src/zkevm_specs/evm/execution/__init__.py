from typing import Callable, Dict

from ..execution_state import ExecutionState

from .begin_tx import *
from .end_tx import *
from .end_block import *

# Opcode's successful cases
from .add_sub import *
from .addmod import *
from .address import *
from .mulmod import *
from .block_ctx import *
from .blockhash import *
from .call import *
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
from .returndatasize import *
from .slt_sgt import *
from .gas import *
from .gasprice import *
from .storage import *
from .selfbalance import *
from .extcodehash import *
from .log import *
from .bitwise import not_opcode
from .sar import *
from .sdiv_smod import sdiv_smod
from .sha3 import sha3
from .shl_shr import shl_shr
from .stop import stop
from .return_ import *
from .extcodecopy import *


EXECUTION_STATE_IMPL: Dict[ExecutionState, Callable] = {
    ExecutionState.BeginTx: begin_tx,
    ExecutionState.EndTx: end_tx,
    ExecutionState.EndBlock: end_block,
    ExecutionState.ADD: add_sub,
    ExecutionState.ADDMOD: addmod,
    ExecutionState.ADDRESS: address,
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
    ExecutionState.BLOCKHASH: blockhash,
    ExecutionState.JUMP: jump,
    ExecutionState.JUMPI: jumpi,
    ExecutionState.PUSH: push,
    ExecutionState.RETURNDATASIZE: returndatasize,
    ExecutionState.SCMP: scmp,
    ExecutionState.GAS: gas,
    ExecutionState.SHA3: sha3,
    ExecutionState.SLOAD: sload,
    ExecutionState.SSTORE: sstore,
    ExecutionState.SELFBALANCE: selfbalance,
    ExecutionState.GASPRICE: gasprice,
    ExecutionState.EXTCODECOPY: extcodecopy,
    ExecutionState.EXTCODEHASH: extcodehash,
    ExecutionState.LOG: log,
    ExecutionState.CALL: call,
    ExecutionState.ISZERO: iszero,
    ExecutionState.SAR: sar,
    ExecutionState.SDIV_SMOD: sdiv_smod,
    ExecutionState.SHL_SHR: shl_shr,
    ExecutionState.STOP: stop,
    ExecutionState.RETURN: return_,
}
