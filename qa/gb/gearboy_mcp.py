"""Minimal MCP (JSON-RPC over stdio) client for Gearboy's headless MCP server.

    with Gearboy(rom) as gb:
        gb.call('debug_continue')
        print(gb.call('read_memory', area='wram0', offset=0, size=16))

Gearboy gives an independent third implementation (and a real debugger: symbols,
breakpoints, trace, profiler, call stack) next to PyBoy and SameBoy."""
import json
import os
import subprocess

from .emu import ROOT, default_rom

GEARBOY = os.environ.get('GEARBOY_BIN', '/home/user/gbdev/Gearboy/platforms/linux/gearboy')
SDL3_LIB = os.environ.get('SDL3_LIB', '/opt/sdl3/lib')


class Gearboy:
    def __init__(self, rom=None, sym=None, extra=()):
        rom = rom or default_rom()
        sym = sym or rom[:-4] + '.sym'
        env = dict(os.environ, LD_LIBRARY_PATH=SDL3_LIB + ':' + os.environ.get('LD_LIBRARY_PATH', ''))
        self.p = subprocess.Popen([GEARBOY, '--mcp-stdio', '--headless', '--portable', *extra, rom, sym],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                  text=True, env=env, cwd=os.path.dirname(GEARBOY))
        self.n = 0
        self.rpc('initialize', {'protocolVersion': '2024-11-05', 'capabilities': {},
                                'clientInfo': {'name': 'polished-qa', 'version': '1'}})
        self.notify('notifications/initialized')

    def _send(self, msg):
        self.p.stdin.write(json.dumps(msg) + '\n')
        self.p.stdin.flush()

    def notify(self, method, params=None):
        self._send({'jsonrpc': '2.0', 'method': method, **({'params': params} if params else {})})

    def rpc(self, method, params=None):
        self.n += 1
        self._send({'jsonrpc': '2.0', 'id': self.n, 'method': method, 'params': params or {}})
        while True:
            line = self.p.stdout.readline()
            if not line:
                raise RuntimeError('Gearboy MCP server closed')
            msg = json.loads(line)
            if msg.get('id') == self.n:
                if 'error' in msg:
                    raise RuntimeError(msg['error'])
                return msg['result']

    def tools(self):
        return {t['name']: t for t in self.rpc('tools/list')['tools']}

    def call(self, tool, /, **args):
        res = self.rpc('tools/call', {'name': tool, 'arguments': args})
        out = []
        for c in res.get('content', []):
            if c.get('type') == 'text':
                out.append(c['text'])
        return out[0] if len(out) == 1 else out

    def __enter__(self):
        return self

    def __exit__(self, *a):
        try:
            self.p.stdin.close()
            self.p.terminate()
        except Exception:
            pass
