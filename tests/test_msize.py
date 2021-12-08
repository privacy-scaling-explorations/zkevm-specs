from zkevm_specs.opcode import check_msize, Memory


def test_msize():
    memory = Memory()
    check_msize(memory, 0)

    memory.write(1, 0)
    check_msize(memory, 1)

    memory.write(32, 0)
    check_msize(memory, 2)
