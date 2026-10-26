#!/usr/bin/env python3
import concurrent.futures
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen

REPO = Path('/mnt/models_2296/zmz/workspace/cosmos3_nano_worldmodel/model')
ENDPOINT = 'https://atomgit.com/hf_mirrors/nvidia/Cosmos3-Nano.git/info/lfs/objects/batch'
INCLUDE_PREFIXES = ('transformer/', 'vae/', 'sound_tokenizer/', 'vision_encoder/', 'text_tokenizer/')

def git(*args):
    return subprocess.check_output(['git', '-C', str(REPO), *args], text=True).strip()

def lfs_files():
    out = git('lfs', 'ls-files', '-n')
    return [p for p in out.splitlines() if p.startswith(INCLUDE_PREFIXES)]

def pointer(path):
    text = git('cat-file', '-p', f'HEAD:{path}')
    meta = {}
    for line in text.splitlines():
        parts = line.split(' ', 2)
        if len(parts) == 3:
            meta[parts[0]] = parts[2]
        elif len(parts) == 2:
            meta[parts[0]] = parts[1]
    return meta['oid'].removeprefix('sha256:'), int(meta['size'])

def href(oid, size):
    body = json.dumps({'operation':'download','objects':[{'oid':oid,'size':size}]}).encode()
    req = Request(ENDPOINT, data=body, headers={
        'Accept':'application/vnd.git-lfs+json',
        'Content-Type':'application/vnd.git-lfs+json',
    }, method='POST')
    with urlopen(req, timeout=60) as r:
        obj = json.load(r)
    try:
        return obj['objects'][0]['actions']['download']['href']
    except Exception as exc:
        raise RuntimeError(json.dumps(obj, ensure_ascii=False)) from exc

def download(path):
    target = REPO / path
    target.parent.mkdir(parents=True, exist_ok=True)
    oid, size = pointer(path)
    control = Path(str(target) + '.aria2')
    if target.exists() and target.stat().st_size == size and not control.exists():
        print(f'SKIP {path} ({size/2**30:.2f} GiB)', flush=True)
        return path
    tmp = target.with_name(target.name + '.aria2')
    url = href(oid, size)
    print(f'START {path} ({size/2**30:.2f} GiB)', flush=True)
    proxy = os.environ.get('https_proxy') or os.environ.get('HTTPS_PROXY') or ''
    cmd = [
        'aria2c', '--all-proxy=' + proxy, '--check-certificate=false',
        '--continue=true', '--allow-overwrite=true', '--auto-file-renaming=false',
        '--file-allocation=none', '--max-connection-per-server=8', '--split=8',
        '--min-split-size=16M', '--max-tries=8', '--retry-wait=3', '--timeout=60',
        '--console-log-level=warn', '--summary-interval=30',
        '--dir', str(target.parent), '--out', target.name, url,
    ]
    subprocess.run(cmd, check=True)
    actual_size = target.stat().st_size
    if actual_size != size:
        raise RuntimeError(f'{path}: size mismatch {actual_size} != {size}')
    h = hashlib.sha256()
    with target.open('rb') as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    if h.hexdigest() != oid:
        target.unlink(missing_ok=True)
        raise RuntimeError(f'{path}: sha256 mismatch')
    tmp.unlink(missing_ok=True)
    print(f'DONE  {path}', flush=True)
    return path

def main():
    files = lfs_files()
    print(f'Downloading {len(files)} LFS model files', flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(download, p): p for p in files}
        failed = []
        for future in concurrent.futures.as_completed(futures):
            p = futures[future]
            try:
                future.result()
            except Exception as exc:
                failed.append((p, str(exc)))
                print(f'FAIL  {p}: {exc}', flush=True)
    if failed:
        for p, exc in failed:
            print(f'FAILED {p}: {exc}', file=sys.stderr)
        return 1
    print('ALL_MODEL_FILES_VERIFIED', flush=True)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
