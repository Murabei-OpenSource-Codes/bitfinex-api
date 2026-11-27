# bitfinex-api

Python client for [Bitfinex REST API v2](https://docs.bitfinex.com/docs/rest-general)
endpoints used in Murabei crawlers and market-data workflows.

## Objective and scope

This package wraps Bitfinex public and authenticated HTTP endpoints behind a
typed Python client with shared timeouts, retries, and error mapping.

### Install

From a built wheel:

```bash
pip install dist/*.whl
```

From source (Poetry):

```bash
pip install poetry
export VERSION=$(grep -E '^VERSION=' VERSION | cut -d'=' -f2-)
sed -e 's#{VERSION}#'"${VERSION}"'#g' pyproject_template.toml > pyproject.toml
poetry build
pip install dist/*.whl
```

### Import

```python
from bitfinex_api import BitfinexAPI
```

Public-only usage (no API key):

```python
client = BitfinexAPI()
```

Authenticated usage:

```python
client = BitfinexAPI(api_key="...", api_secret="...")
```

### Configuration (environment)

| Variable | Default | Used for |
|----------|---------|----------|
| `BITFINEX__REQUEST_TIMEOUT` | `60` | Seconds per HTTP request |
| `BITFINEX__REQUEST_MAX_ATTEMPTS` | `5` | Max retries on network errors |
| `BITFINEX__REQUEST_RETRY_MIN_WAIT` | `0.5` | Seconds between retries |
| `BITFINEX__PROXY_URL` | _(unset)_ | Optional HTTP(S) proxy |

### Integration tests

1. Copy `test_parameters.template` to `test_parameters.secrets`.
2. Set `BITFINEX__API_KEY` and `BITFINEX__API_SECRET` when testing private
   endpoints (`test_parameters.secrets` is gitignored).
3. Run:

```bash
set -a && source test_parameters.secrets && set +a
python -m unittest discover -s tests -v
```

### Development and release

```bash
ruff check src/
```

Release build (increments patch in `VERSION`, renders `pyproject.toml`,
tags, pushes—see `build.sh`):

```bash
./build.sh
```

Package history: [CHANGELOG.md](CHANGELOG.md).

## License

BSD-3-Clause — see [LICENSE](LICENSE).