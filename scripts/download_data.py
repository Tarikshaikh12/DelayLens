"""Download the official Olist v2 archive and verify the recorded CSV hashes."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def download(destination=ROOT / "data/raw", archive=None):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ROOT / "data/source_manifest.json").read_text())
    expected = manifest["files"]
    if all((destination/n).exists() and hashlib.sha256((destination/n).read_bytes()).hexdigest() == h for n,h in expected.items()):
        print("All nine source files already match the pinned Olist v2 hashes.")
        return
    with tempfile.TemporaryDirectory() as temp:
        source = Path(archive) if archive else Path(temp) / "olist.zip"
        if archive is None:
            print("Downloading public Olist v2 data from Kaggle (about 45 MB)...")
            try:
                with urllib.request.urlopen(manifest["download_url"], timeout=90) as r, source.open("wb") as out:
                    shutil.copyfileobj(r, out)
            except Exception as e:
                raise RuntimeError("Download failed. Download Olist v2 from its Kaggle page, then run this script with --archive /path/to/archive.zip. Never put Kaggle credentials in this repository.") from e
        with zipfile.ZipFile(source) as z:
            # Only allow exact expected filenames; never extract arbitrary archive paths.
            for name, digest in expected.items():
                data = z.read(name)
                if hashlib.sha256(data).hexdigest() != digest:
                    raise ValueError(f"Hash mismatch: {name}. Do not silently change the dataset version.")
                (Path(temp) / name).write_bytes(data)
            for name in expected:
                shutil.copyfile(Path(temp) / name, destination / name)
    print("Downloaded and verified all nine files.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", help="Optional official ZIP already downloaded manually")
    parser.add_argument("--destination", type=Path, default=ROOT / "data/raw")
    args = parser.parse_args()
    download(args.destination, args.archive)
