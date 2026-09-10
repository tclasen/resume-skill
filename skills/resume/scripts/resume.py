"""Portable command line entrypoint. Paths are always explicit."""

import argparse
import subprocess
import sys

from pins import validate_pins
from workspace import create_bundle, init_workspace, load_workspace


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("pins", help="Validate the vendored format and ontologies offline")
    for name, help_text in (("init", "Initialize a separate private data repository"),
                            ("workspace", "Check a private workspace")):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("--workspace", required=True)
    bundle = commands.add_parser("bundle", help="Create an applicant or position OKF bundle")
    bundle.add_argument("--workspace", required=True)
    bundle.add_argument("--kind", choices=("applicant", "position"), required=True)
    bundle.add_argument("--id", required=True)
    args = parser.parse_args(argv)
    try:
        validate_pins()
        if args.command == "pins":
            print("OK: all four reviewed pins match")
        elif args.command == "init":
            print(init_workspace(args.workspace))
        elif args.command == "workspace":
            print(load_workspace(args.workspace))
        elif args.command == "bundle":
            print(create_bundle(args.workspace, args.kind, args.id))
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
