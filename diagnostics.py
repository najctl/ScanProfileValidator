"""JSON paths, safe report formatting and deterministic summaries."""
from __future__ import annotations

import json
import re


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

    for result in results:
        result['name'] = redact(result['name'])
        for key in ('errors', 'warnings'):
            for diagnostic in result[key]:
                diagnostic['path'] = redact(diagnostic['path'])
                diagnostic['message'] = redact(diagnostic['message'])
            result[key].sort(key=lambda d: (d['path'], d['code']))
    valid = sum(p['valid'] for p in results)
    return dict(profiles=results, summary=dict(profiles=len(results), valid=valid, invalid=len(results)-valid, errors=sum(len(p['errors']) for p in results), warnings=sum(len(p['warnings']) for p in results)))
