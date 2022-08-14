# Examples

This is an example of CacheStore including the following files:

- `square.py`: Python script with CacheStore
- `cachestore.ini`: Configuration file of CacheStore

## Run example script with CacheStore

Execute python script like below.
Logs will be shown and you can see how to behave cached functions.

```bash
$ python square.py
INFO:cachestore.config:Load config from cachestore.ini
cache.name='square:cache'
cache.settings=CacheSettings(storage=LocalStorage(root=mycachestore), ...)
...
```

`cachestore list` command shows cache statuses of each function:

```bash
$ cachestore list square:cache
2022-08-14 18:00:12,708 - INFO - cachestore.config - Load config from cachestore.ini
name         function               filename  cache last_executed_at
============ ====================== ========= ===== ===================
square:cache square.square          square.py ✓     2022-08-14 17:58:56
square:cache square.expired_square  square.py       2022-08-14 17:58:56
square:cache square.ignored_square  square.py ✓     2022-08-14 17:58:56
square:cache square.disabled_square square.py
```

You can also see more details with subcommand `details -f <function name>`
as follows:

```bash
$ cachestore list square:cache details -f square.square
2022-08-14 18:00:58,724 - INFO - cachestore.config - Load config from cachestore.ini
cache        function      filename  params executed_at         expired_at
============ ============= ========= ====== =================== ==========
square:cache square.square square.py x=3    2022-08-14 17:58:56
square:cache square.square square.py x=2    2022-08-14 17:58:56
```

By using `cachestore remove -f <function name>` command, you can remove all
caches of the specified function.

```bash
$ cachestore remove square:cache
2022-08-14 18:07:17,557 - INFO - cachestore.config - Load config from cachestore.ini
remove: square.squares
```
