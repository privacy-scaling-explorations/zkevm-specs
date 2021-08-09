# ZKEVM Introduction

At the moment every node on ethereum has to validate every transaction in the ethereum virtual machine. This means that every transaction adds work that everyone needs to do to verify ethereums history. Worse still is that each transaction needs to be verified by every new node. Which means the amout of work a new node needs to do the sync the network is growing constantly. We want to build a proof of validity for the Ethereum blocks to avoid this. Are two goals are

1. Make a zkrollup that supports smart contracts
2. Create a proof of validity for every Ethereum block

This means making a proof of validity for the EVM + state reads  / writes + signatures.

To simplify we separate our proofs into two components.

1. **State proof**: State/memory/stack ops have been performed correctly. This does not check if the correct location has been read/written. We allow our prover to pick any location here and in the EVM proof confirm it is correct.
2. **EVM proof**: This checks that the correct opcode is called at the correct time. It checks the validity of these opcodes. It also confirms that for each of these opcodes the state proof performed the correct operation.

Only after verifying both proofs are we confident that that Ethereum block is executed correctly.


## Bus mapping


Our state proof and EVM proof need to talk to eachother. We need some kind of accumulator to do this. Merkle trees where for a long time the best way of achiveing such communication. But this would add 1000’s of consraints to each opcode. instead we use a plookup key value mapping. We call this bus mapping afte the bus on a traditional computer.

One of the big challenges of building a snark to verify a VM is that you need to be able to read random values / opcodes at any time. To do this we use key-value mappings. Key value mappings are basically random linear combinations of all elements


### Plookup key-value mappings
In plookup you can build key-value mappings as follows

``` python
def build_mapping():
    keys = [1,3,5]
    values = [2,4,6]

    randomness = hash(keys, values)

    mappings = []

    for key , value in zip(keys,values):
        mappings.append(key + randomness*value)
    return(mappings)
```


It can be opened at the cost of 3 plookups

``` python
def open_mapping(mappings, keys, values):
    randomness = hash(keys,values)
    index = 1
    # Prover can chose any mapping, key , value
    mapping = plookup(mappings)
    key = plookup(keys)
    value = plookup(values)
    # But it has to satisfy this check
    require(mappings[index] == key[index] + randomness*value[index])
    # with overwhelming probablitiy will not find an invalid mapping.
```

### Bus mapping

```
bus_mapping[global_counter] = {
    type_flag = ["stack", "memory", "storage"],
    rw_flag,
    key,
    value,
    index: opcode,
    call_id: call_id,
    prog_counter: prog_counter
}
```

The bus mapping is witnessed by the prover. In the EVM proof, we have to ensure the prover did not include extra variables. To do this, we limit its degree in the L1 EVM and then check every single element in the EVM proof.

The commitment to the bus mapping is a public input to both the state proof and EVM proof.
