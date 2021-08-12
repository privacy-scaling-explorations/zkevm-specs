# State Proof

In EVM the interpreter has ability to do any random read-write access to data like account balance, account storage, or stack and memory in current scope, but it's hard for a circuit to keep tracking these data to ensure their consistency from time to time. So the state proof helps EVM proof to check all the random read-write access records are valid, throgh grouping them by their unique index first, and then sorting them by accessing timestamp. We call the accessing timestamp **global counter**, which counts the number of access records and also serves as an unique identifier for a record.

When state proof is generated, a random access record set is also produced with the global counter as each record's unique identifier, we called this set **bus mapping** because it acts like the bus in computer which transfers data between components. The bus mapping will be shared to EVM proof, then EVM proof can do random read-write access to anything inside the set at any time, with extra subset arguments to argue those accesses indeed form a subset of the one prodced by state proof.

## Random Read-Write Data

State proof maintains the read-write part of [random accessible data](./evm-proof.md#Random-Accessible-Data) of evm proof:

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
def range_lookup(value: int, range: str):
    result = re.search('([(\[])(.+),\s+(.+)([)\]])', range)
    min = eval(result.group(2)) + (1 if result.group(1) == "(" else 0)
    max = eval(result.group(3)) - (1 if result.group(4) == ")" else 0)
    return min <= value and value <= max


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
        self.fields = tuple(["global_counter", "rw"] + self.fields)
        for field in self.fields:
            self.values[field] = kwargs[field]
            setattr(self, field, self.values[field])

    def __sub__(self, rhs):
        if rhs is None:
            return self
        return type(self)(**{field: self.values[field] - rhs.values[field] for field in self.fields})
```

### `AccountNonce`

```python
class AccountNonce(Record):
    fields = ['address', 'nonce']


def account_nonce_constraint(prev: AccountNonce, cur: AccountNonce):
    diff = cur - prev

    # rw should be a Write (currently evm doesn't support read nonce)
    assert cur.rw == RW.Write

    # NOTE: we don't need to check each address is in [0, 2**160) becasue in
    #       evm circuit it always decompress the address into bytes, which might
    #       come from stack or tx. In both case, evm takes masked value, so evm
    #       circuit only cares first 20 bytes, which will always be in range.

    # grouping
    if prev is not None:
        # address should increase (non-strcit)
        # TODO: check this by 160-bit range lookup or other more efficient method
        assert diff.address >= 0

    if prev is None or diff.address != 0:
        # TODO: verify the nonce exist in previous state trie root or initialized to 0
        pass
    elif diff.address == 0:
        # global counter should increase
        assert range_lookup(diff.global_counter, '(0, 2**28)')

        # nonce can only increase by 1
        assert diff.nonce == 1
```

### `AccountBalance`

```python
class AccountBalance(Record):
    fields = ['address', 'balance']


def account_balance_constraint(prev: AccountBalance, cur: AccountBalance):
    diff = cur - prev

    # rw should be a Read or Write
    assert cur.rw == RW.Read or cur.rw == RW.Write

    # NOTE: we don't need to check each address is in [0, 2**160) becasue in
    #       evm circuit it always decompress the address into bytes, which might
    #       come from stack or tx. In both case, evm takes masked value, so evm
    #       circuit only cares first 20 bytes, which will always be in range.

    # grouping
    if prev is not None:
        # address should increase (non-strcit)
        # TODO: check this by 160-bit range lookup or other more efficient method
        assert diff.address >= 0

    if prev is None or diff.address != 0:
        # TODO: verify the balance exist in previous state trie root or initialized to 0
        pass
    elif diff.address == 0:
        # global counter should increase
        assert range_lookup(diff.global_counter, '(0, 2**28)')

        if cur.rw == RW.Read:
            # balance should be consistent to previous one
            assert cur.balance == prev.balance
```

### `AccountCodeHash`

**TODO**

### `AccountStorage`

**TODO**

### `CallState`

**TODO**

### `CallStateStack`

```python
class CallStateStack(Record):
    fields = ['id', 'index', 'value']


def call_state_stack_constraint(prev: CallStateStack, cur: CallStateStack):
    diff = cur - prev

    # rw should be a Read or Write
    assert cur.rw == RW.Read or cur.rw == RW.Write

    # index should be valid (avoid malicious prover to conceal stack overflow / underflow error)
    assert range_lookup(cur.index, '[0, 2**10)')

    # grouping
    if prev is not None:
        # id should increase (non-strcit)
        assert range_lookup(diff.id, '[0, 2**28)')

        if cur.id == prev.id:
            # index should increase by 1 or remain
            assert diff.index == 0 or diff.index == 1

    if prev is None or diff.index != 0:
        # rw should be a Write for the first row of index
        assert cur.rw == RW.Write
    elif diff.index == 0:
        # global counter should increase
        assert range_lookup(diff.global_counter, '(0, 2**28)')

        if cur.rw == RW.Read:
            # value should be consistent to previous one
            assert cur.value == prev.value
```

### `CallStateMemory`

```python
class CallStateMemory(Record):
    fields = ['id', 'index', 'value']


def call_state_memory_constraint(prev: CallStateMemory, cur: CallStateMemory):
    diff = cur - prev

    # rw should be a Read or Write
    assert cur.rw == RW.Read or cur.rw == RW.Write

    # TODO: decide where to check memory index range, we have 2 choices:
    #       1. check in state circuit: we pick a reasonable hard bound and do
    #          range_lookup check
    #       2. check in evm circuit: memory index always comes from stack, so it
    #          will be decompress into bytes in evm circuit, we can just pick the
    #          first n bytes (say 3 bytes) to recompose the memory index and
    #          lookup bus mapping. When the left 32-n bytes are non-zero, it
    #          should always cause an out-of-gas error (expansion of memory size 
    #          to 2**24 leads to gas cost 538,443,776).

    # value should be a byte
    assert range_lookup(cur.value, '[0, 2**8)')

    # grouping
    if prev is not None:
        # id should increase (non-strcit)
        assert range_lookup(diff.id, '[0, 2**28)')

        if cur.id == prev.id:
            # index should increase by 1 or remain
            assert diff.index == 0 or diff.index == 1

    if prev is None or cur.index != prev.index:
        # rw should be a Write for the first row of index
        assert cur.rw == RW.Write
        # value should be 0 for the first row of index
        assert cur.value == 0
    elif cur.index == prev.index:
        # global counter should increase
        assert range_lookup(diff.global_counter, '(0, 2**28)')

        if cur.rw == RW.Read:
            # value should be consistent to previous one
            assert cur.value == prev.value
```

## Circuit Layout

**TODO**
