#!/usr/bin/env python3
import csv
import json
import os
import sys
import tempfile
from pathlib import Path
from textwrap import shorten

from starlette.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "data" / "example_inputs.csv"
OUT_MD = ROOT / "data" / "example_run_results.md"
OUT_CSV = ROOT / "data" / "example_run_results.csv"


def main():
    rows = list(csv.DictReader(open(CSV, encoding="utf-8")))

    tmpdir = Path(tempfile.mkdtemp())
    try:
        index = tmpdir / "data" / "index"
        index.mkdir(parents=True)
        metadata = []
        for r in rows:
            p = ROOT / r["doc_path"]
            metadata.append({
                "file": r["doc_path"],
                "chunk_id": f"{Path(r['doc_path']).name}::chunk::0",
                "text": p.read_text(encoding="utf-8"),
            })
        (index / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

        # set up environment so app.main imports the temporary index
        cwd = os.getcwd()
        os.chdir(tmpdir)
        sys.path.insert(0, str(ROOT))

        from app.main import app

        results = []
        with TestClient(app) as client:
            for r in rows:
                resp = client.post("/search", json={"q": r["probe_query"]})
                data = resp.json()
                matches = data.get("matches", [])
                results.append(
                    {
                        "case_id": r["case_id"],
                        "case_type": r["case_type"],
                        "probe_query": r["probe_query"],
                        "match_count": len(matches),
                        "matched_files": "|".join(m.get("file", "") for m in matches),
                        "first_match_snippet": shorten(matches[0]["text"].replace("\n", " "), width=120) if matches else "",
                    }
                )

        # write CSV
        if results:
            with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
                writer.writeheader()
                writer.writerows(results)

        # write markdown table
        with open(OUT_MD, "w", encoding="utf-8") as f:
            f.write("# Example Run Results\n\n")
            f.write("|case_id|type|query|matches|matched_files|snippet|\n")
            f.write("|---|---|---|---|---|---|\n")
            for r in results:
                # escape pipes in fields
                q = r["probe_query"].replace("|", "\\|")
                mf = r["matched_files"].replace("|", "\\|")
                snip = r["first_match_snippet"].replace("|", "\\|")
                f.write(f"|{r['case_id']}|{r['case_type']}|{q}|{r['match_count']}|{mf}|{snip}|\n")

        # print markdown to stdout for quick review
        print((OUT_MD).read_text(encoding="utf-8"))

    finally:
        # restore cwd and cleanup
        try:
            os.chdir(cwd)
        except Exception:
            pass
        import shutil

        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    main()
import csv
import json
import os
import sys
import tempfile
from pathlib import Path
from textwrap import shorten

from starlette.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]
CSV_IN = ROOT / "data" / "example_inputs.csv"
CSV_OUT = ROOT / "data" / "example_results.csv"
MD_OUT = ROOT / "data" / "example_results.md"


def load_cases():
    with CSV_IN.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def build_tmp_index(rows, tmp):
    data_index = Path(tmp) / "data" / "index"
    data_index.mkdir(parents=True, exist_ok=True)
    metadata = []
    for row in rows:
        doc_path = ROOT / row["doc_path"]
        metadata.append({
            "file": row["doc_path"],
            "chunk_id": f"{Path(row['doc_path']).name}::chunk::0",
            "text": doc_path.read_text(encoding="utf-8"),
        })
    (data_index / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")


def run_all():
    rows = load_cases()

    # create a temporary workspace where app will read the index
    with tempfile.TemporaryDirectory() as tmpdir:
        build_tmp_index(rows, tmpdir)
        cwd = os.getcwd()
        os.chdir(tmpdir)
        sys.path.insert(0, str(ROOT))
        try:
            from app.main import app

            results = []
            with TestClient(app) as client:
                for r in rows:
                    q = r["probe_query"]
                    resp = client.post("/search", json={"q": q})
                    status = resp.status_code
                    data = resp.json() if resp.status_code == 200 else {}
                    matches = data.get("matches", [])
                    files = "; ".join(m.get("file", "") for m in matches)
                    first_text = shorten(matches[0].get("text", "") if matches else "", width=200, placeholder="...")
                    results.append(
                        {
                            "case_id": r["case_id"],
                            "case_type": r["case_type"],
                            "probe_query": q,
                            "status_code": status,
                            "match_count": len(matches),
                            "matched_files": files,
                            "first_match_snippet": first_text,
                        }
                    )

        finally:
            os.chdir(cwd)

    # write CSV and MD
    with CSV_OUT.open("w", newline="", encoding="utf-8") as outfh:
        writer = csv.DictWriter(outfh, fieldnames=["case_id", "case_type", "probe_query", "status_code", "match_count", "matched_files", "first_match_snippet"])
        writer.writeheader()
        for r in results:
            writer.writerow(r)

    with MD_OUT.open("w", encoding="utf-8") as mdfh:
        mdfh.write("# Example Set Results\n\n")
        for r in results:
            mdfh.write(f"## {r['case_id']} — {r['case_type']}\n\n")
            mdfh.write(f"- Query: `{r['probe_query']}`\n")
            mdfh.write(f"- Status: {r['status_code']}\n")
            mdfh.write(f"- Matches: {r['match_count']}\n")
            mdfh.write(f"- Matched files: {r['matched_files']}\n")
            mdfh.write(f"- Snippet: {r['first_match_snippet']}\n\n")

    print(f"Wrote results to {CSV_OUT} and {MD_OUT}")


if __name__ == "__main__":
    run_all()
