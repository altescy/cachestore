# CacheStore

Function Cache Management Tool for Python

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
