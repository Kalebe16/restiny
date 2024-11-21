
- [For users](#for-users)
  - [How to install](#how-to-install)
  - [How to install (Alternative: Download pre-built executables)](#how-to-install-alternative-download-pre-built-executables)
  - [How to run](#how-to-run)
  - [How to update (pip installations only)](#how-to-update-pip-installations-only)
  - [How to uninstall (pip installations only)](#how-to-uninstall-pip-installations-only)
- [For developers](#for-developers)
  - [How to configure environment](#how-to-configure-environment)
  - [How to run](#how-to-run-1)
  - [How to lint](#how-to-lint)
  - [Third-party Licenses](#third-party-licenses)
- [Why??](#why)

# For users

## How to install

> **Note**: You need to have python installed on your machine.

```bash
pip install "https://github.com/Kalebe16/restiny/archive/refs/heads/main.zip"
pip install restiny # Coming soon — will be available on PyPI shortly
```

## How to install (Alternative: Download pre-built executables)

> **Note**: This is useful if you don’t have Python installed or prefer a standalone binary.

You can also download platform-specific executables directly from the [Releases page](https://github.com/Kalebe16/restiny/releases)

## How to run
```bash
restiny
# Or
python3 -m restiny
```

## How to update (pip installations only)
```bash
pip install --upgrade restiny
```

## How to uninstall (pip installations only)
```bash
pip uninstall restiny
```

# For developers

## How to configure environment
```bash
cd restiny
pyenv local 3.13.1
python3 -m venv venv
./venv/bin/activate
pip install -r requirements.txt
pip install -r requirements.dev.txt
```

## How to run
- In the first console (For debugging)
```bash
textual console -x event -x debug -x system -x worker
```

- In the second console (To run the app)
> When running with textual and ending execution, this message will be displayed:
```bash
Unclosed client session
client_session: <aiohttp.client.ClientSession object at 0x7764cad8a420>
```
> Don’t worry — this does not happen in production.
```bash
textual run --dev restiny/__main__.py
```

## How to lint
```bash
ruff format .; ruff check --fix .
```

## Third-party Licenses

Restiny uses several third-party libraries, each with their respective licenses.

| Package                                                    | License       | Link                                                                          |
|------------------------------------------------------------|---------------|-------------------------------------------------------------------------------|
| [textual](https://github.com/Textualize/textual)           | MIT License   | [Ver licença](https://github.com/Textualize/textual/blob/main/LICENSE)        |
| [httpx](https://github.com/encode/httpx)                   | BSD 3-Clause  | [Ver licença](https://github.com/encode/httpx/blob/master/LICENSE.md)         |
| [pyperclip](https://github.com/asweigart/pyperclip)        | BSD 3-Clause  | [Ver licença](https://github.com/asweigart/pyperclip/blob/master/LICENSE.txt) |


# Why??

_Just for fun! 😄_
