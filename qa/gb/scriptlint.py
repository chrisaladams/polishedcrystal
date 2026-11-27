"""Static lint of map scripts: control flow from every map callback must finish with
`endcallback`. A callback that reaches `end` pops the saved caller position and resumes
executing from a stale script pointer (see docs/qa-report.md, F3)."""
import glob
import os
import re

from .emu import ROOT

BRANCH = re.compile(r'^\s+(sjump|ifequal|ifnotequal|iftrue|iffalse|ifgreater|ifless|ifequalfwd|ifnotequalfwd|iftruefwd|iffalsefwd|'
                    r'ifgreaterfwd|iflessfwd|if_equal|if_not_equal|if_greater_than|if_less_than|sdefer)\w*\s+(?:[^,;]*,\s*)?(\.?\w+)')
TERMINALS = ('end', 'endcallback', 'endtext', 'waitendtext', 'closetext')


def parse_file(path):
    """labels: {full_name: [(lineno, text)]}; local labels (.x) are scoped to their global label."""
    labels, order, cur, glob_ = {}, [], None, ''
    for i, line in enumerate(open(path, encoding='utf-8')):
        m = re.match(r'^(\.?\w+):{0,2}\s*(;.*)?$', line.rstrip('\n'))
        if re.match(r'^[\w.]+:{1,2}\s*(;.*)?$', line) or (m and line.startswith('.')):
            name = line.split(':')[0].split(';')[0].strip()
            if name.startswith('.'):
                full = glob_ + name
            else:
                glob_ = name
                full = name
            cur = full
            labels[cur] = []
            order.append(cur)
        elif cur is not None:
            labels[cur].append((i + 1, line.rstrip('\n')))
    return labels, order


def callbacks(path):
    """(kind, full label, line) for each `callback` in the map header."""
    out, glob_ = [], ''
    for i, line in enumerate(open(path, encoding='utf-8')):
        m0 = re.match(r'^([A-Za-z_]\w*):{1,2}', line)
        if m0:
            glob_ = m0.group(1)
        m = re.match(r'\s+callback\s+(\w+),\s*(\.?\w+)', line)
        if m:
            t = m.group(2)
            out.append((m.group(1), glob_ + t if t.startswith('.') else t, i + 1))
    return out


def _owner(lab):
    return lab.split('.')[0]


def lint_map(path):
    """List of (callback kind, label, line of the `end`) problems in one map file."""
    labels, order = parse_file(path)
    problems = []
    for kind, target, lineno in callbacks(path):
        seen, stack = set(), [target]
        while stack:
            lab = stack.pop()
            if lab in seen or lab not in labels:
                continue
            seen.add(lab)
            falls = True
            for ln, text in labels[lab]:
                s = text.split(';')[0].strip()
                if not s:
                    continue
                m = BRANCH.match(text)
                if m:
                    t = m.group(2)
                    stack.append(_owner(lab) + t if t.startswith('.') else t)
                tok = s.split()[0]
                if tok == 'end':
                    problems.append((kind, lab, ln))
                    falls = False
                    break
                if tok in ('endcallback', 'sjump', 'jumptext') or tok.startswith('jump'):
                    falls = False
                    break
            if falls and lab in order:
                i = order.index(lab)
                if i + 1 < len(order):
                    stack.append(order[i + 1])
    return problems


def lint_all():
    out = {}
    for path in sorted(glob.glob(os.path.join(ROOT, 'maps', '*.asm'))):
        p = lint_map(path)
        if p:
            out[os.path.basename(path)] = p
    return out
