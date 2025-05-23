# mkdocstrings-go

[![ci](https://github.com/jasiollo/mkdocstrings-go/workflows/ci/badge.svg)](https://github.com/jasiollo/mkdocstrings-go/actions?query=workflow%3Aci)
[![documentation](https://img.shields.io/badge/docs-mkdocs-708FCC.svg?style=flat)](https://jasiollo.github.io/mkdocstrings-go/)
[![pypi version](https://img.shields.io/pypi/v/mkdocstrings-go.svg)](https://pypi.org/project/mkdocstrings-go/)
[![gitter](https://badges.gitter.im/join%20chat.svg)](https://app.gitter.im/#/room/#mkdocstrings-go:gitter.im)

A Go handler for mkdocstrings.

## Installation

```bash
pip install --extra-index-url https://test.pypi.org/simple/ mkdocstrings-go-jasiollo
```

## Usage
### Go into your go project directory and run:
```
mkdocs new .
```
### Add following configuration to mkdocs.yml:
```
plugins:
- mkdocstrings:
    default_handler: go

theme:
  name: "material"
```
### Make sure you have godoc json installed in ~/.go/bin
You can install it by running:
```
go install github.com/rtfd/godocjson@latest
```

### Add .md files containing paths to .go files to include in documentation:
```
# reference

::: /home/flopper/zprp-go/hello/hello.go
```

### Serve documentation
```
mkdoc serve
```