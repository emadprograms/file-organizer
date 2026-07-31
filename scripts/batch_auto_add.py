"""
Batch runner that processes houses sequentially using auto_add.py.
Reads the manifest from .planning/batch/, processes each pending house
with an addition PDF, and updates the manifest after each house.

Usage:
    python scripts/batch_auto_add.py "Safra D" [--start-from 628]
"""
import argparse
import json
import os
import sys
import subprocess
import time
import re
from pathlib import Path
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')


def slugify(area: str) -> str:
    return area.lower().replace(" ", "_")


def load_manifest(manifest_path: Path) -> dict:
    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_manifest(manifest_path: Path, data: dict) -> None:
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_key_tracker(tracker_path: Path) -> dict:
    if tracker_path.exists():
        try:
            with open(tracker_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {}

def save_key_tracker(tracker_path: Path, data: dict) -> None:
    with open(tracker_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Batch auto_add runner")
    parser.add_argument("area", help="Area name (e.g. 'Safra D')")
    parser.add_argument("--start-from", type=str, default=None,
                        help="House ID to start from (e.g. 628). Skips all houses before this ID.")
    parser.add_argument("--retry-failed", action="store_true",
                        help="Retry houses that were marked as failed/timeout in the manifest.")
    parser.add_argument("--manifest-dir", type=Path,
                        default=Path("C:/Users/Emad/Documents/GitHub/file-organizer/.planning/batch"),
                        help="Directory containing manifest files")
    parser.add_argument("--timeout", type=int, default=1800,
                        help="Timeout per house in seconds (default: 1800 = 30 min)")

    args = parser.parse_args()

    manifest_path = args.manifest_dir / f"{slugify(args.area)}_manifest.json"
    if not manifest_path.exists():
        print(f"ERROR: Manifest not found at {manifest_path}")
        print(f"Run /gsd-batch-yaml \"{args.area}\" first to generate the manifest.")
        return 1

    manifest = load_manifest(manifest_path)
    houses = manifest.get("houses", [])
    additions_dir = manifest.get("additions_dir", f"D:/{args.area} additions")
    project_root = Path(__file__).resolve().parent.parent

    # Load all API keys from .env and .env2 — inject them per-subprocess to force key rotation
    api_keys = []
    for env_file in [".env", ".env2"]:
        env_path = project_root / env_file
        if env_path.exists():
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if line.startswith('GEMINI_API_KEY') and '=' in line:
                        val = line.split('=', 1)[1].strip()
                        if val:
                            api_keys.append(val)
                    elif '=' not in line and len(line) > 20: # raw key
                        api_keys.append(line)
                            
    if not api_keys:
        # Fallback: read from current env
        for k, v in sorted(os.environ.items()):
            if k.startswith('GEMINI_API_KEY') and v:
                api_keys.append(v)
                
    tracker_path = args.manifest_dir / "api_key_status.json"
    key_tracker = load_key_tracker(tracker_path)
    
    current_time = time.time()
    active_keys = []
    for key in api_keys:
        if key in key_tracker:
            exhausted_time = key_tracker[key].get("exhausted_at", 0)
            if current_time - exhausted_time < 24 * 3600:
                continue # in cooldown
        active_keys.append(key)
        
    api_keys = active_keys
    print(f"  API keys available for rotation (after cooldown): {len(api_keys)}", flush=True)

    global_key_idx = 0

    # Filter houses to process
    to_process = []
    started = args.start_from is None  # If no --start-from, process everything

    for house in houses:
        hid = house["house_id"]

        # Handle --start-from: skip until we find the target house
        if not started:
            # Compare numerically for proper ordering
            hid_num = re.match(r'(\d+)', hid)
            start_num = re.match(r'(\d+)', args.start_from)
            if hid_num and start_num:
                if int(hid_num.group(1)) >= int(start_num.group(1)):
                    started = True
            elif hid == args.start_from:
                started = True

            if not started:
                continue

        # Skip houses that are already done
        if house["run_status"] == "done":
            continue

        # Skip houses that are failed/timeout unless --retry-failed
        if house["run_status"] in ("failed", "timeout") and not args.retry_failed:
            continue

        # Skip houses without YAML
        if house.get("yaml_status") not in ("ready",):
            continue

        # Skip houses that were user-skipped
        if house.get("skipped_reason"):
            continue

        # Must have an addition PDF for auto_add to work
        if not house.get("has_addition_pdf"):
            # Just reconcile-only — run reconciliation directly
            to_process.append((house, False))
        else:
            to_process.append((house, True))

    total = len(to_process)
    with_additions = sum(1 for _, has_pdf in to_process if has_pdf)
    reconcile_only = total - with_additions

    print(f"\n{'='*60}")
    print(f"  Batch Auto-Add Runner for {args.area}")
    print(f"{'='*60}")
    print(f"  Total houses to process: {total}")
    print(f"    With addition PDFs:    {with_additions}")
    print(f"    Reconcile-only:        {reconcile_only}")
    if args.start_from:
        print(f"  Starting from house:     {args.start_from}")
    print(f"  Timeout per house:       {args.timeout}s")
    print(f"{'='*60}\n")

    succeeded = 0
    failed = 0
    timed_out = 0
    skipped = 0
    failed_houses = []
    timeout_houses = []

    for idx, (house, has_addition) in enumerate(to_process, 1):
        hid = house["house_id"]
        house_dir = house["house_dir"]

        if has_addition:
            task_type = "reconcile + addition"
        else:
            task_type = "reconcile-only"

        print(f"\n[{idx}/{total}] Processing House {hid} ({task_type})...", flush=True)

        if has_addition:
            # Run auto_add.py
            cmd = [
                sys.executable, "-u", str(project_root / "scripts" / "auto_add.py"),
                hid, args.area,
                "--additions-dir", additions_dir
            ]
        else:
            # Run reconcile only
            cmd = [
                sys.executable, "-u", str(project_root / "src" / "main.py"),
                "reconcile",
                str(Path(manifest.get("areas_root", "D:/Areas")) / args.area / house_dir),
                "--tenants"
            ]

        start_time = time.time()
        house_success = False
        FAST_FAIL_THRESHOLD = 15  # seconds — under this means structural error, not quota

        if has_addition and api_keys:
            # Try each API key starting from global_key_idx
            for i in range(len(api_keys)):
                key_idx = (global_key_idx + i) % len(api_keys)
                api_key = api_keys[key_idx]
                key_start = time.time()
                print(f"  [KEY {key_idx+1}/{len(api_keys)}] Trying with key #{key_idx+1}...", flush=True)
                subprocess_env = {**os.environ, 'PYTHONUNBUFFERED': '1', 'GEMINI_API_KEY': api_key}
                try:
                    result = subprocess.run(
                        cmd,
                        cwd=str(project_root),
                        timeout=args.timeout,
                        env=subprocess_env
                    )
                    key_elapsed = time.time() - key_start
                    elapsed = time.time() - start_time
                    if result.returncode == 0:
                        print(f"  [OK]   House {hid}: SUCCESS with key #{key_idx+1} ({elapsed:.0f}s)", flush=True)
                        house["run_status"] = "done"
                        house["run_error"] = None
                        succeeded += 1
                        house_success = True
                        global_key_idx = key_idx
                        break
                    elif key_elapsed < FAST_FAIL_THRESHOLD:
                        # Fast failure = structural error (missing .source_files, bad PDF, etc.)
                        # Rotating keys won't help — fail immediately
                        print(f"  [FAIL] House {hid}: structural error (failed in {key_elapsed:.0f}s) — skipping key rotation", flush=True)
                        break
                    else:
                        print(f"  [FAIL] House {hid}: key #{key_idx+1} quota/slow failure — rotating to next key...", flush=True)
                        key_tracker[api_key] = {"exhausted_at": time.time()}
                        save_key_tracker(tracker_path, key_tracker)
                except subprocess.TimeoutExpired:
                    elapsed = time.time() - start_time
                    print(f"  [TIME] House {hid}: key #{key_idx+1} timed out ({elapsed:.0f}s) — rotating...", flush=True)
                    key_tracker[api_key] = {"exhausted_at": time.time()}
                    save_key_tracker(tracker_path, key_tracker)
                except Exception as e:
                    print(f"  [ERR]  House {hid}: key #{key_idx+1} error: {e} — rotating...", flush=True)

            if not house_success:
                elapsed = time.time() - start_time
                print(f"  [FAIL] House {hid}: ALL KEYS EXHAUSTED ({elapsed:.0f}s)", flush=True)
                house["run_status"] = "failed"
                house["run_error"] = "All API keys exhausted"
                failed += 1
                failed_houses.append((hid, "All API keys exhausted"))
        else:
            # Reconcile-only or no keys: single run
            try:
                result = subprocess.run(
                    cmd,
                    cwd=str(project_root),
                    timeout=args.timeout,
                    env={**os.environ, 'PYTHONUNBUFFERED': '1'}
                )
                elapsed = time.time() - start_time
                if result.returncode == 0:
                    print(f"  [OK]   House {hid}: SUCCESS ({elapsed:.0f}s)", flush=True)
                    house["run_status"] = "done"
                    house["run_error"] = None
                    succeeded += 1
                    house_success = True
                else:
                    print(f"  [FAIL] House {hid}: FAILED ({elapsed:.0f}s)", flush=True)
                    house["run_status"] = "failed"
                    house["run_error"] = "Failed with non-zero exit code"
                    failed += 1
                    failed_houses.append((hid, "Failed with non-zero exit code"))
            except subprocess.TimeoutExpired:
                elapsed = time.time() - start_time
                print(f"  [TIME] House {hid}: TIMED OUT ({elapsed:.0f}s)", flush=True)
                house["run_status"] = "timeout"
                house["run_error"] = f"Exceeded {args.timeout}s timeout"
                timed_out += 1
                timeout_houses.append(hid)
            except Exception as e:
                elapsed = time.time() - start_time
                print(f"  [ERR]  House {hid}: ERROR ({elapsed:.0f}s) - {e}", flush=True)
                house["run_status"] = "failed"
                house["run_error"] = str(e)[:500]
                failed += 1
                failed_houses.append((hid, str(e)[:200]))

        # Save manifest after every house (crash-safe)
        save_manifest(manifest_path, manifest)

    # Final report
    print(f"\n{'='*60}")
    print(f"  Batch Run Complete for {args.area}")
    print(f"{'='*60}")
    print(f"  Processed:   {total} houses")
    print(f"  Succeeded:   {succeeded}")
    print(f"  Failed:      {failed}")
    print(f"  Timed out:   {timed_out}")

    if failed_houses:
        print(f"\n  Failed Houses:")
        for hid, err in failed_houses:
            print(f"    • {hid} — {err}")

    if timeout_houses:
        print(f"\n  Timed Out Houses:")
        for hid in timeout_houses:
            print(f"    • {hid}")

    print(f"\n  Manifest updated: {manifest_path}")
    print(f"{'='*60}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
