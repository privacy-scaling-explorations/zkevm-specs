from __future__ import annotations
from typing import Any, List, Mapping, Optional, Sequence, Set, Tuple, Type, TypeVar, Union
from enum import IntEnum, auto
from itertools import chain, product
from dataclasses import dataclass, field, fields

from .opcode import constant_gas_cost_pairs
from .precompile import precompile_info_pairs

from ..util import Expression, FQ, Word, WordOrValue
from .execution_state import ExecutionState


class FixedTableTag(IntEnum):
    """
    Tag for FixedTable lookup, where the FixedTable is a prebuilt fixed-column
    table.
    """

    Range5 = auto()  # value, 0, 0
    Range16 = auto()  # value, 0, 0
    Range32 = auto()  # value, 0, 0
    Range64 = auto()  # value, 0, 0
    Range256 = auto()  # value, 0, 0
    Range512 = auto()  # value, 0, 0
    Range1024 = auto()  # value, 0, 0
    Range24_576 = auto()  # value, 0, 0
    SignByte = auto()  # value, signbyte, 0
    BitwiseAnd = auto()  # lhs, rhs, lhs & rhs, 0
    BitwiseOr = auto()  # lhs, rhs, lhs | rhs, 0
    BitwiseXor = auto()  # lhs, rhs, lhs ^ rhs, 0
    ResponsibleOpcode = auto()  # execution_state, opcode, aux
    Pow2 = auto()  # value, value_pow
    OpcodeConstantGas = auto()  # opcode constant gas
    PrecompileInfo = auto()  # precompile constant gas

    def table_assignments(self) -> List[FixedTableRow]:
        if self == FixedTableTag.Range5:
            return [FixedTableRow(FQ(self), FQ(i), FQ(0), FQ(0)) for i in range(5)]
        if self == FixedTableTag.Range16:
            return [FixedTableRow(FQ(self), FQ(i), FQ(0), FQ(0)) for i in range(16)]
        elif self == FixedTableTag.Range32:
            return [FixedTableRow(FQ(self), FQ(i), FQ(0), FQ(0)) for i in range(32)]
        elif self == FixedTableTag.Range64:
            return [FixedTableRow(FQ(self), FQ(i), FQ(0), FQ(0)) for i in range(64)]
        elif self == FixedTableTag.Range256:
            return [FixedTableRow(FQ(self), FQ(i), FQ(0), FQ(0)) for i in range(256)]
        elif self == FixedTableTag.Range512:
            return [FixedTableRow(FQ(self), FQ(i), FQ(0), FQ(0)) for i in range(512)]
        elif self == FixedTableTag.Range1024:
            return [FixedTableRow(FQ(self), FQ(i), FQ(0), FQ(0)) for i in range(1024)]
        elif self == FixedTableTag.Range24_576:
            return [FixedTableRow(FQ(self), FQ(i), FQ(0), FQ(0)) for i in range(24576)]
        elif self == FixedTableTag.SignByte:
            return [FixedTableRow(FQ(self), FQ(i), FQ((i >> 7) * 0xFF), FQ(0)) for i in range(256)]
        elif self == FixedTableTag.BitwiseAnd:
            return [
                FixedTableRow(FQ(self), FQ(lhs), FQ(rhs), FQ(lhs & rhs))
                for lhs, rhs in product(range(256), range(256))
            ]
        elif self == FixedTableTag.BitwiseOr:
            return [
                FixedTableRow(FQ(self), FQ(lhs), FQ(rhs), FQ(lhs | rhs))
                for lhs, rhs in product(range(256), range(256))
            ]
        elif self == FixedTableTag.BitwiseXor:
            return [
                FixedTableRow(FQ(self), FQ(lhs), FQ(rhs), FQ(lhs ^ rhs))
                for lhs, rhs in product(range(256), range(256))
            ]
        elif self == FixedTableTag.ResponsibleOpcode:
            return [
                FixedTableRow(FQ(self), FQ(execution_state), FQ(opcode), FQ(aux))
                for execution_state in list(ExecutionState)
                for opcode, aux in map(
                    lambda pair: pair if isinstance(pair, tuple) else (pair, 0),
                    execution_state.responsible_opcode(),
                )
            ]
        elif self == FixedTableTag.OpcodeConstantGas:
            return [
                FixedTableRow(FQ(self), FQ(code[0]), FQ(code[1]), FQ(0))
                for code in constant_gas_cost_pairs()
            ]
        elif self == FixedTableTag.Pow2:
            return [
                FixedTableRow(
                    FQ(self),
                    FQ(value),
                    FQ(1 << value) if value < 128 else FQ(0),
                    FQ(0) if value < 128 else FQ(1 << (value - 128)),
                )
                for value in range(256)
            ]
        elif self == FixedTableTag.PrecompileInfo:
            return [
                FixedTableRow(
                    FQ(self), FQ(execution_state), FQ(precompile_address), FQ(base_gas_cost)
                )
                for (execution_state, precompile_address, base_gas_cost) in precompile_info_pairs()
            ]
        else:
            raise ValueError("Unreacheable")

    def range_table_tag(range: int) -> FixedTableTag:
        if range == 5:
            return FixedTableTag.Range5
        if range == 16:
            return FixedTableTag.Range16
        elif range == 32:
            return FixedTableTag.Range32
        elif range == 64:
            return FixedTableTag.Range64
        elif range == 256:
            return FixedTableTag.Range256
        elif range == 512:
            return FixedTableTag.Range512
        elif range == 1024:
            return FixedTableTag.Range1024
        elif range == 24576:
            return FixedTableTag.Range24_576
        else:
            raise ValueError(
                f"Range {range} lookup is not supported yet, please add a new variant Range{range} in FixedTableTag with proper table assignments"
            )


