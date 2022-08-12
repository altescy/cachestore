# CacheStore

[![Actions Status](https://github.com/altescy/cachestore/workflows/CI/badge.svg)](https://github.com/altescy/cachestore/actions/workflows/ci.yml)
[![Python version](https://img.shields.io/pypi/pyversions/cachestore)](https://github.com/altescy/cachestore)
[![License](https://img.shields.io/github/license/altescy/cachestore)](https://github.com/altescy/cachestore/blob/master/LICENSE)
[![pypi version](https://img.shields.io/pypi/v/cachestore)](https://pypi.org/project/cachestore/)

Function Cache Management Tool for Python

## Installation

```bash
pip install cachestore
```

## Usage

### Python

```pytnon
from cachestore import Cache

cache = Cache()

@cache()
def awesome_function(x, *, y="y", **kwargs):
    ...
```

### CLI

```bash
$ cachestore --help
usage: cachestore

positional arguments:
  {list,remove}

optional arguments:
  -h, --help     show this help message and exit
  --version      show program's version number and exit
```
