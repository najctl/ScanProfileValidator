"""CLI entry point: load UTF-8 JSON, print reports and return exit codes."""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

from validator import validate_profiles


def main():
    parser = argparse.ArgumentParser(description='Validate scan profile configs with path-precise diagnostics.')
    parser.add_argument('--input', default='inputs/primary.json', help='UTF-8 fixture JSON')
    arguments = parser.parse_args()
    try:
        text = pathlib.Path(arguments.input).read_text(encoding='utf-8')
        def reject_constant(value):
            raise ValueError('Non-finite numbers are not valid JSON')
        payload = json.loads(text, parse_constant=reject_constant)
        result = validate_profiles(payload)
    except (OSError, UnicodeError):
        print('error: cannot read input as a UTF-8 file', file=sys.stderr)
        return 2
    except json.JSONDecodeError as error:
        print(f'error: malformed JSON at line {error.lineno}, column {error.colno}', file=sys.stderr)
        return 2
    except RecursionError:
        print('error: input nesting exceeds the JSON parser limit', file=sys.stderr)
        return 2
    except ValueError as error:
        print(f'error: {error}', file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if result['summary']['invalid'] else 0


if __name__ == '__main__':
    sys.exit(main())
