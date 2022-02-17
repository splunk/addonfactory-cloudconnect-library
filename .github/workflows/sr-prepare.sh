#!/usr/bin/env bash

set -eE
set -v
poetry version $1
poetry build