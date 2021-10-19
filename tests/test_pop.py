import pytest

from zkevm_specs.encoding import u256_to_u8s, u8s_to_u256
from zkevm_specs.opcode.stack import Stack

WORD_TWO_VALUES = (
    (20, 30),
)


@pytest.mark.parametrize("word1,word2", WORD_TWO_VALUES)
def test_pop(word1, word2):
    evm_stack = Stack()
    evm_stack.push(word1)
    evm_stack.push(word2)
    assert word2 == evm_stack.peek()
    evm_stack.pop()
    assert word1 == evm_stack.peek()
