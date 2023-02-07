from rlp import decode, encode
from zkevm_specs.util import keccak256, address_encode, generate_contract_address


def test_contract_address():
    sender_address = address_encode("970E8128AB834E8EAC17Ab8E3812F010678CF791")

    caddr0 = generate_contract_address(sender_address, 0)
    caddr1 = generate_contract_address(sender_address, 1)
    caddr2 = generate_contract_address(sender_address, 2)

    assert "333c3310824b7c685133f2bedb2ca4b8b4df633d" == caddr0.hex()
    assert "8bda78331c916a08481428e4b07c96d3e916d165" == caddr1.hex()
    assert "c9ddedf451bc62ce88bf9292afb13df35b670699" == caddr2.hex()
