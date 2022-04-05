# Zkevm Specifications

[![Python package](https://github.com/appliedzkp/zkevm-specs/actions/workflows/python-package.yml/badge.svg)](https://github.com/appliedzkp/zkevm-specs/actions/workflows/python-package.yml)

The project aims to define a validity snark proof for Ethereum transactions.

## The Written Specification

We recommend the reader to start with [Introduction](./specs/introduction.md)

## Python Executable Specification

We provide the [Beacon Chain](https://github.com/ethereum/eth2.0-specs) style Python executable specification to help implementors figure out the specified behavior.

Installing [poetry](https://python-poetry.org)(Python 3.9 is required)

```
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
```

Installing dependencies

```
make install
```

Run the tests

```
make test
```

## Implementations

See [appliedzkp/zkevm-circuits](https://github.com/appliedzkp/zkevm-circuits)
