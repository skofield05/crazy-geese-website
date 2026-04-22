"""
Schema- und Asset-Check fuer data/data.json.

Nutzung (aus dem Repo-Root):
    python scripts/validate_data.py

Exitcode 0 = alles ok, 1 = Fehler gefunden.
"""
from __future__ import annotations

import datetime
import json
import pathlib
import sys


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_FILE = REPO_ROOT / "data" / "data.json"

REQUIRED_POST_FIELDS = ("slug", "url", "titel", "datum")


def _is_valid_date(s: str) -> bool:
    try:
        datetime.date.fromisoformat(s)
        return True
    except (TypeError, ValueError):
        return False


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"FAIL: data.json ist kein valides JSON: {e}")
        return 1

    _check_blog(data.get("blog"), errors, warnings)
    _check_spiele(data.get("spiele"), errors, warnings)

    for w in warnings:
        print(f"WARN: {w}")
    for e in errors:
        print(f"FAIL: {e}")

    if errors:
        print(f"\n{len(errors)} Fehler, {len(warnings)} Warnungen.")
        return 1
    print(f"OK: data.json valide, {len(warnings)} Warnungen.")
    return 0


def _check_blog(blog: object, errors: list[str], warnings: list[str]) -> None:
    if blog is None:
        warnings.append("blog-Key fehlt in data.json (kein Blog konfiguriert).")
        return
    if not isinstance(blog, dict):
        errors.append("blog muss ein Objekt sein.")
        return

    posts = blog.get("posts", [])
    if not isinstance(posts, list):
        errors.append("blog.posts muss ein Array sein.")
        return

    slugs: set[str] = set()
    for i, post in enumerate(posts):
        where = f"blog.posts[{i}]"
        if not isinstance(post, dict):
            errors.append(f"{where} muss ein Objekt sein.")
            continue

        for field in REQUIRED_POST_FIELDS:
            if not post.get(field):
                errors.append(f"{where}.{field} fehlt oder ist leer.")

        slug = post.get("slug")
        if slug:
            if slug in slugs:
                errors.append(f"{where}.slug '{slug}' ist nicht eindeutig.")
            slugs.add(slug)

        datum = post.get("datum")
        if datum and not _is_valid_date(datum):
            errors.append(f"{where}.datum '{datum}' – erwarte gueltiges YYYY-MM-DD.")

        for path_field in ("url", "cover"):
            p = post.get(path_field)
            if not p:
                continue
            full = REPO_ROOT / p
            if not full.exists():
                errors.append(f"{where}.{path_field} -> {p} existiert nicht.")

        if post.get("cover") and not post.get("cover_alt"):
            warnings.append(f"{where}: cover vorhanden, aber cover_alt fehlt (Barrierefreiheit).")


def _check_spiele(spiele: object, errors: list[str], warnings: list[str]) -> None:
    if not isinstance(spiele, dict):
        return
    for bucket in ("naechste", "vergangene"):
        games = spiele.get(bucket, [])
        if not isinstance(games, list):
            errors.append(f"spiele.{bucket} muss ein Array sein.")
            continue
        for i, g in enumerate(games):
            where = f"spiele.{bucket}[{i}]"
            if not isinstance(g, dict):
                errors.append(f"{where} muss ein Objekt sein.")
                continue
            for field in ("datum", "heim", "gast"):
                if not g.get(field):
                    errors.append(f"{where}.{field} fehlt.")
            datum = g.get("datum")
            if datum and not _is_valid_date(datum):
                errors.append(f"{where}.datum '{datum}' – erwarte gueltiges YYYY-MM-DD.")


if __name__ == "__main__":
    sys.exit(main())
