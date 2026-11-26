"""Adversarial hardening & integrity tests for Wing 1 compiled native macOS tools."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = [
    ("PortPilot", ROOT / "tools/PortPilot/build/PortPilot.app", ROOT / "dist/PortPilot_v1.0.0_macOS_arm64.dmg"),
    ("SnapShrink", ROOT / "tools/SnapShrink/build/SnapShrink.app", ROOT / "dist/SnapShrink_v1.0.0_macOS_arm64.dmg"),
]
FORBIDDEN_STRINGS = (
    "api.gumroad.com",
    "licenses/verify",
    "IOPlatformUUID",
    "IOPlatformExpertDevice",
    "DYLD_INSERT_LIBRARIES",
    ".pp_license_v1",
    ".ss_license_v1",
)


@pytest.mark.parametrize("name,app_bundle,dmg_path", TOOLS)
def test_native_macos_binary_hardening(name: str, app_bundle: Path, dmg_path: Path) -> None:
    if not app_bundle.exists():
        pytest.skip(f"{name} local compiled bundle not present in CI checkout")

    binary = app_bundle / "Contents/MacOS" / name
    assert binary.exists(), f"Missing Mach-O binary: {binary}"
    assert dmg_path.exists() and dmg_path.stat().st_size > 100_000, f"Missing or empty DMG: {dmg_path}"

    # 1. Confirm compiled ARM64 Mach-O executable
    file_out = subprocess.check_output(["file", str(binary)], text=True)
    assert "Mach-O 64-bit executable arm64" in file_out

    # 2. Confirm ZERO plaintext source files exist anywhere inside the .app bundle
    source_files = [
        p for p in app_bundle.rglob("*")
        if p.suffix.lower() in {".swift", ".py", ".sh", ".c", ".h", ".m"}
    ]
    assert source_files == [], f"Source files leaked into .app bundle: {source_files}"

    # 3. Confirm ZERO sensitive strings appear in binary strings output
    strings_out = subprocess.check_output(["strings", str(binary)], text=True, errors="ignore")
    leaked = [tok for tok in FORBIDDEN_STRINGS if tok.lower() in strings_out.lower()]
    assert leaked == [], f"Sensitive plaintext strings leaked into {name}: {leaked}"

    # 4. Confirm aggressive symbol stripping (<= 3 defined external symbols)
    nm_out = subprocess.check_output(["nm", "-gU", str(binary)], text=True)
    defined_syms = [line for line in nm_out.splitlines() if line.strip()]
    assert len(defined_syms) <= 3, f"Too many defined symbols exposed in {name}: {defined_syms}"

    # 5. Confirm code signature integrity
    subprocess.run(["codesign", "--verify", "--deep", "--strict", str(app_bundle)], check=True)

    # 6. Confirm live self-test passes (XOR vault, IOKit UUID, HMAC receipt + cross-Mac rejection)
    test_out = subprocess.check_output([str(binary), "--self-test"], text=True)
    payload = json.loads(test_out)
    assert payload.get("ok") is True, f"Self-test failed for {name}: {payload}"
