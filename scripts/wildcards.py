#!/usr/bin/env python3
"""Read current wildcard / currency inventory from the Arena Player.log.

Arena writes an InventoryInfo blob on every login and after most transactions.
The LAST occurrence in the file is the current one -- SeqId is NOT monotonic
across sessions, so never sort by it.

TRAP: Arena omits zero-valued keys entirely. An entry with no "WildCardRares"
key means zero rares, not "unknown". Defaulting to 0 is correct; treating a
missing key as an error is not.

Usage:
    python scripts/wildcards.py            # human-readable
    python scripts/wildcards.py --json     # machine-readable
"""
import argparse
import json
import os
import re
import sys

DEFAULT_LOG = os.path.expandvars(
    r"%USERPROFILE%\AppData\LocalLow\Wizards Of The Coast\MTGA\Player.log"
)

FIELDS = {
    "WildCardCommons": "common",
    "WildCardUnCommons": "uncommon",
    "WildCardRares": "rare",
    "WildCardMythics": "mythic",
    "Gems": "gems",
    "Gold": "gold",
    "TotalVaultProgress": "vault_progress",
    "wcTrackPosition": "wc_track_position",
}

BLOCK_RE = re.compile(r'"InventoryInfo":\s?\{.*?"CustomTokens"')


def read_inventory(log_path):
    with open(log_path, "r", encoding="utf-8", errors="replace") as fh:
        text = fh.read()

    blocks = BLOCK_RE.findall(text)
    if not blocks:
        raise SystemExit(
            f"No InventoryInfo block found in {log_path}.\n"
            "Launch Arena and log in at least once, then re-run."
        )

    # Last occurrence in file order == most recent write.
    latest = blocks[-1]
    out = {}
    for key, label in FIELDS.items():
        m = re.search(rf'"{key}":\s?(\d+)', latest)
        # Missing key means zero -- Arena omits zero-valued fields.
        out[label] = int(m.group(1)) if m else 0
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--log", default=DEFAULT_LOG, help="path to Player.log")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    args = ap.parse_args()

    if not os.path.exists(args.log):
        sys.exit(f"Player.log not found at {args.log}")

    inv = read_inventory(args.log)

    if args.json:
        print(json.dumps(inv, indent=2))
        return

    print("WILDCARDS")
    for r in ("common", "uncommon", "rare", "mythic"):
        print(f"  {r:<9} {inv[r]:>4}")
    print("  (Arena writes InventoryInfo at session/transaction boundaries, not")
    print("   after every craft -- these can lag. Verify in-client before")
    print("   committing to a big spend.)")
    print("\nCURRENCY")
    print(f"  gems      {inv['gems']:>4}")
    print(f"  gold      {inv['gold']:>4}")
    print(f"\nVault     {inv['vault_progress']}/1000")
    print(f"WC track  position {inv['wc_track_position']}")


if __name__ == "__main__":
    main()
