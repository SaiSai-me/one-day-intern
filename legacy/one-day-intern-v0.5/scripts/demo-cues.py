#!/usr/bin/env python3
"""Return one due NPC line; the runner sends it and records a real receipt."""
import argparse
import json
from datetime import datetime
from pathlib import Path


def due(state, at, script):
    demo = state.get('demo', {})
    if state.get('mode') != 'live_demo' or demo.get('pacing') != 'cue' or state.get('paused') or state.get('status') != 'running':
        return None
    stage = demo.get('stage')
    entered = demo.get('stage_entered_at') or demo.get('live_started_at')
    if not entered:
        return None
    elapsed = (datetime.fromisoformat(at) - datetime.fromisoformat(entered)).total_seconds()
    receipts = state['artifacts']['action_receipts']
    for i, line in enumerate(script.get(stage, [])):
        key = f'demo.cue.{stage}.{i}'
        receipt = receipts.get(key)
        if receipt and receipt.get('status') == 'done':
            continue
        if receipt:
            return {'key': key, 'reconcile': True}  # Unknown outcome must not be resent.
        if elapsed >= line['after']:
            return {'key': key, **line}
        return None
    return None


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--state', required=True, type=Path)
    p.add_argument('--at', required=True)
    args = p.parse_args()
    script = json.loads((Path(__file__).resolve().parents[1] / 'assets/live-demo-cues.json').read_text())
    print(json.dumps(due(json.loads(args.state.read_text()), args.at, script), ensure_ascii=False))