class BlockContextFieldTag(IntEnum):
    """
    Tag for BlockTable lookup, where the BlockTable is an instance-column table
    where part of it will be built by verifier.
    We can also merge BlockTable and TxTable together to save columns, but for
    simplicity we keep them separate for now.
    """

    Coinbase = auto()
    GasLimit = auto()
    Number = auto()
    Timestamp = auto()
    PrevRandao = auto()
    BaseFee = auto()
    ChainId = auto()
    HistoryHash = auto()


class TxContextFieldTag(IntEnum):
    """
    Tag for TxTable lookup, where the TxTable is an instance-column table where
    part of it will be built by verifier.
    Note that the field here is targeting legacy transaction format, supporting
    of EIP1559 is deferred to future work.
    """

    Nonce = auto()
    Gas = auto()
    GasPrice = auto()
    CallerAddress = auto()
    CalleeAddress = auto()
    IsCreate = auto()
    Value = auto()
    CallDataLength = auto()
    CallDataGasCost = auto()
    TxInvalid = auto()
    AccessListGasCost = auto()
    TxSignHash = auto()
    CallData = auto()


class BytecodeFieldTag(IntEnum):
    """
    Tag for BytecodeTable lookup.
    """

    Header = 1
    Byte = 2


class RW(IntEnum):
    Read = 0
    Write = 1


class Target(IntEnum):
    """
    Tag for RWTable lookup, where the RWTable an advice-column table built by
    prover, which will be part of State circuit and each unit read-write data
    will be verified to be consistent between each write.
    """

    Start = auto()  # Used for upper rows padding

    TxAccessListAccount = auto()
    TxAccessListAccountStorage = auto()
    TxRefund = auto()

    Account = auto()
    AccountStorage = auto()

    CallContext = auto()
    Stack = auto()
    Memory = auto()
    TxLog = auto()
    TxReceipt = auto()

    # For state writes which affect future execution before reversion, we need
    # to write them with reversion when the write might fail.
    def write_with_reversion(self) -> bool:
        return self in [
            Target.TxAccessListAccount,
            Target.TxAccessListAccountStorage,
            Target.Account,
            Target.AccountStorage,
            Target.TxRefund,
        ]


class AccountFieldTag(IntEnum):
    Nonce = auto()
    Balance = auto()
    CodeHash = auto()
    NonExisting = auto()


