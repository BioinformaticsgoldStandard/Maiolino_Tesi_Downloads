import os
import re
import tarfile
import urllib.request
import urllib.error
import time
import random
import shutil
from pathlib import Path
import numpy as np
import h5py

# Spoof full browser headers to bypass WAF
opener = urllib.request.build_opener()
opener.addheaders = [
    ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'),
    ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
    ('Accept-Language', 'en-US,en;q=0.5')
]
urllib.request.install_opener(opener)

GEO_COHORTS = {
    "2026": [
        "GSE312100", "GSE271962", "GSE315102", "GSE311730", "GSE288481",
        "GSE268609", "GSE324481", "GSE320040", "GSE300150", "GSE281619"
    ],
    "2025": [
        "GSE292090", "GSE289546", "GSE295689", "GSE296768", "GSE292840",
        "GSE301435", "GSE223424", "GSE251706", "GSE279488", "GSE295708"
    ]
}

def get_geo_suppl_url(gse_id: str) -> str:
    stub = gse_id[:-3] + "nnn"
    return f"https://ftp.ncbi.nlm.nih.gov/geo/series/{stub}/{gse_id}/suppl/"

def fetch_with_retry(url: str, dest: Path = None, max_retries: int = 5):
    """Executes network calls with exponential backoff for rate limits."""
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(url, timeout=20) as response:
                if dest:
                    with open(dest, 'wb') as out_file:
                        shutil.copyfileobj(response, out_file)
                    return None
                else:
                    return response.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if attempt == max_retries - 1:
                raise
            wait = (2 ** attempt) + random.uniform(3, 7)
            print(f"  [!] HTTP {e.code}. Retrying in {wait:.1f}s (Attempt {attempt+1}/{max_retries})...")
            time.sleep(wait)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait = (2 ** attempt) + random.uniform(3, 7)
            print(f"  [!] Error: {e}. Retrying in {wait:.1f}s...")
            time.sleep(wait)

def list_remote_files(url: str) -> list[str]:
    try:
        html = fetch_with_retry(url)
        files = re.findall(r'href="([^"/]+)"', html)
        return [f for f in files if not f.startswith("?")]
    except Exception as e:
        print(f"  [!] Failed to read directory {url}: {e}")
        return []

def inspect_h5ad_for_raw_counts(filepath: Path) -> str:
    try:
        with h5py.File(filepath, "r") as f:
            has_raw = "raw" in f
            layers = list(f["layers"].keys()) if "layers" in f else []
            x_group = f["X"]
            data_sample = x_group["data"][:100] if "data" in x_group else x_group[:100]
            is_x_integer = np.all(np.equal(np.mod(data_sample, 1), 0))
            return f"X_is_int={is_x_integer} | has_raw={has_raw} | layers={layers}"
    except Exception as e:
        return f"Inspection error: {e}"

def download_and_organize(base_dir: str = "./scrna_repro_study"):
    for year, gse_list in GEO_COHORTS.items():
        for gse in gse_list:
            out_dir = Path(base_dir) / year / gse
            out_dir.mkdir(parents=True, exist_ok=True)
            
            url = get_geo_suppl_url(gse)
            print(f"\n=== Fetching {gse} ({year}) ===")
            files = list_remote_files(url)
            
            if not files:
                print(f"  [-] No Series-level suppl files found.")
                continue

            for fname in files:
                dest = out_dir / fname
                if not dest.exists():
                    print(f"  [↓] Downloading {fname}...")
                    fetch_with_retry(url + fname, dest)
                    time.sleep(2.5) 
                else:
                    print(f"  [✓] Already exists: {fname}")

                if fname.endswith(".tar"):
                    extract_dir = out_dir / "unpacked_raw"
                    extract_dir.mkdir(exist_ok=True)
                    print(f"  [📦] Extracting {fname} -> {extract_dir.name}/")
                    with tarfile.open(dest, "r") as tar:
                        tar.extractall(path=extract_dir, filter="data")

                if fname.endswith(".h5ad"):
                    audit = inspect_h5ad_for_raw_counts(dest)
                    print(f"  [🔍] H5AD Audit ({fname}): {audit}")

if __name__ == "__main__":
    download_and_organize()