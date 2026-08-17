"""Specification-compatible H0271.xlsx -> config.js entry point."""

import sys

from model_sync import run_export


if __name__ == "__main__":
    run_export(sys.argv[1:])
