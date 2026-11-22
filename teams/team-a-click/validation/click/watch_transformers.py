"""Notify the originating Orca conversation when the remote evaluation settles.

Runs in a dedicated Orca shell, not an agent. Never changes the evaluation.
Delivery receipts mean prompt acceptance, not that a result was already reported.
"""

import argparse
import datetime
import fcntl
import hashlib
import json
from pathlib import Path
import subprocess
import time


REMOTE_ROOT = "/workspace/transformers-bf16-20261120"
def snapshot_script(remote_root):
    return f"""import json
from pathlib import Path
p=Path({remote_root!r})
out={{'status':json.loads((p/'results/status.json').read_text())}}
t=p/'results/tracking.json'
if t.exists(): out['tracking']=json.loads(t.read_text())
print(json.dumps(out))
"""


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def save(path, value):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    temporary.replace(path)


def event(snapshot, timestamp):
    status = snapshot["status"]
    if status["state"] in ("COMPLETE", "STOPPED"):
        return {"kind": status["state"], "status": status}
    heartbeat = snapshot.get("tracking", {}).get("updated_utc")
    if heartbeat:
        last = datetime.datetime.fromisoformat(heartbeat.replace("Z", "+00:00")).timestamp()
        if timestamp - last > 180:
            return {"kind": "TRACKING_STALE", "last_heartbeat": heartbeat, "status": status}
    return None


def event_key(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def send(args, value, folder):
    # Read before sending and verify that this is still the original Codex pane.
    shown = subprocess.run(
        [args.orca, "terminal", "show", "--terminal", args.target, "--json"],
        text=True, capture_output=True, timeout=15, check=True,
    )
    terminal = json.loads(shown.stdout)["result"]["terminal"]
    if not (terminal.get("connected") and terminal.get("writable")
            and terminal.get("agentIdentity") == "codex"
            and terminal.get("worktreeId") == args.worktree):
        raise RuntimeError("Original conversation is unavailable; refusing another target")
    subprocess.run(
        [args.orca, "terminal", "read", "--terminal", args.target, "--screen", "--json"],
        text=True, capture_output=True, timeout=15, check=True,
    )
    prompt = (
        "[사용자가 요청한 CLIcK 평가 자동 알림] "
        "tailab의 Transformers BF16 평가에서 상태 변화가 감지됐습니다. "
        "원격 상태를 재확인하고 이 대화에 한국어로 결과를 보고해주세요. "
        "COMPLETE이면 report/README.md와 report/results.json을 확인해 "
        "모델별 결과 및 Lighteval↔입력 정렬 harness 일치 여부를 요약하고 결과를 로컬에 보관하세요. "
        "STOPPED 또는 추적/연결 오류이면 중단 단계, 완료량, 오류와 다음 조치를 먼저 보고하세요. "
        "이 알림은 평가 조건 변경이나 외부 PR 게시를 요청하지 않습니다. "
        f"작업 구분: {args.description}. "
        f"컨테이너 click-vllm-20261120, 실행 폴더 {args.remote_root}. "
        f"감지 기록: {folder / 'event.json'}\n"
        + json.dumps(value, ensure_ascii=False)
    )
    return subprocess.run(
        [args.orca, "terminal", "send", "--terminal", args.target,
         "--text", prompt, "--enter", "--wait-submit", "10", "--json"],
        text=True, capture_output=True, timeout=30,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--orca", default="orca")
    parser.add_argument("--target", required=True)
    parser.add_argument("--worktree", required=True)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--remote-root", default=REMOTE_ROOT)
    parser.add_argument("--description", default="CLIcK Qwen·Kanana Transformers BF16 전체 평가")
    args = parser.parse_args()
    args.state_dir.mkdir(parents=True, exist_ok=True)
    lock = (args.state_dir / "watcher.lock").open("w")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    failures, outage = 0, 0
    while True:
        value = None
        try:
            result = subprocess.run(
                ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
                 "-o", "ServerAliveInterval=10", "-o", "ServerAliveCountMax=2",
                 "tailab", "docker exec -i click-vllm-20261120 /workspace/.venv/bin/python -"],
                input=snapshot_script(args.remote_root), text=True, capture_output=True, timeout=25, check=True,
            )
            snapshot = json.loads(result.stdout)
            failures = 0
            value = event(snapshot, time.time())
            save(args.state_dir / "watcher-status.json", {
                "state": "WATCHING", "checked_utc": now(), "interval_seconds": 30,
                "target": args.target, "remote": snapshot,
            })
        except Exception as error:
            if failures == 0:
                outage += 1
            failures += 1
            save(args.state_dir / "watcher-status.json", {
                "state": "CHECK_FAILED", "checked_utc": now(),
                "consecutive_failures": failures, "error": str(error),
            })
            if failures >= 3:
                value = {"kind": "MONITOR_CONNECTION_ERROR", "outage": outage}
        if value:
            folder = args.state_dir / "events" / event_key(value)
            folder.mkdir(parents=True, exist_ok=True)
            attempted = folder / "delivery-attempt.json"
            if not attempted.exists():
                save(folder / "event.json", value)
                # Persist before dispatch: never duplicate an ambiguously accepted prompt.
                save(attempted, {"attempted_utc": now(), "target": args.target})
                try:
                    result = send(args, value, folder)
                    receipt = {"returncode": result.returncode, "stdout": result.stdout,
                               "stderr": result.stderr, "finished_utc": now()}
                except Exception as error:
                    receipt = {"error": str(error), "finished_utc": now(),
                               "delivery": "unconfirmed; do not resend without inspection"}
                save(folder / "delivery-receipt.json", receipt)
                print(json.dumps({"event": value, "receipt": receipt}, ensure_ascii=False), flush=True)
            if value["kind"] == "COMPLETE":
                save(args.state_dir / "watcher-status.json", {
                    "state": "FINISHED", "checked_utc": now(), "event_dir": str(folder),
                    "note": "Inspect delivery-receipt.json; prompt acceptance is not a completed report.",
                })
                return
        time.sleep(30)


if __name__ == "__main__":
    main()
