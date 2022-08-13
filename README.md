# CacheStore

[![Actions Status](https://github.com/altescy/cachestore/workflows/CI/badge.svg)](https://github.com/altescy/cachestore/actions/workflows/ci.yml)
[![Python version](https://img.shields.io/pypi/pyversions/cachestore)](https://github.com/altescy/cachestore)
[![License](https://img.shields.io/github/license/altescy/cachestore)](https://github.com/altescy/cachestore/blob/master/LICENSE)
[![pypi version](https://img.shields.io/pypi/v/cachestore)](https://pypi.org/project/cachestore/)

Function Cache Management Tool for Python

## About

**CacheStore** is a cache management system for Python functions by
storing execution results into a external storage. You can resuse the
cached result from the second time even accross different executions.

**cachestore** command enables you to manange the cached result from
command line. Please see `--help` for more details.

**Features**

- Easily caching execution results by decorating target functions
- Exporting the cached result into external storage to reuse them access different exeutions
- Detecting appropreate caches based on argumetns/source code of functions
- Changing cache behavior via configuration file (see [exmaples](./examples))
- Providing CLI tool to manage caches

## Installation

```bash
pip install cachestore
```

## Usage

### Python

```python
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
  {list,prune,remove}

optional arguments:
  -h, --help           show this help message and exit
  --version            show program's version number and exit
```
