from rlp import decode, encode
from zkevm_specs.evm import Account, generate_contract_address
from zkevm_specs.util import keccak256


def test_contract_address():
    sender_addr0 = Account(address=0x970E8128AB834E8EAC17AB8E3812F010678CF791, nonce=0)
    sender_addr1 = Account(address=0x970E8128AB834E8EAC17AB8E3812F010678CF791, nonce=1)
    sender_addr2 = Account(address=0x970E8128AB834E8EAC17AB8E3812F010678CF791, nonce=2)

    expected_caddr0 = Account(address=0x333C3310824B7C685133F2BEDB2CA4B8B4DF633D)
    expected_caddr1 = Account(address=0x8BDA78331C916A08481428E4B07C96D3E916D165)
    expected_caddr2 = Account(address=0xC9DDEDF451BC62CE88BF9292AFB13DF35B670699)

    caddr0 = generate_contract_address(sender_addr0)
    caddr1 = generate_contract_address(sender_addr1)
    caddr2 = generate_contract_address(sender_addr2)

    assert expected_caddr0.address.to_bytes(20, "big") == caddr0
    assert expected_caddr1.address.to_bytes(20, "big") == caddr1
    assert expected_caddr2.address.to_bytes(20, "big") == caddr2