class CallContextFieldTag(IntEnum):
    """
    Tag for RWTable lookup with tag CallContext, which is used to index specific
    field of CallContext.
    """

    # The following are read-only data inside a call, they will be written in
    # State circuit directly in their first row, and most of them will be
    # read and checked to be agreed with caller before the beginning of call.
    # It's not like transaction or bytecode that require specifically friendly
    # layout for verification, so maintaining the consistency directly in
    # RWTable seems more intuitive than creating another table for it.
    RwCounterEndOfReversion = auto()  # to know at which point in the future we should revert
    CallerId = auto()  # to know caller's id
    TxId = auto()  # to know tx's id
    Depth = auto()  # to know if call too deep
    CallerAddress = auto()
    CalleeAddress = auto()
    CallDataOffset = auto()
    CallDataLength = auto()
    ReturnDataOffset = auto()  # for callee to set return_data to caller's memeory
    ReturnDataLength = auto()
    Value = auto()
    IsSuccess = auto()  # to peek result in the future
    IsPersistent = auto()  # to know if current call is within reverted call or not
    IsStatic = auto()  # to know if state modification is within static call or not
    IsRoot = auto()
    IsCreate = auto()
    CodeHash = auto()

    # The following are read-only data inside a call like previous section for
    # opcode RETURNDATASIZE and RETURNDATACOPY, except they will be updated when
    # end of callee execution.
    LastCalleeId = auto()
    LastCalleeReturnDataOffset = auto()
    LastCalleeReturnDataLength = auto()

    # The following are used by caller to save its own CallState when it's
    # going to dive into another call, and will be read out to restore caller's
    # CallState in the end by callee.
    # Note that stack and memory could also be included here, but since they
    # need extra constraints on their data format, so we separate them to be
    # different kinds of Target.
    ProgramCounter = auto()
    StackPointer = auto()
    GasLeft = auto()
    MemorySize = auto()
    ReversibleWriteCounter = auto()


class TxLogFieldTag(IntEnum):
    """
    Tag for RWTable lookup with tag TxLog, which is used to index specific
    field of TxLog.
    """

    # The following are write-only data inside a transaction, they will be written in
    # State circuit directly.
    Address = auto()  # address of the contract that generated the event
    Topic = auto()  # list of topics provided by the contract
    Data = auto()  # log data in bytes
    TopicLength = auto()  # topic number, For RLP encoding
    DataLength = auto()  # how many bytes read from memory, For RLP encoding


class TxReceiptFieldTag(IntEnum):
    """
    Tag for RWTable lookup with tag TxReceipt, which is used to index specific
    field of TxReceipt.
    """

    # The following are write-only data inside a transaction, they will be written in
    # State circuit directly.
    PostStateOrStatus = auto()  # flag indicates whether if a tx succeed or not
    # the cumulative gas used in the block containing the transaction receipt as of immediately
    # after the transaction has happened.
    CumulativeGasUsed = auto()
    # record how many log entries in the receipt/tx , 0 if tx fails
    LogLength = auto()


class CopyDataTypeTag(IntEnum):
    """
    Tag for CopyTable that specifies the type of data source.
    """

    Bytecode = auto()
    Memory = auto()
    TxCalldata = auto()
    TxLog = auto()

    # RLC Accumulator tag can be used whenever we wish to
    # accumulates `value` iteratively over all the steps in
    # copy circuit. This is specifically used in the SHA3
    # opcode execution where the copy table's last row has
    # an accumulated value that is the RLC representation of
    # all input bytes. Using this value, we can then lookup
    # the Keccak table for the SHA3 of the input bytes.
    RlcAcc = auto()


class MPTProofType(IntEnum):
    """
    Tag for MPT lookup.
    """

    NonceMod = 1
    BalanceMod = 2
    CodeHashMod = 3
    NonExistingAccountProof = 4
    AccountDeleteMod = 5
    StorageMod = 6
    NonExistingStorageProof = 7
    WithdrawalMod = 8

    @staticmethod
    def from_account_field_tag(field_tag: AccountFieldTag) -> MPTProofType:
        if field_tag == AccountFieldTag.Nonce:
            return MPTProofType.NonceMod
        if field_tag == AccountFieldTag.Balance:
            return MPTProofType.BalanceMod
        elif field_tag == AccountFieldTag.CodeHash:
            return MPTProofType.CodeHashMod
        elif field_tag == AccountFieldTag.NonExisting:
            return MPTProofType.NonExistingAccountProof
        raise Exception("Unexpected AccountFieldTag value")


class WrongQueryKey(Exception):
    def __init__(self, table_name: str, diff: Set[str]) -> None:
        self.message = f"Lookup {table_name} with invalid keys {diff}"


class LookupUnsatFailure(Exception):
    def __init__(self, table_name: str, inputs: Any) -> None:
        self.inputs = inputs
        self.message = f"Lookup {table_name} is unsatisfied on inputs {inputs}"


class LookupAmbiguousFailure(Exception):
    def __init__(self, table_name: str, inputs: Any, matched_rows: Sequence[Any]) -> None:
        self.inputs = inputs
        self.message = f"Lookup {table_name} is ambiguous on inputs {inputs}, ${len(matched_rows)} matched rows found: {matched_rows}"


