## How to configure environment
```bash
cd restiny
pyenv local 3.13
python3 -m venv venv
./venv/bin/activate
pip install -r requirements.txt
pip install -r requirements.dev.txt
```

## How to run
- In one console (For debugging)
```bash
textual console -x event -x debug -x system -x worker
```

- And in another console (To run the app)
> When running with textual and ending execution, this message will be displayed:
>```bash
>Unclosed client session
>client_session: <aiohttp.client.ClientSession object at 0x7764cad8a420>
>```
> Don’t worry — this does not happen in production.
```bash
textual run --dev restiny/__main__.py
```

## How to lint
```bash
ruff format .; ruff check --fix .
```
