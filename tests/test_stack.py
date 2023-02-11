import pytest

from zkevm_specs.opcode.stack import Stack

WORD_TWO_VALUES = ((20, 30),)

WORD_THREE_VALUES = ((20, 30, 40),)


@pytest.mark.parametrize("word1,word2", WORD_TWO_VALUES)
def test_pop(word1, word2):
    evm_stack = Stack()
    evm_stack.push(word1)
    evm_stack.push(word2)
    assert word2 == evm_stack.peek()
    evm_stack.pop()
    assert word1 == evm_stack.peek()


@pytest.mark.parametrize("word1,word2", WORD_TWO_VALUES)
def check_dupx(word1, word2):
    evm_stack = Stack()
    evm_stack.push(word1)
    evm_stack.push(word2)
    assert word2 == evm_stack.peek()
    evm_stack.dupx(2)
    assert word1 == evm_stack.peek()


@pytest.mark.parametrize("word1,word2,word3", WORD_THREE_VALUES)
def check_swapx(word1, word2, word3):
    evm_stack = Stack()
    evm_stack.push(word1)
    evm_stack.push(word2)
    evm_stack.push(word3)
    evm_stack.swapx(2)
    assert word1 == evm_stack.peek()
    evm_stack.pop()
    evm_stack.pop()
    assert word3 == evm_stack.peek()
