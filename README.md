# llm-tools-sandboxed-shell

[![PyPI](https://img.shields.io/pypi/v/llm-tools-sandboxed-shell.svg)](https://pypi.org/project/llm-tools-sandboxed-shell/)
[![Changelog](https://img.shields.io/github/v/release/c0ffee0wl/llm-tools-sandboxed-shell?include_prereleases&label=changelog)](https://github.com/c0ffee0wl/llm-tools-sandboxed-shell/releases)
[![Tests](https://github.com/c0ffee0wl/llm-tools-sandboxed-shell/actions/workflows/test.yml/badge.svg)](https://github.com/c0ffee0wl/llm-tools-sandboxed-shell/actions/workflows/test.yml)

## Installation

Install this plugin in the same environment as [LLM](https://llm.datasette.io/).
```bash
llm install llm-tools-sandboxed-shell
```
## Usage

Usage instructions go here.

## Development

To set up this plugin locally, first checkout the code. Then create a new virtual environment:
```bash
cd llm-tools-sandboxed-shell
python -m venv venv
source venv/bin/activate
```
Now install the dependencies and test dependencies:
```bash
python -m pip install -e '.[test]'
```
To run the tests:
```bash
python -m pytest
```
