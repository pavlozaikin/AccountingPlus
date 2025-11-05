from __future__ import annotations

import re
from collections import OrderedDict
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List, MutableMapping, Optional, Set

from django.conf import settings

OBLAST_FROM_HEADING: Dict[str, str] = {
    "Житомирський ОТЦК та СП": "Житомирська область",
    "Київський МТЦК та СП": "м. Київ",
    "Київський ОТЦК та СП": "Київська область",
    "Полтавський ОТЦК та СП": "Полтавська область",
    "Сумський ОТЦК та СП": "Сумська область",
    "Черкаський ОТЦК та СП": "Черкаська область",
    "Чернігівський ОТЦК та СП": "Чернігівська область",
    "Чернігівський РТЦК та СП": "Чернігівська область",
    "Ніжинський РТЦК та СП": "Чернігівська область",
    "Прилуцький РТЦК та СП": "Чернігівська область",
    "Корюківський РТЦК та СП": "Чернігівська область",
    "Новгород-Сіверський РТЦК та СП": "Чернігівська область",
    "Одеський ОТЦК та СП": "Одеська область",
    "Херсонський ОТЦК та СП": "Херсонська область",
    "Миколаївський ОТЦК та СП": "Миколаївська область",
    "Вінницький ОТЦК та СП": "Вінницька область",
    "Кіровоградський ОТЦК та СП": "Кіровоградська область",
    "Волинський ОТЦК та СП": "Волинська область",
    "Закарпатський ОТЦК та СП": "Закарпатська область",
    "Івано-Франківський ОТЦК та СП": "Івано-Франківська область",
    "Львівський ОТЦК та СП": "Львівська область",
    "Рівненський ОТЦК та СП": "Рівненська область",
    "Тернопільський ОТЦК та СП": "Тернопільська область",
    "Хмельницький ОТЦК та СП": "Хмельницька область",
    "Чернівецький ОТЦК та СП": "Чернівецька область",
    "Дніпропетровський ОТЦК та СП": "Дніпропетровська область",
    "Донецький ОТЦК та СП": "Донецька область",
    "Луганський ОТЦК та СП": "Луганська область",
    "Харківський ОТЦК та СП": "Харківська область",
    "Запорізький ОТЦК та СП": "Запорізька область",
}

EXCLUDED_TCK_NAMES: Set[str] = {"Вінницький обʼєднаний міський ТЦК та СП"}


def _strip_contact_value(value: str) -> str:
    """Return the value without surrounding whitespace and NBSP characters."""

    return value.strip().replace("\xa0", " ")


def _normalise_tel_href(value: str) -> str:
    """Prepare a value that can be safely used in a tel: hyperlink."""

    cleaned = re.sub(r"[^0-9+]", "", value)
    return cleaned


def _get_data_file() -> Path:
    return Path(settings.BASE_DIR) / "data" / "tckdataforlist.md"


@lru_cache(maxsize=1)
def get_tck_reference_data() -> List[Dict[str, object]]:
    """Parse the Markdown data file and return structured contact data."""

    data_file = _get_data_file()
    if not data_file.exists():
        return []

    oblasts: MutableMapping[str, Dict[str, object]] = OrderedDict()
    current_oblast: Optional[Dict[str, object]] = None
    current_entry: Optional[Dict[str, object]] = None
    current_section: Optional[Dict[str, object]] = None

    for raw_line in data_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("### "):
            title = line[4:].strip()
            if current_oblast is None:
                continue
            current_entry = {"title": title, "sections": []}
            current_oblast["entries"].append(current_entry)
            current_section = None
            continue

        if line.startswith("## "):
            title = line[3:].strip()
            if current_oblast is None:
                continue
            current_entry = {"title": title, "sections": []}
            current_oblast["entries"].append(current_entry)
            current_section = None
            continue

        if line.startswith("# "):
            title = line[2:].strip()
            oblast_name = OBLAST_FROM_HEADING.get(title)
            if oblast_name is None:
                oblast_name = title
            current_oblast = oblasts.setdefault(
                oblast_name, {"name": oblast_name, "entries": []}
            )
            current_entry = {"title": title, "sections": []}
            current_oblast["entries"].append(current_entry)
            current_section = None
            continue

        if line.startswith("#### "):
            if current_entry is None:
                continue
            heading = line[5:].strip()
            section_title = heading.rstrip(":")
            section_type = "email" if "email" in section_title.lower() else "phone"
            current_section = {
                "title": section_title,
                "type": section_type,
                "items": [],
            }
            current_entry["sections"].append(current_section)
            continue

        if current_section is None:
            continue

        value = _strip_contact_value(line)
        if not value:
            continue

        if current_section["type"] == "email":
            item = {"text": value, "href": f"mailto:{value}"}
        else:
            href_value = _normalise_tel_href(value)
            item = {"text": value, "href": f"tel:{href_value}"}
        current_section["items"].append(item)

    return list(oblasts.values())


def count_tck_entries(regions: Iterable[Dict[str, object]]) -> int:
    """Return the total number of individual ТЦК entries across all regions."""

    return sum(len(region.get("entries", [])) for region in regions)


@lru_cache(maxsize=1)
def get_tck_names() -> List[str]:
    """Return the ordered list of unique ТЦК назв sourced from the data file."""

    regions = get_tck_reference_data()
    seen: Set[str] = set()
    names: List[str] = []
    for region in regions:
        for entry in region.get("entries", []):
            title = str(entry.get("title") or "").strip()
            if not title or title in seen or title in EXCLUDED_TCK_NAMES:
                continue
            seen.add(title)
            names.append(title)
    return names
