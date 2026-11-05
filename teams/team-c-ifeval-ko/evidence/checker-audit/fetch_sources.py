"""Restore pinned, byte-verified sources using read-only HTTP downloads."""
import concurrent.futures
import hashlib
import io
import json
from pathlib import Path
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parent


def download(url, expected, dest):
    if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest() == expected:
        return dest.read_bytes()
    data = urllib.request.urlopen(url, timeout=90).read()
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError(f"Source hash mismatch: {url}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    return data


def main():
    provenance = json.loads((ROOT / "provenance.json").read_text())
    entries = [info for entry in provenance.values() for info in entry["files"].values()]
    def restore(info):
        download(info["url"], info["sha256"], ROOT / info["local_path"])
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(restore, entries))
    package = provenance["harness"]["package_snapshot"]
    archive = download(package["archive_url"], package["archive_sha256"], ROOT / package["archive_path"])
    base = ROOT / package["local_path"]
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
        for member in tar.getmembers():
            relative = member.name.partition("/")[2]
            if not member.isfile():
                continue
            wanted = relative in {"pyproject.toml", "README.md", "LICENSE.md", "MANIFEST.in"} or relative.startswith("lm_eval/") and relative.endswith(".py")
            if relative.startswith("lm_eval/tasks/"):
                wanted = relative.startswith("lm_eval/tasks/ifeval/") or relative.count("/") == 2 and relative.endswith(".py")
            if not wanted:
                continue
            if ".." in Path(relative).parts or Path(relative).is_absolute():
                raise ValueError("Unexpected archive path")
            dest = base / relative
            data = tar.extractfile(member).read()
            if not dest.exists() or dest.read_bytes() != data:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(data)
    import pyarrow.parquet as pq
    rows = pq.read_table(ROOT / "sources/ko/data/train-00000-of-00001.parquet").to_pylist()
    (ROOT / "sources/ko/data/rows.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(entries)} source files and harness package archive; Ko {len(rows)} rows")


if __name__ == "__main__":
    main()
