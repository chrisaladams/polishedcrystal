"""Write results.json and summary.md for a run."""
import json
import os

from qa import coverage


def write(out_root, info, results):
    with open(os.path.join(out_root, 'results.json'), 'w') as f:
        json.dump({'meta': info, 'results': results}, f, indent=1)
    lines = ['# QA run', '',
             '- ROM: `%s` sha1 `%s` (%s, %d bytes)' % (info['rom']['path'], info['rom']['sha1'], info['rom']['header']['cartridge'],
                                                   info['rom']['header']['rom_bytes']),
             '- Commit: `%s`%s on `%s`' % (info['git']['commit'], ' (working tree dirty)' if info['git']['dirty'] else '', info['git']['branch']),
             '- Tools: ' + ', '.join('%s %s' % kv for kv in info['tools'].items()),
             '- Seed: %s   Suite: %s   Backend option: %s   SameBoy models: %s' % (info['seed'], info['suite'], info['backend_option'], info['models']),
             '- Hardware: %s' % info['hardware_configuration'], '',
             '| Result | Test | Backend | Seconds | Provenance |', '|---|---|---|---|---|']
    for r in sorted(results, key=lambda r: (r['status'] != 'fail', r['status'] != 'error', r['name'])):
        be = r['backend'] + (' ' + r['model'] if r['model'] else '')
        lines.append('| %s | %s | %s | %s | %s |' % (r['status'].upper(), r['name'], be, r['seconds'], r['provenance'] or '-'))
    bad = [r for r in results if r['status'] in ('fail', 'error')]
    if bad:
        lines += ['', '## Failures', '']
        for r in bad:
            lines.append('### %s (%s)' % (r['name'], r['backend']))
            for fmsg in r['failures']:
                lines.append('- ' + fmsg)
            if r['error']:
                lines += ['```', r['error'].strip()[-1500:], '```']
            if r['artifacts']:
                lines.append('Artifacts: ' + ', '.join(os.path.relpath(a, out_root) for a in r['artifacts']))
    lines += ['', coverage.table(results)]
    with open(os.path.join(out_root, 'summary.md'), 'w') as f:
        f.write('\n'.join(lines) + '\n')
