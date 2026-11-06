#!/usr/bin/env python3
"""Package artifacts from a successful ScarletNX Build run for this mirror's Release.

Does not build or execute artifact contents. Required platforms must be present.
Uses the authenticated GitHub CLI (GH_TOKEN) supplied by GitHub Actions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile


# Artifact name template, public release asset, required, packaging method.
PACKAGES = (
    ("ScarletNX-linux-x86_64-{short}.AppImage", "ScarletNX-linux-x86_64.AppImage", True, "copy"),
    ("ScarletNX-linux-aarch64-{short}.AppImage", "ScarletNX-linux-aarch64.AppImage", True, "copy"),
    ("ScarletNX-windows-x86_64-{short}", "ScarletNX-windows-x86_64.zip", True, "zip"),
    ("ScarletNX-android-universal-{short}.apk", "ScarletNX-android-universal.apk", True, "copy"),
    ("ScarletNX-linux-ppc64le-{short}.AppImage", "ScarletNX-linux-ppc64le.AppImage", False, "copy"),
    ("ScarletNX-linux-ppc64-{short}.AppImage", "ScarletNX-linux-ppc64.AppImage", False, "copy"),
    ("ScarletNX-linux-riscv64-{short}.AppImage", "ScarletNX-linux-riscv64.AppImage", False, "copy"),
    ("ScarletNX-linux-loongarch64-{short}.AppImage", "ScarletNX-linux-loongarch64.AppImage", False, "copy"),
    ("ScarletNX-macos-arm64-{short}.zip", "ScarletNX-macos-arm64.zip", False, "copy"),
    ("ScarletNX-ios-arm64-{short}.ipa", "ScarletNX-ios-arm64.ipa", False, "copy"),
)


def gh(*arguments: str) -> str:
    return subprocess.check_output(("gh", *arguments), text=True).strip()


def package_archive(source_dir: Path, output: Path) -> None:
    files = sorted(path for path in source_dir.rglob("*") if path.is_file())
    if not files:
        raise RuntimeError(f"Empty Windows artifact: {source_dir}")
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path in files:
            archive.write(path, path.relative_to(source_dir))


def package_file(source_dir: Path, output: Path) -> None:
    candidates = [p for p in source_dir.rglob("*") if p.is_file() and p.suffix == output.suffix]
    if len(candidates) != 1:
        raise RuntimeError(f"Expected exactly one {output.suffix} in {source_dir}, got {len(candidates)}")
    shutil.copyfile(candidates[0], output)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--run", required=True)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if len(args.sha) != 40 or any(ch not in "0123456789abcdef" for ch in args.sha):
        parser.error("--sha must be a lowercase full Git commit SHA")

    response = json.loads(gh("api", f"repos/{args.repo}/actions/runs/{args.run}/artifacts?per_page=100"))
    available = {item["name"] for item in response["artifacts"] if not item.get("expired")}
    short = args.sha[:7]
    required = {tpl.format(short=short) for tpl, _, is_required, _ in PACKAGES if is_required}
    missing = sorted(required - available)
    if missing:
        raise RuntimeError("Required build artifacts missing: " + ", ".join(missing))

    args.out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="scarletnx-artifacts-") as temporary:
        root = Path(temporary)
        for template, asset, is_required, mode in PACKAGES:
            artifact = template.format(short=short)
            if artifact not in available:
                print(f"Optional artifact unavailable: {artifact}")
                continue
            download_to = root / artifact
            download_to.mkdir()
            gh("run", "download", args.run, "--repo", args.repo,
               "--name", artifact, "--dir", str(download_to))
            output = args.out / asset
            if mode == "zip":
                package_archive(download_to, output)
            else:
                package_file(download_to, output)
            print(f"Ready: {asset} ({output.stat().st_size} bytes)")

    assets = sorted(path for path in args.out.iterdir() if path.is_file())
    if len(assets) < len(required):
        raise RuntimeError("Required release assets were not all packaged")
    checksums = []
    for path in assets:
        digest = hashlib.file_digest(path.open("rb"), "sha256").hexdigest()
        checksums.append(f"{digest}  {path.name}")
    (args.out / "SHA256SUMS.txt").write_text("\n".join(checksums) + "\n", encoding="ascii")


if __name__ == "__main__":
    main()
