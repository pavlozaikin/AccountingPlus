"""Helpers to make WeasyPrint work on macOS/Homebrew setups."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable, Tuple

_HOME_BREW_CANDIDATES: Tuple[Path, ...] = (Path("/opt/homebrew"), Path("/usr/local"))


def _existing_prefixes() -> Tuple[Path, ...]:
    """Return Homebrew prefixes that exist on the current machine."""
    prefixes = tuple(prefix for prefix in _HOME_BREW_CANDIDATES if prefix.exists())
    return prefixes


def _prepend_env(name: str, value: str) -> None:
    if not value:
        return
    current = os.environ.get(name)
    parts = current.split(":") if current else []
    if value in parts:
        return
    os.environ[name] = ":".join([value] + parts) if parts else value


def configure_environment(prefixes: Iterable[Path] | None = None) -> Tuple[Path, ...]:
    """Expose Homebrew library/bin/pkgconfig paths via environment variables."""
    resolved = tuple(prefixes) if prefixes is not None else _existing_prefixes()
    for prefix in resolved:
        lib_dir = prefix / "lib"
        if lib_dir.exists():
            lib_path = str(lib_dir)
            _prepend_env("DYLD_FALLBACK_LIBRARY_PATH", lib_path)
            _prepend_env("DYLD_LIBRARY_PATH", lib_path)
            _prepend_env("LIBRARY_PATH", lib_path)
        pkgconfig_dir = prefix / "lib" / "pkgconfig"
        if pkgconfig_dir.exists():
            _prepend_env("PKG_CONFIG_PATH", str(pkgconfig_dir))
        bin_dir = prefix / "bin"
        if bin_dir.exists():
            _prepend_env("PATH", str(bin_dir))
    return resolved


def _macos_library_candidates() -> dict[str, Tuple[str, ...]]:
    return {
        "libgobject-2.0-0": ("libgobject-2.0.dylib", "libgobject-2.0.0.dylib"),
        "gobject-2.0-0": ("libgobject-2.0.dylib", "libgobject-2.0.0.dylib"),
        "gobject-2.0": ("libgobject-2.0.dylib", "libgobject-2.0.0.dylib"),
        "libpango-1.0-0": ("libpango-1.0.dylib", "libpango-1.0.0.dylib"),
        "pango-1.0-0": ("libpango-1.0.dylib", "libpango-1.0.0.dylib"),
        "pango-1.0": ("libpango-1.0.dylib", "libpango-1.0.0.dylib"),
        "libharfbuzz-0": ("libharfbuzz.dylib", "libharfbuzz.0.dylib"),
        "harfbuzz": ("libharfbuzz.dylib", "libharfbuzz.0.dylib"),
        "harfbuzz-0.0": ("libharfbuzz.dylib", "libharfbuzz.0.dylib"),
        "libharfbuzz-subset-0": (
            "libharfbuzz-subset.dylib",
            "libharfbuzz-subset.0.dylib",
        ),
        "harfbuzz-subset": ("libharfbuzz-subset.dylib", "libharfbuzz-subset.0.dylib"),
        "harfbuzz-subset-0.0": (
            "libharfbuzz-subset.dylib",
            "libharfbuzz-subset.0.dylib",
        ),
        "libfontconfig-1": ("libfontconfig.dylib", "libfontconfig.1.dylib"),
        "fontconfig-1": ("libfontconfig.dylib", "libfontconfig.1.dylib"),
        "fontconfig": ("libfontconfig.dylib", "libfontconfig.1.dylib"),
        "libpangoft2-1.0-0": ("libpangoft2-1.0.dylib", "libpangoft2-1.0.0.dylib"),
        "pangoft2-1.0-0": ("libpangoft2-1.0.dylib", "libpangoft2-1.0.0.dylib"),
        "pangoft2-1.0": ("libpangoft2-1.0.dylib", "libpangoft2-1.0.0.dylib"),
        "libcairo": ("libcairo.dylib", "libcairo.2.dylib"),
        "cairo": ("libcairo.dylib", "libcairo.2.dylib"),
    }


def patch_cffi_dlopen(prefixes: Iterable[Path] | None = None) -> None:
    """Monkey patch cffi.FFI.dlopen to try absolute Homebrew paths on macOS."""
    if sys.platform != "darwin":
        return
    try:
        import cffi  # type: ignore
    except ImportError:
        return

    ffi_type = type(cffi.FFI())  # noqa: N806 - keep original naming
    if getattr(ffi_type.dlopen, "_accountingplus_patched", False):
        return

    lib_roots = tuple(str(prefix / "lib") for prefix in (prefixes or _existing_prefixes()))
    library_candidates = _macos_library_candidates()
    original_dlopen = ffi_type.dlopen

    def _fallback(name: str) -> Iterable[str]:
        candidates = library_candidates.get(name, ())
        for candidate in candidates:
            for root in lib_roots:
                candidate_path = Path(root) / candidate
                if candidate_path.exists():
                    yield str(candidate_path)
        if name.endswith("-0"):
            trimmed = f"{name[:-2]}.dylib"
            for root in lib_roots:
                candidate_path = Path(root) / trimmed
                if candidate_path.exists():
                    yield str(candidate_path)

    def patched_dlopen(self, name, flags=0):
        try:
            return original_dlopen(self, name, flags)
        except OSError as original_error:
            lookup = name.decode(errors="ignore") if isinstance(name, bytes) else str(name)
            for candidate in _fallback(lookup):
                try:
                    return original_dlopen(self, candidate, flags)
                except OSError:
                    continue
            raise original_error

    patched_dlopen._accountingplus_patched = True  # type: ignore[attr-defined]
    ffi_type.dlopen = patched_dlopen  # type: ignore[assignment]


def bootstrap() -> Tuple[Path, ...]:
    prefixes = configure_environment()
    patch_cffi_dlopen(prefixes)
    return prefixes


__all__ = ["bootstrap", "configure_environment", "patch_cffi_dlopen"]

