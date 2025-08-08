import argparse
import subprocess
import threading
import time
import queue
import re
import json
import os
import glob
import fnmatch
from dataclasses import dataclass, field
from typing import List, Callable, Optional, Dict, Any, Tuple

UCI_BESTMOVE_RE = re.compile(r'^bestmove\s+([a-h][1-8][a-h][1-8][qrbn]?)')
ID_RE = re.compile(r'^(id)\s+(name|author)\s+.+', re.IGNORECASE)
OPTION_RE = re.compile(r'^option\s+name\s+.+', re.IGNORECASE)

@dataclass
class StageResult:
    name: str
    ok: bool
    duration: float
    detail: str = ''
    fail_type: Optional[str] = None

@dataclass
class EngineReport:
    engine_path: str
    stages: List[StageResult] = field(default_factory=list)
    launch_error: Optional[str] = None
    total_duration: float = 0.0

    @property
    def engine_name(self) -> str:
        return os.path.basename(self.engine_path)

    def critical_pass(self) -> bool:
        # Define minimal required stages
        needed = { 'launch', 'uci_handshake', 'isready', 'first_move_movetime' }
        got = { s.name for s in self.stages if s.ok }
        return needed.issubset(got)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'engine': self.engine_name,
            'path': self.engine_path,
            'critical_pass': self.critical_pass(),
            'total_duration': self.total_duration,
            'stages': [s.__dict__ for s in self.stages],
        }