@dataclass(frozen=True)
class TableRow:
    @classmethod
    def validate_query(cls, table_name: str, query: Mapping[str, Any]):
        names = set([field.name for field in fields(cls)])
        queried = set(query.keys())
        if not queried.issubset(names):
            raise WrongQueryKey(table_name, queried - names)

    def match(self, query: Mapping[str, Union[Expression, Word]]) -> bool:
        match = True
        for key, value in query.items():
            rhs = getattr(self, key)
            if isinstance(value, Word):
                assert isinstance(rhs, Word)
                match = match and (
                    value.lo.expr() == rhs.lo.expr() and value.hi.expr() == rhs.hi.expr()
                )
            else:
                assert isinstance(value, Expression) and isinstance(rhs, Expression)
                match = match and (value.expr() == rhs.expr())
        return match


@dataclass(frozen=True)
class FixedTableRow(TableRow):
    tag: Expression
    value0: Expression
    value1: Expression = field(default=FQ(0))
    value2: Expression = field(default=FQ(0))


@dataclass(frozen=True)
class BlockTableRow(TableRow):
    field_tag: Expression
    # meaningful only for HistoryHash, will be zero for other tags
    block_number_or_zero: Expression
    value: WordOrValue


@dataclass(frozen=True)
class TxTableRow(TableRow):
    tx_id: Expression
    field_tag: Expression
    # meaningful only for CallData, will be zero for other tags
    call_data_index_or_zero: Expression
    value: WordOrValue


@dataclass(frozen=True)
class WithdrawalTableRow(TableRow):
    id: Expression
    validator_id: Expression
    address: Word
    amount: Expression


@dataclass(frozen=True)
class BytecodeTableRow(TableRow):
    bytecode_hash: Word
    field_tag: Expression
    index: Expression
    is_code: Expression
    value: Expression


@dataclass(frozen=True)
class RWTableRow(TableRow):
    rw_counter: Expression
    rw: Expression
    key0: Expression  # Target
    id: Expression = field(default=FQ(0))
    address: Expression = field(default=FQ(0))
    field_tag: Expression = field(default=FQ(0))
    storage_key: Word = field(default=Word(0))
    value: WordOrValue = field(default=WordOrValue(FQ(0)))
    value_prev: WordOrValue = field(default=WordOrValue(FQ(0)))
    aux0: Word = field(default=Word(0))  # TODO: Rename this to initial_value


@dataclass(frozen=True)
class MPTTableRow(TableRow):
    address: Expression
    proof_type: Expression
    storage_key: Word
    root: Word
    root_prev: Word
    value: Word
    value_prev: Word


@dataclass(frozen=True)
class CopyCircuitRow(TableRow):
    q_step: FQ
    is_first: FQ
    is_last: FQ
    id: WordOrValue  # one of call_id, bytecode_hash, tx_id
    tag: FQ  # CopyDataTypeTag
    addr: FQ
    src_addr_end: FQ
    bytes_left: FQ
    value: FQ
    rlc_acc: FQ
    is_code: FQ
    is_pad: FQ
    rw_counter: FQ
    rwc_inc_left: FQ
    is_memory: FQ
    is_bytecode: FQ
    is_tx_calldata: FQ
    is_tx_log: FQ
    is_rlc_acc: FQ


@dataclass(frozen=True)
class CopyTableRow(TableRow):
    is_first: FQ
    src_id: WordOrValue
    src_tag: FQ
    dst_id: WordOrValue
    dst_tag: FQ
    src_addr: FQ
    src_addr_end: FQ
    dst_addr: FQ
    length: FQ
    rlc_acc: FQ
    rw_counter: FQ
    rwc_inc: FQ


@dataclass(frozen=True)
class KeccakTableRow(TableRow):
    state_tag: FQ
    input_rlc: FQ
    input_len: FQ
    output: Word


@dataclass(frozen=True)
class ExpCircuitRow(TableRow):
    q_usable: FQ
    # columns from the exponentiation table
    is_step: FQ
    identifier: FQ  # rw_counter
    is_last: FQ
    base: Word
    exponent: Word
    exponentiation: Word
    # columns from the MulAddGadget (a*b + c == d)
    a: Word
    b: Word
    c: Word
    d: Word
    # columns from the parity check (2*q + r == exponent)
    q: Word
    r: FQ


@dataclass(frozen=True)
class ExpTableRow(TableRow):
    is_step: FQ
    identifier: FQ
    is_last: FQ
    base_limb0: FQ
    base_limb1: FQ
    base_limb2: FQ
    base_limb3: FQ
    exponent: Word
    exponentiation: Word


