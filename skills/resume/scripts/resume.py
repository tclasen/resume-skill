"""Portable command line entrypoint. Paths are always explicit."""

import argparse
import json
from pathlib import Path
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
    for name, help_text in (("add", "Add a new attributed OKF concept without overwriting"),
                            ("validate", "Validate a bundle against the resume authoring profile")):
        command = commands.add_parser(name, help=help_text)
        command.add_argument("--workspace", required=True)
        command.add_argument("--kind", choices=("applicant", "position"), required=True)
        command.add_argument("--bundle", required=True)
        if name == "add":
            command.add_argument("--id", required=True)
            command.add_argument("--file", required=True, help="UTF-8 OKF Markdown concept")
    prop = commands.add_parser("property", help="Look up an exact approved ontology property definition")
    prop.add_argument("uri")
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
        else:
            from knowledge import add_concept, properties, validate_bundle
            if args.command == "add":
                print(add_concept(args.workspace, args.kind, args.bundle, args.id,
                                  Path(args.file).read_text(encoding="utf-8")))
            elif args.command == "validate":
                print(json.dumps(validate_bundle(args.workspace, args.kind, args.bundle), indent=2))
            elif args.command == "property":
                catalog = properties()
                if args.uri not in catalog:
                    raise ValueError("URI is not a defined property in the approved pinned ontologies")
                print(json.dumps(catalog[args.uri], ensure_ascii=False, indent=2))
    except ModuleNotFoundError as error:
        print(f"Missing dependency: {error.name}. Install scripts/requirements.txt in a virtual environment.", file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
