from __future__ import annotations
import copy
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import validate_profiles


def run_cli(*args):
    return subprocess.run([sys.executable, str(ROOT / 'app.py'), *args], cwd=ROOT, capture_output=True, text=True)


def batch():
    return {'policy': {'allowed_suffixes': ['.north.example.test'], 'secret_prefixes': ['demo_tok_', 'DEMO-KEY-']}, 'profiles': [{'name': 'api-nightly', 'target': 'https://api.north.example.test/', 'schedule': 'daily 02:30', 'auth': {'type': 'none'}, 'max_duration_minutes': 90}]}


class ValidatorTests(unittest.TestCase):
    def codes(self, data):
        return [(e['path'], e['code']) for p in validate_profiles(data)['profiles'] for e in p['errors']]

    def test_help(self):
        result = run_cli('--help')
        self.assertEqual(result.returncode, 0)
        self.assertIn('--input', result.stdout)

    def test_file_and_malformed_errors(self):
        for file in ('inputs/does-not-exist.json', 'inputs/malformed-input.txt'):
            with self.subTest(file=file):
                result = run_cli('--input', file)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, '')
                self.assertIn('error:', result.stderr)
                self.assertNotIn('Traceback', result.stderr)

    def test_primary_exact_diagnostics(self):
        result = run_cli('--input', 'inputs/primary.json')
        self.assertEqual(result.returncode, 1)
        report = json.loads(result.stdout)
        self.assertEqual(report['summary'], dict(profiles=7, valid=2, invalid=5, errors=13, warnings=2))
        expected = [[], [], [('max_duration_minutes', 'type'), ('name', 'duplicate'), ('name', 'invalid'), ('schedule', 'invalid')], [('auth.token_ref', 'secret')], [('auth.token_ref', 'not_allowed'), ('target', 'invalid')], [('exclude_paths[1]', 'invalid'), ('exclude_paths[2]', 'duplicate'), ('target', 'invalid')], [('api_key', 'secret'), ('auth.token_ref', 'missing'), ('schedule', 'missing')]]
        for i, profile in enumerate(report['profiles']):
            self.assertEqual([(e['path'], e['code']) for e in profile['errors']], [(f'$.profiles[{i}].{p}', c) for p, c in expected[i]])
        self.assertEqual([len(p['warnings']) for p in report['profiles']], [0, 1, 0, 0, 0, 0, 1])
        self.assertEqual(result.stderr, '')

    def test_secondary_reuses_policy(self):
        result = run_cli('--input', 'inputs/secondary.json')
        self.assertEqual(result.returncode, 1)
        report = json.loads(result.stdout)
        self.assertEqual(report['summary'], dict(profiles=4, valid=1, invalid=3, errors=5, warnings=1))
        expected = [[], [('max_duration_minutes', 'invalid'), ('target', 'invalid')], [('auth.recording_id', 'not_allowed'), ('max_duration_minutes', 'type')], [('auth.token', 'secret')]]
        for i, p in enumerate(report['profiles']):
            self.assertEqual([(e['path'], e['code']) for e in p['errors']], [(f'$.profiles[{i}].{path}', code) for path, code in expected[i]])
        self.assertEqual(report['profiles'][3]['warnings'][0]['path'], '$.profiles[3].auth.token')

    def test_duration_boundaries_and_types(self):
        for value, code in ((5, None), (240, None), (4, 'invalid'), (241, 'invalid'), (True, 'type'), (45.0, 'type'), ('45', 'type'), (None, 'type')):
            with self.subTest(value=value):
                data = batch()
                data['profiles'][0]['max_duration_minutes'] = value
                self.assertEqual(self.codes(data), [] if code is None else [('$.profiles[0].max_duration_minutes', code)])

    def test_case_insensitive_duplicate(self):
        data = batch()
        data['profiles'].append(copy.deepcopy(data['profiles'][0]))
        data['profiles'][1]['name'] = 'API-Nightly'
        self.assertEqual(self.codes(data), [('$.profiles[1].name', 'duplicate'), ('$.profiles[1].name', 'invalid')])

    def test_hostname_not_url_substring(self):
        for url, valid in [('https://API.NORTH.EXAMPLE.TEST:8443/', True), ('https://api.north.example.test@relay.example/', False), ('https://api.north.example.test.evil/', False), ('https://north.example.test/', False), ('http://api.north.example.test/', False), ('https://api.north.example.test:bad/', False)]:
            with self.subTest(url=url):
                data = batch()
                data['profiles'][0]['target'] = url
                self.assertEqual(validate_profiles(data)['profiles'][0]['valid'], valid)

    def test_secrets_at_depth_and_in_name(self):
        data = batch()
        secret = 'demo_tok_private'
        p = data['profiles'][0]
        p['name'] = secret
        p['extra'] = {'nested': [secret]}
        p['auth'] = {'type': 'none', 'token_ref': secret}
        report = validate_profiles(data)
        self.assertNotIn(secret, json.dumps(report))
        self.assertEqual(report['profiles'][0]['name'], '[REDACTED]')
        self.assertEqual([code for _, code in self.codes(data)], ['secret'] * 3)
        self.assertEqual(len(report['profiles'][0]['warnings']), 1)

    def test_cli_secret_redaction(self):
        data = batch()
        data['profiles'][0]['name'] = 'demo_tok_private'
        result = self.cli_data(data)
        self.assertEqual(result.returncode, 1)
        self.assertNotIn('demo_tok_private', result.stdout + result.stderr)

    def test_redaction_preserves_diagnostic_codes(self):
        data = batch()
        data['policy']['secret_prefixes'] = ['ty']
        data['profiles'][0]['name'] = 'type'
        data['profiles'][0]['max_duration_minutes'] = True
        result = self.cli_data(data)
        self.assertEqual(result.returncode, 1)
        profile = json.loads(result.stdout)['profiles'][0]
        self.assertEqual(profile['name'], '[REDACTED]')
        self.assertEqual([(e['path'], e['code']) for e in profile['errors']], [
            ('$.profiles[0].max_duration_minutes', 'type'),
            ('$.profiles[0].name', 'secret'),
        ])

    def test_redaction_does_not_rewrite_its_own_marker(self):
        data = batch()
        data['policy']['secret_prefixes'] = ['demo_tok_', 'RED']
        data['profiles'][0]['name'] = 'demo_tok_private'
        data['profiles'][0]['extra'] = 'RED'
        profile = validate_profiles(data)['profiles'][0]
        self.assertEqual(profile['name'], '[REDACTED]')
        self.assertNotIn('demo_tok_private', json.dumps(profile))

    def test_missing_wrong_types_and_auth_skip(self):
        data = batch()
        data['profiles'] = [{}]
        self.assertEqual(len(self.codes(data)), 5)
        for auth in ({'token_ref': 123}, {'type': 123, 'recording_id': 'bad'}, {'type': 'bad', 'token_ref': 'bad'}):
            data = batch()
            data['profiles'][0]['auth'] = auth
            self.assertEqual(len(self.codes(data)), 1)
            self.assertEqual(self.codes(data)[0][0], '$.profiles[0].auth.type')
        data = batch()
        data['profiles'][0]['auth'] = []
        self.assertEqual(self.codes(data), [('$.profiles[0].auth', 'type')])

    def test_auth_formats_and_unused_fields(self):
        for auth, expected in [({'type': 'bearer'}, 'missing'), ({'type': 'bearer', 'token_ref': 'bad'}, 'invalid'), ({'type': 'recorded', 'recording_id': 'rec-0001'}, None), ({'type': 'recorded', 'recording_id': 'rec-001'}, 'invalid'), ({'type': 'none', 'token_ref': 123}, 'not_allowed')]:
            data = batch()
            data['profiles'][0]['auth'] = auth
            codes = self.codes(data)
            self.assertEqual([c for _, c in codes], [] if expected is None else [expected])

    def test_schedule_boundaries(self):
        for value, valid in [('daily 00:00', True), ('weekly Sun 23:59', True), ('daily 24:00', False), ('daily 12:60', False), ('daily 7:30', False), ('weekly sun 01:00', False), ('daily 02:30\n', False)]:
            data = batch()
            data['profiles'][0]['schedule'] = value
            self.assertEqual(validate_profiles(data)['profiles'][0]['valid'], valid)

    def test_excludes_and_warning_only(self):
        data = batch()
        p = data['profiles'][0]
        p['owner'] = 'team'
        self.assertTrue(validate_profiles(data)['profiles'][0]['valid'])
        p['exclude_paths'] = ['/admin', 'static', '/admin', False]
        self.assertEqual(self.codes(data), [('$.profiles[0].exclude_paths[1]', 'invalid'), ('$.profiles[0].exclude_paths[2]', 'duplicate'), ('$.profiles[0].exclude_paths[3]', 'type')])

    def test_deterministic_and_no_mutation(self):
        data = batch()
        data['profiles'][0].update({'z': 1, 'a': 2})
        original = copy.deepcopy(data)
        self.assertEqual(validate_profiles(data), validate_profiles(data))
        self.assertEqual(data, original)

    def cli_data(self, data):
        with tempfile.TemporaryDirectory() as directory:
            file = pathlib.Path(directory) / 'input.json'
            file.write_text(json.dumps(data), encoding='utf-8')
            return run_cli('--input', str(file))

    def test_valid_and_empty_exit_zero(self):
        self.assertEqual(self.cli_data(batch()).returncode, 0)
        data = batch()
        data['profiles'] = []
        result = self.cli_data(data)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(json.loads(result.stdout)['summary'], dict(profiles=0, valid=0, invalid=0, errors=0, warnings=0))

    def test_invalid_envelopes_exit_two(self):
        for data in ([], {}, {'policy': {}, 'profiles': []}, {'policy': {'allowed_suffixes': ['bad'], 'secret_prefixes': []}, 'profiles': []}, {'policy': batch()['policy'], 'profiles': [None]}):
            with self.subTest(data=data):
                result = self.cli_data(data)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, '')
                self.assertIn('error:', result.stderr)


if __name__ == '__main__':
    unittest.main()
