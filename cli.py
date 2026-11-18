"""GMaps Scout from the command line.

Example:
  python cli.py "coffee shop in Bali" --limit 20 --out leads.xlsx
"""
import argparse
import csv
import sys
import time

from gmapscout_core import COLUMNS, scrape


def main():
    p = argparse.ArgumentParser(description="Turn publicly listed business details into a spreadsheet (Vulpfest Lab).")
    p.add_argument("query", help='what to search for on Google Maps, e.g. "coffee shop in Bali"')
    p.add_argument("--limit", type=int, default=20, help="maximum number of places (default 20, up to 200)")
    p.add_argument("--out", metavar="FILE", help="save as .xlsx or .csv")
    p.add_argument("--show-browser", action="store_true", help="show the browser window instead of running headless")
    a = p.parse_args()
    print("Reminder: collect only publicly listed business information and follow the terms of the sites you use.", file=sys.stderr)

    def log(msg, type="info"):
        print(f"[{time.strftime('%H:%M:%S')}] {type.upper():<7} {msg.replace('**', '')}", file=sys.stderr)

    def progress(phase, current, total):
        if phase == "extract":
            print(f"  reading {current}/{total}", end="\r", file=sys.stderr)

    rows = scrape(a.query, max(1, min(a.limit, 200)), headless=not a.show_browser, log=log, on_progress=progress)
    if not rows:
        print("No data retrieved.", file=sys.stderr)
        return 1
    if a.out and a.out.lower().endswith(".xlsx"):
        import pandas as pd
        pd.DataFrame(rows, columns=COLUMNS).to_excel(a.out, index=False, sheet_name="Leads")
    elif a.out:
        with open(a.out, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=COLUMNS)
            w.writeheader()
            w.writerows(rows)
    else:
        for r in rows:
            print(f"{r['Entity Name']}\t{r['Contact Number']}\t{r['Website URL']}\t{r['Address']}")
    if a.out:
        print(f"Saved {len(rows)} places to {a.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