class UCIEngine:
    _all_lines: List[str]
    def __init__(self, path: str):
        self.path = path
        self.proc: Optional[subprocess.Popen] = None
        self._reader_thread: Optional[threading.Thread] = None
        self._out_queue: "queue.Queue[str]" = queue.Queue()
        self._alive = False
        # full transcript of every stdout line
        self._all_lines = []

    def start(self) -> None:
        self.proc = subprocess.Popen([self.path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)
        self._alive = True
        self._reader_thread = threading.Thread(target=self._reader, daemon=True)
        self._reader_thread.start()

    def _reader(self):
        assert self.proc and self.proc.stdout
        for line in self.proc.stdout:
            clean = line.rstrip('\r\n')
            self._all_lines.append(clean)
            self._out_queue.put(clean)
        self._alive = False

    def send(self, line: str):
        if not self.proc or not self.proc.stdin:
            return
        self.proc.stdin.write(line + '\n')
        self.proc.stdin.flush()

    def read_lines_until(self, predicate: Callable[[str], bool], timeout: float) -> Tuple[bool, List[str]]:
        deadline = time.time() + timeout
        lines: List[str] = []
        while time.time() < deadline:
            try:
                remaining = deadline - time.time()
                l = self._out_queue.get(timeout=remaining)
                lines.append(l)
                if predicate(l):
                    return True, lines
            except queue.Empty:
                break
        return False, lines

    def collect_for(self, timeout: float) -> List[str]:
        deadline = time.time() + timeout
        lines: List[str] = []
        while time.time() < deadline:
            try:
                l = self._out_queue.get(timeout=0.05)
                lines.append(l)
            except queue.Empty:
                break
        return lines

    def terminate(self):
        if self.proc and self.proc.poll() is None:
            try:
                self.send('quit')
                time.sleep(0.2)
            except Exception:
                pass
            try:
                self.proc.terminate()
            except Exception:
                pass
            try:
                self.proc.kill()
            except Exception:
                pass

# ---- Test stages ----

def stage_launch(engine: UCIEngine, ctx: dict) -> StageResult:
    t0 = time.time()
    try:
        engine.start()
        time.sleep(0.5)
        ok = engine.proc is not None and engine.proc.poll() is None
        return StageResult('launch', ok, time.time() - t0, detail='' if ok else 'Process not alive', fail_type=None if ok else 'CRASH')
    except Exception as e:
        return StageResult('launch', False, time.time() - t0, detail=str(e), fail_type='CRASH')


def stage_uci_handshake(engine: UCIEngine, ctx: dict) -> StageResult:
    t0 = time.time()
    engine.send('uci')
    lines: List[str] = []
    uciok = False
    deadline = t0 + ctx['timeouts']['uci_handshake']
    while time.time() < deadline:
        chunk = engine.collect_for(0.1)
        lines.extend(chunk)
        if any(l == 'uciok' for l in lines):
            uciok = True
            break
    ok = uciok
    detail = '\n'.join(lines[-10:])
    fail_type = None
    if not ok:
        # classify traceback
        if any('Traceback (most recent call last):' in l for l in lines):
            fail_type = 'TRACEBACK'
        else:
            fail_type = 'TIMEOUT'
    return StageResult('uci_handshake', ok, time.time() - t0, detail=detail, fail_type=fail_type)


def stage_isready(engine: UCIEngine, ctx: dict) -> StageResult:
    t0 = time.time()
    engine.send('isready')
    ok, lines = engine.read_lines_until(lambda l: l == 'readyok', timeout=ctx['timeouts']['isready'])
    return StageResult('isready', ok, time.time() - t0, detail=';'.join(lines[-5:]), fail_type=None if ok else 'TIMEOUT')


def stage_newgame(engine: UCIEngine, ctx: dict) -> StageResult:
    t0 = time.time()
    engine.send('ucinewgame')
    engine.send('isready')
    ok, lines = engine.read_lines_until(lambda l: l == 'readyok', timeout=ctx['timeouts']['newgame'])
    return StageResult('newgame', ok, time.time() - t0, detail=';'.join(lines[-5:]), fail_type=None if ok else 'TIMEOUT')


def _move_stage(engine: UCIEngine, name: str, go_cmd: str, timeout: float) -> StageResult:
    t0 = time.time()
    engine.send('position startpos')
    engine.send(go_cmd)
    ok, lines = engine.read_lines_until(lambda l: l.startswith('bestmove'), timeout=timeout)
    detail = ';'.join(lines[-8:])
    if not ok:
        return StageResult(name, False, time.time() - t0, detail=detail, fail_type='NO_BESTMOVE')
    # validate bestmove
    best_line = next((l for l in lines if l.startswith('bestmove')), '')
    if not UCI_BESTMOVE_RE.match(best_line):
        return StageResult(name, False, time.time() - t0, detail=best_line, fail_type='ILLEGAL_MOVE')
    return StageResult(name, True, time.time() - t0, detail=best_line)


def stage_first_move_movetime(engine: UCIEngine, ctx: dict) -> StageResult:
    return _move_stage(engine, 'first_move_movetime', 'go movetime 1000', ctx['timeouts']['first_move_movetime'])


def stage_first_move_timecontrol(engine: UCIEngine, ctx: dict) -> StageResult:
    # Provide small clock so engine must respond promptly
    return _move_stage(engine, 'first_move_timecontrol', 'go wtime 2000 btime 2000 winc 0 binc 0', ctx['timeouts']['first_move_timecontrol'])


def stage_multi_sequence(engine: UCIEngine, ctx: dict) -> StageResult:
    t0 = time.time()
    moves_needed = 3
    moves_got = 0
    transcript: List[str] = []
    for i in range(moves_needed):
        engine.send('position startpos moves ' + ' '.join(ctx['sequence_moves'][:2*i]))
        engine.send('go movetime 500')
        ok, lines = engine.read_lines_until(lambda l: l.startswith('bestmove'), timeout=ctx['timeouts']['multi_sequence_single'])
        transcript.extend(lines)
        if not ok:
            return StageResult('multi_sequence', False, time.time()-t0, detail='Missing move {}'.format(i+1), fail_type='NO_BESTMOVE')
        moves_got += 1
        best_line = next((l for l in lines if l.startswith('bestmove')), '')
        m_match = UCI_BESTMOVE_RE.match(best_line)
        if not m_match:
            return StageResult('multi_sequence', False, time.time()-t0, detail='Bad move line '+best_line, fail_type='ILLEGAL_MOVE')
        ctx['sequence_moves'].append(m_match.group(1))
    return StageResult('multi_sequence', moves_got == moves_needed, time.time()-t0, detail='Moves='+','.join(ctx['sequence_moves']))


def stage_graceful_quit(engine: UCIEngine, ctx: dict) -> StageResult:
    t0 = time.time()
    engine.send('quit')
    timeout = ctx['timeouts']['graceful_quit']
    while time.time() - t0 < timeout:
        if engine.proc and engine.proc.poll() is not None:
            return StageResult('graceful_quit', True, time.time()-t0, detail='Exit code {}'.format(engine.proc.returncode))
        time.sleep(0.05)
    return StageResult('graceful_quit', False, time.time()-t0, detail='Did not exit', fail_type='TIMEOUT')

TEST_STAGES: List[Callable[[UCIEngine, dict], StageResult]] = [
    stage_launch,
    stage_uci_handshake,
    stage_isready,
    stage_newgame,
    stage_first_move_movetime,
    stage_first_move_timecontrol,
    stage_multi_sequence,
    stage_graceful_quit,
]


def run_engine_tests(path: str, timeouts: Dict[str, float]) -> EngineReport:
    report = EngineReport(engine_path=path)
    ctx = {
        'timeouts': timeouts,
        'sequence_moves': ['e2e4', 'e7e5', 'g1f3'],  # seeds used progressively
    }
    t0_total = time.time()
    engine = UCIEngine(path)
    for stage in TEST_STAGES:
        res = stage(engine, ctx)
        report.stages.append(res)
        if stage == stage_launch and not res.ok:
            break
        # If engine process died, stop further stages
        if engine.proc and engine.proc.poll() is not None and stage != stage_graceful_quit:
            break
    engine.terminate()
    report.total_duration = time.time() - t0_total
    # Write transcript log
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    try:
        with open(os.path.join(log_dir, os.path.basename(path) + '.log'), 'w', encoding='utf-8') as lf:
            lf.write('\n'.join(engine._all_lines))
    except Exception:
        pass
    return report


def discover_engines(directory: str, includes: List[str], excludes: List[str]) -> List[str]:
    paths: List[str] = []
    for pattern in includes:
        paths.extend(glob.glob(os.path.join(directory, pattern)))
    # deduplicate
    uniq = []
    for p in paths:
        if p not in uniq:
            uniq.append(p)
    # filter excludes
    def excluded(p: str) -> bool:
        base = os.path.basename(p)
        for ex in excludes:
            if fnmatch.fnmatch(base, ex):
                return True
        return False
    return [p for p in uniq if os.path.isfile(p) and not excluded(p)]


def write_reports(reports: List[EngineReport], json_path: str, md_path: str):
    data = [r.to_dict() for r in reports]
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    # Markdown
    lines = [f'# Engine Test Report', '', f'Total engines: {len(reports)}', '']
    pass_count = sum(1 for r in reports if r.critical_pass())
    lines.append(f'Critical PASS: {pass_count}/{len(reports)}')
    lines.append('')
    for r in reports:
        lines.append(f'## Engine: {r.engine_name}')
        lines.append(f'Path: `{r.engine_path}`')
        lines.append(f'Result: {"PASS" if r.critical_pass() else "FAIL"} (critical tests)')
        lines.append(f'Total Duration: {r.total_duration:.2f}s')
        lines.append('')
        lines.append('| Stage | OK | Time (s) | Detail |')
        lines.append('|-------|----|----------|--------|')
        for s in r.stages:
            lines.append(f'| {s.name} | {"✅" if s.ok else "❌"} | {s.duration:.2f} | {s.fail_type+":" if s.fail_type else ""}{s.detail.replace("|","/")[:120]} |')
        lines.append('')
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def main():
    parser = argparse.ArgumentParser(description='Batch test UCI chess engines for basic compatibility.')
    parser.add_argument('--dir', default='Functioning_Engines_20250807', help='Directory containing engine executables')
    parser.add_argument('--include', action='append', default=['*.exe'], help='Glob pattern to include (repeatable)')
    parser.add_argument('--exclude', action='append', default=[], help='Glob pattern to exclude (repeatable)')
    parser.add_argument('--parallel', type=int, default=1, help='Number of engines to test in parallel (currently sequential enforced)')
    parser.add_argument('--timeout-scale', type=float, default=1.0, help='Multiply all timeouts by this factor')
    parser.add_argument('--json', help='Override JSON report path')
    parser.add_argument('--md', help='Override Markdown report path')
    parser.add_argument('--max-move-ms', type=int, default=1500, help='Hard cap wait for single move (ms)')
    args = parser.parse_args()

    base_timeouts = {
        'uci_handshake': 3.0,
        'isready': 2.0,
        'newgame': 2.0,
        'first_move_movetime': 2.0,
        'first_move_timecontrol': 3.0,
        'multi_sequence_single': 2.0,
        'graceful_quit': 2.0,
    }
    timeouts = {k: v * args.timeout_scale for k, v in base_timeouts.items()}

    engines = discover_engines(args.dir, args.include, args.exclude)
    if not engines:
        print('No engines found in', args.dir)
        return
    print(f'Found {len(engines)} engines')

    reports: List[EngineReport] = []
    for eng in engines:
        print(f'Testing {os.path.basename(eng)}...')
        rep = run_engine_tests(eng, timeouts)
        reports.append(rep)
        print(f'  -> {"PASS" if rep.critical_pass() else "FAIL"}')

    timestamp = time.strftime('%Y%m%d_%H%M%S')
    json_path = f'results/{args.json}' or f'results/engine_test_report_{timestamp}.json'
    md_path = f'results/{args.md}' or f'results/engine_test_report_{timestamp}.md'
    write_reports(reports, json_path, md_path)
    print('Reports written:')
    print(' JSON:', json_path)
    print(' MD  :', md_path)

if __name__ == '__main__':
    main()
