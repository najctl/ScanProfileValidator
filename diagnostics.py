"""JSON paths, safe report formatting and deterministic summaries."""
from __future__ import annotations

import json
import re


_PATH_TOKEN = re.compile(
    r'\.(?P<plain>[A-Za-z_][A-Za-z0-9_]*)'
    r'|\[(?P<index>[0-9]+)\]'
    r'|\[(?P<quoted>"(?:[^"\\]|\\.)*")\]'
)


def child_path(parent, key):
    return parent + '.' + key if re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', key) else parent + '[' + json.dumps(key) + ']'


def finalize_report(results, secrets):
    """Redact fresh report objects, sort diagnostics, and calculate totals."""
    # Preserve the report schema and diagnostic codes. Replace only display text.
    # One substitution pass prevents secret matches inside inserted markers.
    secret_pattern = re.compile('|'.join(re.escape(s) for s in sorted(secrets, key=lambda s: (-len(s), s)))) if secrets else None

    def redact(value):
        if isinstance(value, str) and secret_pattern is not None:
            return secret_pattern.sub(lambda match: '[REDACTED]', value)
        return value

    def redact_path(path):
        # Decode each key before matching secrets, then escape the safe key.
        # Matching against already-escaped path text misses quotes/backslashes.
        # Each original key is redacted once, so markers are never reprocessed.
        def render(token):
            if token.group('index') is not None:
                return token.group(0)
            key = token.group('plain')
            if key is None:
                key = json.loads(token.group('quoted'))
            return child_path('', redact(key))

        return _PATH_TOKEN.sub(render, path)

    for result in results:
        result['name'] = redact(result['name'])
        for key in ('errors', 'warnings'):
            for diagnostic in result[key]:
                diagnostic['path'] = redact_path(diagnostic['path'])
                diagnostic['message'] = redact(diagnostic['message'])
            result[key].sort(key=lambda d: (d['path'], d['code']))
    valid = sum(p['valid'] for p in results)
    return dict(profiles=results, summary=dict(profiles=len(results), valid=valid, invalid=len(results)-valid, errors=sum(len(p['errors']) for p in results), warnings=sum(len(p['warnings']) for p in results)))
