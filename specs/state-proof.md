# State Proof

In EVM the interpreter has ability to do any random read-write access to data like account balance, account storage, or stack and memory in current scope, but it's hard for a circuit to keep tracking these data to ensure their consistency from time to time. So the state proof helps EVM proof to check all the random read-write access records are valid, throgh grouping them by their unique index first, and then sorting them by accessing timestamp. We call the accessing timestamp **global counter**, which counts the number of access records and also serves as an unique identifier for a record.

When state proof is generated, a random access record set is also produced with the global counter as each record's unique identifier, we called this set **bus mapping** because it acts like the bus in computer which transfers data between components. The bus mapping will be shared to EVM proof, then EVM proof can do random read-write access to anything inside the set at any time, with extra subset arguments to argue those accesses indeed form a subset of the one prodced by state proof.

## Random Read-Write Data

State proof maintains the read-write part of [random accessible data](./evm-proof.md#Random-Accessible-Data) of EVM proof:

| Target                                | Index             | Description                              |
| ------------------------------------- | ----------------- | ---------------------------------------- |
| [`AccountNonce`](#AccountNonce)       | `{address}`       | Account's nonce                          |
| [`AccountBalance`](#AccountBalance)   | `{address}`       | Account's balance                        |
| [`AccountCodeHash`](#AccountCodeHash) | `{address}`       | Account's code hash                      |
| [`AccountStorage`](#AccountStorage)   | `{address}.{key}` | Account's storage as a key-value mapping |
| [`CallState`](#CallState)             | `{id}.{enum}`     | Call's internal state                    |
| [`CallStateStack`](#CallStateStack)   | `{id}.{index}`    | Call's stack as a encoded word array     |
| [`CallStateMemory`](#CallStateMemory) | `{id}.{index}`    | Call's memory as a byte array            |

The concatenation of **Target** and **Index** becomes the unique index for data. Each record will be attached with a global counter as their accessing timestamp, and the records are constraint to be in group by their unique index first and to be sorted by their global counter increasingly. Given the access to previous record, each target has their custom constraints, for example, `AccountNonce` always increase by 1, and values in `CallStateMemory` should fit in 8-bit.

## Circuit Constraints

The following part describes the custom constraints for each target by a python script. There are some common helper class and function:

```python
def range_lookup(value: int, range: range):
    return range.start <= value and value < range.stop


class RW(Enum):
    Read: int = 0
    Write: int = 1

    def __sub__(self, _):
        return None


class Record:
    fields: Tuple[str]
    values: object

    def __init__(self, **kwargs) -> None:
        self.values = {}
        self.fields = tuple(['global_counter', 'rw'] + self.fields)
        for field in self.fields:
            self.values[field] = kwargs[field]
            setattr(self, field, self.values[field])

    def __sub__(self, rhs):
        if rhs is None:
            return self
        return type(self)(**{field: self.values[field] - rhs.values[field] for field in self.fields})


class ReadWriteGate:
    group_fields: Tuple[(str, Callable)]

    def constraint(self, prev, cur):
        diff = cur - prev

        is_first_row = prev is None
        is_first_row_in_group = is_first_row or \
            any([getattr(diff, field) != 0 for field, _ in self.group_fields])

        # grouping
        if not is_first_row:
            for field, group_fn in self.group_fields:
                assert(group_fn(cur, prev, diff))
                if getattr(diff, field) != 0:
                    break

        # rw should be valid
        assert cur.rw in (RW.Read, RW.Write)

        # global counter should increase in group
        if not is_first_row_in_group:
            assert range_lookup(diff.global_counter, range(1, 2**28))

        type(self).constraint_every_row(prev, cur, diff)
        type(self).constraint_in_group(prev, cur, diff, is_first_row_in_group)

    @abstractclassmethod
    def constraint_every_row(prev, cur, diff):
        raise NotImplemented

    @abstractclassmethod
    def constraint_in_group(prev, cur, diff, is_first_row_in_group):
        raise NotImplemented
```

### `AccountNonce`

| Field     | Description     |
| --------- | --------------- |
| `address` | account address |
| `nonce`   | account nonce   |

```python
class AccountNonce(Record):
    fields = ['address', 'nonce']


class AccountNonceGate(ReadWriteGate):
    group_fields = [
        # TODO: check address by 160-bit range lookup or other more efficient method
        ('address', lambda cur, pre, diff: diff.address >= 0)
    ]

    def constraint_every_row(prev: AccountNonce, cur: AccountNonce, diff: AccountNonce):
        # rw should be a Write (currently evm doesn't support read nonce)
        assert cur.rw == RW.Write

        # NOTE: we don't need to check each address is in [0, 2**160) becasue in
        #       evm circuit it always decompress the address into bytes, which might
        #       come from stack or tx. In both case, evm takes masked value, so evm
        #       circuit only cares first 20 bytes, which will always be in range.

    def constraint_in_group(prev: AccountNonce, cur: AccountNonce, diff: AccountNonce, is_first_row_in_group: bool):
        if is_first_row_in_group:
            # TODO: verify the nonce exist in previous state trie root or initialized to 0
            pass
        else:
            # nonce can only increase by 1
            assert diff.nonce == 1
```

### `AccountBalance`

| Field     | Description                    |
| --------- | ------------------------------ |
| `address` | account address                |
| `balance` | account balance (encoded word) |

```python
class AccountBalance(Record):
    fields = ['address', 'balance']


class AccountBalanceGate(ReadWriteGate):
    group_fields = [
        # TODO: check address by 160-bit range lookup or other more efficient method
        ('address', lambda cur, pre, diff: diff.address >= 0)
    ]

    def constraint_every_row(prev: AccountBalance, cur: AccountBalance, diff: AccountBalance):
        # NOTE: we don't need to check each address (same reason of AccountNonce)
        pass

    def constraint_in_group(prev: AccountBalance, cur: AccountBalance, diff: AccountBalance, is_first_row_in_group: bool):
        if is_first_row_in_group:
            # rw should be a Write for the first row in group
            assert cur.rw == RW.Write

            # TODO: verify the balance exist in previous state trie root or initialized to 0
            pass
        else:
            if cur.rw == RW.Read:
                # balance should be consistent to previous one
                assert diff.balance == 0
```

### `AccountCodeHash`

**TODO**

### `AccountStorage`

**TODO** - add field `is_cold_load` for [`EIP2929`](https://eips.ethereum.org/EIPS/eip-2929) and [`EIP2930`](https://eips.ethereum.org/EIPS/eip-2930).

| Field        | Description                                                         |
| ------------ | ------------------------------------------------------------------- |
| `address`    | account address                                                     |
| `key`        | storage key (encoded word)                                          |
| `value`      | storage value (encoded word)                                        |
| `value_prev` | storage value in previous record, used for reverting (encoded word) |

```python
class AccountStorage(Record):
    fields = ['address', 'key', 'value', 'value_prev']


class AccountStorageGate(ReadWriteGate):
    group_fields = [
        # TODO: check address by 160-bit range lookup or other more efficient method
        ('address', lambda cur, pre, diff: diff.address >= 0),
        # TODO: check key by bytes comparator in case overflow
        ('key', lambda cur, pre, diff: diff.key >= 0),
    ]

    def constraint_every_row(prev: AccountStorage, cur: AccountStorage, diff: AccountStorage):
        # NOTE: we don't need to check each address (same reason of AccountNonce)
        pass

    def constraint_in_group(prev: AccountStorage, cur: AccountStorage, diff: AccountStorage, is_first_row_in_group: bool):
        if is_first_row_in_group:
            # rw should be a Write for the first row in group
            assert cur.rw == RW.Write

            # TODO: verify the storage exist in previous state trie root or initialized to 0
            pass
        else:
            if cur.rw == RW.Read:
                # value and value_prev should be consistent to previous one
                assert diff.value == 0 and diff.value_prev == 0
            elif cur.rw == RW.Write:
                # value_prev should be previous one
                assert cur.value_prev == prev.value
```

### `CallState`

| Field   | Description                             |
| ------- | --------------------------------------- |
| `id`    | call id                                 |
| `enum`  | state field as a enum (`CallStateEnum`) |
| `value` | state value (encoded word)              |

```python
class CallStateEnum(Enum):
    ProgramCounter = 1
    StackPointer = 2
    MemeorySize = 3
    GasCounter = 4
    StateWriteCounter = 5
    CalleeId = 6
    ReturndataOffset = 7
    ReturndataSize = 8

    def __sub__(self, rhs):
        return self.value - rhs.value


class CallState(Record):
    fields = ['id', 'enum', 'value']


class CallStateGate(ReadWriteGate):
    group_fields = [
        # TODO: decide a reasonable call id range circuit should support
        ('id', lambda cur, pre, diff: diff.id >= 0),
        # enum should increase by 1 or remain
        ('enum', lambda cur, pre, diff: diff.enum in (0, 1)),
    ]

    def constraint_every_row(prev: CallState, cur: CallState, diff: CallState):
        # enum should be valid
        assert range_lookup(cur.enum.value, range(1, len(CallStateEnum) + 1))

    def constraint_in_group(prev: CallState, cur: CallState, diff: CallState, is_first_row_in_group: bool):
        if is_first_row_in_group:
            # rw should be a Write for the first row in group
            assert cur.rw == RW.Write
        else:
            if cur.rw == RW.Read:
                # value should be consistent to previous one
                assert diff.value == 0
```

### `CallStateStack`

| Field   | Description                |
| ------- | -------------------------- |
| `id`    | call id                    |
| `index` | stack index                |
| `value` | stack value (encoded word) |

```python
class CallStateStack(Record):
    fields = ['id', 'index', 'value']


class CallStateStackGate(ReadWriteGate):
    group_fields = [
        # TODO: decide a reasonable call id range circuit should support
        ('id', lambda cur, pre, diff: diff.id >= 0),
        # index should increase by 1 or remain
        ('index', lambda cur, pre, diff: diff.index in (0, 1)),
    ]

    def constraint_every_row(prev: CallStateStack, cur: CallStateStack, diff: CallStateStack):
        # index should be valid (avoid malicious prover to conceal stack overflow / underflow error)
        assert range_lookup(cur.index, range(0, 2**10))

    def constraint_in_group(prev: CallStateStack, cur: CallStateStack, diff: CallStateStack, is_first_row_in_group: bool):
        if is_first_row_in_group:
            # rw should be a Write for the first row in group
            assert cur.rw == RW.Write
        else:
            if cur.rw == RW.Read:
                # value should be consistent to previous one
                assert diff.value == 0
```

### `CallStateMemory`

| Field   | Description                 |
| ------- | --------------------------- |
| `id`    | call id                     |
| `index` | memory index                |
| `value` | memory value (encoded word) |

```python
class CallStateMemory(Record):
    fields = ['id', 'index', 'value']


class CallStateMemoryGate(ReadWriteGate):
    group_fields = [
        # TODO: decide a reasonable call id range circuit should support
        ('id', lambda cur, pre, diff: diff.id >= 0),
        # TODO: decide a reasonable memory index range circuit should support
        ('index', lambda cur, pre, diff: diff.index >= 0),
    ]

    def constraint_every_row(prev: CallStateMemory, cur: CallStateMemory, diff: CallStateMemory):
        # TODO: decide where to check memory index range, we have 2 choices:
        #       1. check in state circuit: we decide a reasonable hard bound and do
        #          range_lookup check
        #       2. check in evm circuit: memory index always comes from stack, so it
        #          will be decompress into bytes in evm circuit, we can just pick the
        #          first n bytes (say 3 bytes) to recompose the memory index and
        #          lookup bus mapping. When the left 32-n bytes are non-zero, it
        #          should always cause an out-of-gas error (expansion of memory size
        #          to 2**24 leads to gas cost 538,443,776).

        # value should be a byte
        assert range_lookup(cur.value, range(0, 2**8))

    def constraint_in_group(prev: CallStateMemory, cur: CallStateMemory, diff: CallStateMemory, is_first_row_in_group: bool):
        if is_first_row_in_group:
            # rw should be a Write for the first row in group
            assert cur.rw == RW.Write

            # value should be 0 for the first row in group
            assert cur.value == 0
        else:
            if cur.rw == RW.Read:
                # value should be consistent to previous one
                assert diff.value == 0
```

## Circuit Layout

**TODO**
