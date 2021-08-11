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

The following part describes the custom constraints for each target by a python script.

### `AccountNonce`

```python
class AccountNonceRecord:
    global_counter: int
    rw: RW
    address: Address
    nonce: int


def account_noncee_constraint(prev: AccountNonceRecord, cur: AccountNonceRecord):
    # address should be valid
    assert range_lookup(cur.address, 160)
    # rw should be a Write
    assert cur.rw == RW.Write

    # grouping
    if prev is not None:
        # address should increase (non-strcit)
        assert cur.address >= prev.address

    if prev is None or cur.address != prev.address:
        # TODO: verify the nonce exist in previous state trie root
        pass
    elif cur.address == prev.address:
        # global counter should increase
        assert cur.global_counter > prev.global_counter
        # nonce can only increase by 1
        assert cur.nonce == prev.nonce + 1
```

### `AccountBalance`

```python
class AccountBalanceRecord:
    global_counter: int
    rw: RW
    address: Address
    balance: int


def account_balance_constraint(prev: AccountBalanceRecord, cur: AccountBalanceRecord):
    # address should be valid
    assert range_lookup(cur.address, 160)
    # rw should be a Read or Write
    assert cur.rw == RW.Read or cur.rw == RW.Write

    # grouping
    if prev is not None:
        # address should increase (non-strcit)
        assert cur.address >= prev.address

    if prev is None or cur.address != prev.address:
        # TODO: verify the nonce exist in previous state trie root
        pass
    elif cur.address == prev.address:
        # global counter should increase
        assert cur.global_counter > prev.global_counter

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
class CallStateStackRecord:
    global_counter: int
    rw: RW
    id: int
    index: int
    value: int


def call_state_stack_constraint(prev: CallStateStackRecord, cur: CallStateStackRecord):
    # index should be valid (stack size is 1024)
    assert range_lookup(cur.index, 10)
    # rw should be a Read or Write
    assert cur.rw == RW.Read or cur.rw == RW.Write

    # grouping
    if prev is not None:
        # id should increase (non-strcit)
        assert cur.id >= prev.id

        if cur.id == prev.id:
            # index should increase (non-strcit)
            assert cur.index >= prev.index

    if prev is None or cur.index != prev.index:
        # rw should be a Write for the first row of index
        assert cur.rw == RW.Write
    elif cur.index == prev.index:
        # global counter should increase
        assert cur.global_counter > prev.global_counter

        if cur.rw == RW.Read:
            # value should be consistent to previous one
            assert cur.value == prev.value
```

### `CallStateMemory`

```python
class CallStateMemoryRecord:
    global_counter: int
    rw: RW
    id: int
    index: int
    value: int


def call_state_memory_constraint(prev: CallStateMemoryRecord, cur: CallStateMemoryRecord):
    # index should be valid (circuit hard bound for memory size, which leads to gas cost 538,443,776)
    assert range_lookup(cur.index, 24)
    # rw should be a Read or Write
    assert cur.rw == RW.Read or cur.rw == RW.Write
    # value should be a byte
    assert range_lookup(cur.value, 8)

    # grouping
    if prev is not None:
        # id should increase (non-strcit)
        assert cur.id >= prev.id

        if cur.id == prev.id:
            # index should increase (non-strcit)
            assert cur.index >= prev.index

    if prev is None or cur.index != prev.index:
        # rw should be a Write for the first row of index
        assert cur.rw == RW.Write
        # value should be 0 for the first row of index
        assert cur.value == 0
    elif cur.index == prev.index:
        # global counter should increase
        assert cur.global_counter > prev.global_counter

        if cur.rw == RW.Read:
            # value should be consistent to previous one
            assert cur.value == prev.value
```

## Circuit Layout

**TODO**
