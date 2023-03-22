# ErrorContractAddressCollision state

### EVM behavior
`ErrorContractAddressCollision` only happen in `create2`. contract address generates by
following in evm. if same code and salt provide, it results in the same address.

`func (evm *EVM) Create2(caller ContractRef, code []byte, gas uint64, endowment *big.Int, salt *uint256.Int) (ret []byte, contractAddr common.Address, leftOverGas uint64, err error) {
	codeAndHash := &codeAndHash{code: code}
	contractAddr = crypto.CreateAddress2(caller.Address(), salt.Bytes32(), codeAndHash.Hash().Bytes())
	return evm.create(caller, codeAndHash, gas, endowment, contractAddr, CREATE2)
}`

for `create`, it used caller address and caller once to derive contract address as below.
so it won't meet address collision issue.

`func (evm *EVM) Create(caller ContractRef, code []byte, gas uint64, value *big.Int) (ret []byte, contractAddr common.Address, leftOverGas uint64, err error) {
	contractAddr = crypto.CreateAddress(caller.Address(), evm.StateDB.GetNonce(caller.Address()))
	return evm.create(caller, &codeAndHash{code: code}, gas, value, contractAddr, CREATE)
}`

when this error occurs, `create` terminate immediately and not run init code anymore.
### Constraints
Note: this error circuit implementation will merge into `create` gadget, so here only listing constraint
when this error requires, others is the same as `create`
1. op code is `create2` when such error happens
2. constrain creating address code hash is not zero(already existing)
3. Current call must be failed and last callee return data and offset is zero .

## Code
    TODO: add after circuit merge first.