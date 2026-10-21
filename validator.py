"""Reusable scan-profile validation independent of files and the CLI."""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from diagnostics import child_path, finalize_report


def validate_profiles(payload, arguments=None):
    """Return a report without changing payload; raise ValueError for invalid structure."""
    if not isinstance(payload, dict):
        raise ValueError('input must be a JSON object')
    policy = payload.get('policy')
    if not isinstance(policy, dict):
        raise ValueError('$.policy must be an object')
    for key in ('allowed_suffixes', 'secret_prefixes'):
        values = policy.get(key)
        if not isinstance(values, list) or any(not isinstance(v, str) or not v or (key == 'allowed_suffixes' and not v.startswith('.')) for v in values):
            raise ValueError(f'$.policy.{key} must be an array of valid strings')
    profiles = payload.get('profiles')
    if not isinstance(profiles, list) or any(not isinstance(p, dict) for p in profiles):
        raise ValueError('$.profiles must be an array of objects')
    prefixes = tuple(policy['secret_prefixes'])
    secrets, names, results = set(), set(), []
    for index, profile in enumerate(profiles):
        root = f'$.profiles[{index}]'
        errors, warnings, secret_paths = [], [], set()

        def scan(value, path):
            # An explicit stack handles deep unknown fields without Python recursion.
            pending = [(value, path)]
            while pending:
                value, path = pending.pop()
                if isinstance(value, str) and value.startswith(prefixes):
                    secrets.add(value)
                    secret_paths.add(path)
                    errors.append(dict(path=path, code='secret', message='Secret value redacted'))
                elif isinstance(value, dict):
                    pending.extend((item, child_path(path, key)) for key, item in value.items())
                elif isinstance(value, list):
                    pending.extend((item, f'{path}[{i}]') for i, item in enumerate(value))

        scan(profile, root)

        def error(path, code, message):
            if path not in secret_paths:
                errors.append(dict(path=path, code=code, message=message))

        def get(obj, key, parent, expected, required=True):
            path = child_path(parent, key)
            if key not in obj:
                if required:
                    error(path, 'missing', 'Required field is missing')
                return None
            if path in secret_paths:
                return None
            if type(obj[key]) is not expected:
                error(path, 'type', f'Expected {expected.__name__}')
                return None
            return obj[key]

        def unknown(obj, allowed, parent):
            for key in obj.keys() - allowed:
                warnings.append(dict(path=child_path(parent, key), code='unknown_field', message='Unknown field'))

        unknown(profile, {'name', 'target', 'schedule', 'auth', 'max_duration_minutes', 'exclude_paths'}, root)
        name = get(profile, 'name', root, str)
        if name is not None:
            if not re.fullmatch(r'[a-z][a-z0-9-]{2,39}', name):
                error(root + '.name', 'invalid', 'Name must match [a-z][a-z0-9-]{2,39}')
            if name.casefold() in names:
                error(root + '.name', 'duplicate', 'Name repeats an earlier profile ignoring case')
            names.add(name.casefold())
        target = get(profile, 'target', root, str)
        if target is not None:
            try:
                url = urlsplit(target)
                allowed = url.scheme == 'https' and bool(url.hostname) and url.hostname.lower().endswith(tuple(policy['allowed_suffixes']))
                url.port  # Reject malformed or out-of-range ports.
                allowed = allowed and not any(c.isspace() or ord(c) < 32 for c in target)
            except ValueError:
                allowed = False
            if not allowed:
                error(root + '.target', 'invalid', 'Expected an HTTPS URL with an allowed hostname')
        schedule = get(profile, 'schedule', root, str)
        if schedule is not None and not re.fullmatch(r'(?:daily|weekly (?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)) (?:[01][0-9]|2[0-3]):[0-5][0-9]', schedule):
            error(root + '.schedule', 'invalid', 'Expected daily HH:MM or weekly DAY HH:MM with a valid time')
        duration = get(profile, 'max_duration_minutes', root, int)
        if duration is not None and not 5 <= duration <= 240:
            error(root + '.max_duration_minutes', 'invalid', 'Duration must be between 5 and 240')
        auth = get(profile, 'auth', root, dict)
        if auth is not None:
            parent = root + '.auth'
            unknown(auth, {'type', 'token_ref', 'recording_id'}, parent)
            kind = get(auth, 'type', parent, str)
            if kind is not None and kind not in {'none', 'bearer', 'recorded'}:
                error(parent + '.type', 'invalid', 'Expected none, bearer or recorded')
            elif kind is not None:
                used = {'bearer': 'token_ref', 'recorded': 'recording_id'}.get(kind)
                for key, pattern in (('token_ref', r'[A-Z][A-Z0-9_]{2,63}'), ('recording_id', r'rec-[0-9]{4}')):
                    if key == used:
                        value = get(auth, key, parent, str)
                        if value is not None and not re.fullmatch(pattern, value):
                            error(parent + '.' + key, 'invalid', 'Invalid authentication reference format')
                    elif key in auth:
                        error(parent + '.' + key, 'not_allowed', 'Field is not used by this authentication type')
        excludes = get(profile, 'exclude_paths', root, list, False)
        if excludes is not None:
            seen = set()
            for i, value in enumerate(excludes):
                path = f'{root}.exclude_paths[{i}]'
                if path in secret_paths:
                    continue
                if not isinstance(value, str):
                    error(path, 'type', 'Expected str')
                    continue
                if not value.startswith('/'):
                    error(path, 'invalid', 'Excluded path must start with /')
                if value in seen:
                    error(path, 'duplicate', 'Excluded path repeats an earlier entry')
                seen.add(value)
        results.append(dict(index=index, name=profile.get('name') if isinstance(profile.get('name'), str) else None, valid=not errors, errors=errors, warnings=warnings))

    return finalize_report(results, secrets)