class Tables:
    """
    A collection of lookup tables used in EVM circuit.
    """

    fixed_table = set(chain(*[tag.table_assignments() for tag in list(FixedTableTag)]))
    block_table: Set[BlockTableRow]
    tx_table: Set[TxTableRow]
    withdrawal_table: Set[WithdrawalTableRow]
    bytecode_table: Set[BytecodeTableRow]
    rw_table: Set[RWTableRow]
    copy_table: Set[CopyTableRow]
    keccak_table: Set[KeccakTableRow]
    exp_table: Set[ExpTableRow]

    def __init__(
        self,
        block_table: Set[BlockTableRow],
        tx_table: Set[TxTableRow],
        withdrawal_table: Set[WithdrawalTableRow],
        bytecode_table: Set[BytecodeTableRow],
        rw_table: Union[Set[Sequence[Expression]], Set[RWTableRow]],
        copy_circuit: Optional[Sequence[CopyCircuitRow]] = None,
        keccak_table: Optional[Sequence[KeccakTableRow]] = None,
        exp_circuit: Optional[Sequence[ExpCircuitRow]] = None,
    ) -> None:
        self.block_table = block_table
        self.tx_table = tx_table
        self.withdrawal_table = withdrawal_table
        self.bytecode_table = bytecode_table
        self.rw_table = set(
            row if isinstance(row, RWTableRow) else RWTableRow(*row)  # type: ignore  # (RWTableRow input args)
            for row in rw_table
        )
        if copy_circuit is not None:
            self.copy_table = self._convert_copy_circuit_to_table(copy_circuit)
        if keccak_table is not None:
            self.keccak_table = set(keccak_table)
        if exp_circuit is not None:
            self.exp_table = self._convert_exp_circuit_to_table(exp_circuit)

    def _convert_copy_circuit_to_table(self, copy_circuit: Sequence[CopyCircuitRow]):
        rows: List[CopyTableRow] = []
        for i, row in enumerate(copy_circuit):
            # the first row and the row next to it will be used for its fields.
            if row.is_first == 1:
                first_row = row
                assert i + 1 < len(copy_circuit), "Not enough rows in copy circuit"
                next_row = copy_circuit[i + 1]
                assert next_row.q_step == 0, "Invalid copy circuit"
                rows.append(
                    CopyTableRow(
                        is_first=first_row.is_first,
                        src_id=first_row.id,
                        src_tag=first_row.tag,
                        dst_id=next_row.id,
                        dst_tag=next_row.tag,
                        src_addr=first_row.addr,
                        src_addr_end=first_row.src_addr_end,
                        dst_addr=next_row.addr,
                        length=first_row.bytes_left,
                        rlc_acc=row.rlc_acc,
                        rw_counter=first_row.rw_counter,
                        rwc_inc=first_row.rwc_inc_left,
                    )
                )
        return set(rows)

    def _convert_exp_circuit_to_table(self, exp_circuit: Sequence[ExpCircuitRow]):
        rows: List[ExpTableRow] = []
        for i, row in enumerate(exp_circuit):
            base_limbs = row.base.to_64s()
            rows.append(
                ExpTableRow(
                    is_step=FQ.one(),
                    identifier=row.identifier,
                    is_last=row.is_last,
                    base_limb0=base_limbs[0],
                    base_limb1=base_limbs[1],
                    base_limb2=base_limbs[2],
                    base_limb3=base_limbs[3],
                    exponent=row.exponent,
                    exponentiation=row.exponentiation,
                )
            )
        return set(rows)

    def fixed_lookup(
        self,
        tag: Expression,
        value0: Expression,
        value1: Expression = FQ(0),
        value2: Expression = FQ(0),
    ) -> FixedTableRow:
        query = {
            "tag": tag,
            "value0": value0,
            "value1": value1,
            "value2": value2,
        }
        row = FixedTableRow(tag, value0, value1, value2)
        if row not in self.fixed_table:
            raise LookupUnsatFailure(FixedTableRow.__name__, query)
        return row

    def block_lookup(
        self, field_tag: Expression, block_number: Expression = FQ(0)
    ) -> BlockTableRow:
        query = {"field_tag": field_tag, "block_number_or_zero": block_number}
        return lookup(BlockTableRow, self.block_table, query)

    def tx_lookup(
        self, tx_id: Expression, field_tag: Expression, call_data_index: Expression = FQ(0)
    ) -> TxTableRow:
        query = {
            "tx_id": tx_id,
            "field_tag": field_tag,
            "call_data_index_or_zero": call_data_index,
        }
        return lookup(TxTableRow, self.tx_table, query)

    def withdrawal_lookup(
        self, id: Expression, validator_id: Expression, address: Word, amount: Expression
    ) -> WithdrawalTableRow:
        query = {
            "id": id,
            "validator_id": validator_id,
            "address": address,
            "amount": amount,
        }
        return lookup(WithdrawalTableRow, self.withdrawal_table, query)

    def bytecode_lookup(
        self,
        bytecode_hash: Word,
        field_tag: Expression,
        index: Expression,
        is_code: Optional[Expression] = None,
    ) -> BytecodeTableRow:
        query: Mapping[str, Union[FQ, Expression, Word, None]] = {
            "bytecode_hash": bytecode_hash,
            "field_tag": field_tag,
            "index": index,
            "is_code": is_code,
        }
        return lookup(BytecodeTableRow, self.bytecode_table, query)

    def rw_lookup(
        self,
        rw_counter: Expression,
        rw: Expression,
        tag: Expression,
        id: Optional[Expression] = None,
        address: Optional[Expression] = None,
        field_tag: Optional[Expression] = None,
        storage_key: Optional[Word] = None,
        value: Optional[Word] = None,
        value_prev: Optional[Word] = None,
        aux0: Optional[Word] = None,
    ) -> RWTableRow:
        query = {
            "rw_counter": rw_counter,
            "rw": rw,
            "key0": tag,
            "id": id,
            "address": address,
            "field_tag": field_tag,
            "storage_key": storage_key,
            "value": value,
            "value_prev": value_prev,
            "aux0": aux0,
        }
        return lookup(RWTableRow, self.rw_table, query)

    def copy_lookup(
        self,
        src_id: Union[Expression, Word],
        src_tag: Expression,
        dst_id: Union[Expression, Word],
        dst_tag: Expression,
        src_addr: Expression,
        src_addr_end: Expression,
        dst_addr: Expression,
        length: Expression,
        rw_counter: Expression,
        log_id: Optional[Expression] = None,
    ) -> CopyTableRow:
        if dst_tag == CopyDataTypeTag.TxLog:
            assert log_id is not None
            dst_addr = dst_addr + FQ(int(TxLogFieldTag.Data) << 32) + FQ(log_id.expr().n << 48)
        query: Mapping[str, Union[FQ, Expression, Word, None]] = {
            "src_id": WordOrValue(src_id),
            "src_tag": src_tag,
            "dst_id": WordOrValue(dst_id),
            "dst_tag": dst_tag,
            "src_addr": src_addr,
            "src_addr_end": src_addr_end,
            "dst_addr": dst_addr,
            "length": length,
            "rw_counter": rw_counter,
        }
        return lookup(CopyTableRow, self.copy_table, query)

    def keccak_lookup(self, length: Expression, value_rlc: Expression):
        query = {
            "state_tag": FQ(2),  # Finalize
            "input_len": length,
            "input_rlc": value_rlc,
        }
        return lookup(KeccakTableRow, self.keccak_table, query)

    def exp_lookup(
        self,
        identifier: Expression,
        is_last: Expression,
        base_limbs: Tuple[Expression, ...],
        exponent: Word,
    ):
        query: Mapping[str, Union[FQ, Expression, Word, None]] = {
            "is_step": FQ.one().expr(),
            "identifier": identifier.expr(),
            "is_last": is_last.expr(),
            "base_limb0": base_limbs[0].expr(),
            "base_limb1": base_limbs[1].expr(),
            "base_limb2": base_limbs[2].expr(),
            "base_limb3": base_limbs[3].expr(),
            "exponent": exponent,
        }
        return lookup(ExpTableRow, self.exp_table, query)


T = TypeVar("T", bound=TableRow)


def lookup(
    table_cls: Type[T],
    table: Set[T],
    query: Mapping[str, Optional[Union[FQ, Expression, Word]]],
) -> T:
    table_name = table_cls.__name__
    table_cls.validate_query(table_name, query)

    matched_rows = [
        row
        for row in table
        # Filter out None values
        if row.match({key: value for key, value in query.items() if value is not None})
    ]

    if len(matched_rows) == 0:
        raise LookupUnsatFailure(table_name, query)
    elif len(matched_rows) > 1:
        raise LookupAmbiguousFailure(table_name, query, matched_rows)

    return matched_rows[0]
