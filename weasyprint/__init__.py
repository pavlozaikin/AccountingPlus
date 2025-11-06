"""Shim package that ensures WeasyPrint sees Homebrew libraries on macOS."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Iterable, List

from accountingplus.weasyprint_support import bootstrap


def _collect_search_paths(current_package_dir: Path) -> List[str]:
    project_root = current_package_dir.parent.resolve()
    search_paths: List[str] = []
    for entry in sys.path:
        try:
            resolved = Path(entry or ".").resolve()
        except OSError:
            # Skip entries that can't be resolved (e.g. zipimport paths).
            continue
        if resolved == project_root:
            continue
        search_paths.append(str(resolved))
    return search_paths


def _load_original_weasyprint(search_paths: Iterable[str]) -> tuple[ModuleType, str]:
    module_name = __name__
    for entry in search_paths:
        try:
            spec = importlib.machinery.PathFinder.find_spec(module_name, [entry])
        except (ImportError, AttributeError):
            continue
        if spec is None or spec.loader is None:
            continue
        origin = getattr(spec, "origin", None)
        submodule_locations = getattr(spec, "submodule_search_locations", None)
        if origin is None:
            continue
        package_dir = Path(origin).resolve().parent
        if package_dir == Path(__file__).resolve().parent:
            # Skip our shim package.
            continue
        real_name = f"_{module_name}_real"
        real_spec = importlib.util.spec_from_file_location(
            real_name,
            origin,
            submodule_search_locations=submodule_locations,
        )
        if real_spec is None or real_spec.loader is None:
            continue
        module = importlib.util.module_from_spec(real_spec)
        sys.modules[real_name] = module
        real_spec.loader.exec_module(module)
        return module, real_name
    raise ImportError("Failed to locate the original WeasyPrint package.")


def _apply_real_module(real: ModuleType, alias_name: str) -> None:
    shim = sys.modules[__name__]
    shim_dict = shim.__dict__
    real_dict = real.__dict__

    # Remove previously injected symbols except the mandatory module metadata.
    for key in list(shim_dict.keys()):
        if key in {"__name__", "__package__", "__loader__", "__spec__", "__path__", "__file__"}:
            continue
        if key.startswith("_accountingplus"):
            continue
        shim_dict.pop(key, None)

    # Copy the real module content into the shim.
    for key, value in real_dict.items():
        if key == "__name__":
            continue
        shim_dict[key] = value

    # Ensure module metadata points to the real implementation.
    for meta in ("__doc__", "__all__", "__package__", "__file__", "__path__", "__loader__", "__spec__"):
        if hasattr(real, meta):
            shim_dict[meta] = getattr(real, meta)

    import sys as _cleanup_sys

    _cleanup_sys.modules.pop(alias_name, None)


bootstrap()
_search_paths = _collect_search_paths(Path(__file__).resolve().parent)
_real_module, _alias_name = _load_original_weasyprint(_search_paths)
_apply_real_module(_real_module, _alias_name)
