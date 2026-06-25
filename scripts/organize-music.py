"""Organize Music/ into Artist/Album (Year)/Title.ext using embedded tags."""
from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

from mutagen import File as MutagenFile

ROOT = Path(__file__).resolve().parents[2] / "Documents" / "Music"
UNSORTED = ROOT / "Unsorted"
AUDIO_EXTS = {".flac", ".opus", ".mp3", ".ogg", ".m4a"}
INVALID = re.compile(r'[<>:"/\\|?*]')
COVER_HINT = re.compile(r"cover|kuu amane", re.I)


def load_tags(path: Path) -> dict:
    audio = MutagenFile(path, easy=True)
    if audio is None:
        raise ValueError(f"could not read tags: {path}")

    def get(key: str, default: str = "") -> str:
        val = audio.get(key)
        if not val:
            return default
        return val[0].strip() if isinstance(val[0], str) else str(val[0]).strip()

    return {
        "artist": get("albumartist") or get("artist") or "Unknown Artist",
        "album": get("album") or "Unknown Album",
        "title": get("title") or path.stem,
        "track": get("tracknumber", "0").split("/")[0],
        "date": get("date"),
    }


def year_from_date(date: str) -> str:
    m = re.match(r"(\d{4})", date or "")
    return m.group(1) if m else ""


def sanitize(name: str) -> str:
    cleaned = INVALID.sub("_", name).strip().rstrip(".")
    return cleaned or "untitled"


def target_for(path: Path, tags: dict) -> Path:
    artist = tags["artist"]
    album = tags["album"]
    title = tags["title"]
    year = year_from_date(tags["date"])

    parent_name = path.parent.name
    if parent_name.startswith("Covers - "):
        artist = "Kuu Amane"
        album_dir = parent_name
        filename = f"{sanitize(title)}{path.suffix.lower()}"
        return ROOT / sanitize(artist) / album_dir / filename

    if COVER_HINT.search(path.name):
        artist = "Kuu Amane"
        album = f"Covers - {album}"

    album_dir = sanitize(album)
    if year:
        album_dir = f"{album_dir} ({year})"

    filename = f"{sanitize(title)}{path.suffix.lower()}"
    return ROOT / sanitize(artist) / album_dir / filename


def iter_sources(unsorted_only: bool, include_unsorted: bool):
    if unsorted_only:
        if not UNSORTED.is_dir():
            return
        yield from sorted(UNSORTED.rglob("*"))
        return

    for path in sorted(ROOT.rglob("*")):
        if not include_unsorted and (UNSORTED in path.parents or path == UNSORTED):
            continue
        yield path


def main() -> None:
    parser = argparse.ArgumentParser(description="Sort audio files in Documents/Music")
    parser.add_argument(
        "--unsorted-only",
        action="store_true",
        help="Only process files under Music/Unsorted/ (default: process entire library except Unsorted)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process entire library including Unsorted/",
    )
    args = parser.parse_args()

    unsorted_only = args.unsorted_only
    include_unsorted = args.all
    if not args.all and not args.unsorted_only and UNSORTED.is_dir():
        unsorted_only = True

    moves: list[tuple[Path, Path]] = []

    for path in iter_sources(unsorted_only, include_unsorted):
        if not path.is_file():
            continue
        if path.suffix.lower() not in AUDIO_EXTS:
            continue

        tags = load_tags(path)
        dest = target_for(path, tags)
        if path.resolve() != dest.resolve():
            moves.append((path, dest))

    if not moves:
        print("Nothing to move.")
    else:
        for src, dest in moves:
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                raise SystemExit(f"Refusing to overwrite: {dest}")
            print(f"{src.relative_to(ROOT)}")
            print(f"  -> {dest.relative_to(ROOT)}")
            shutil.move(str(src), str(dest))

    # Remove empty folders (deepest first), keep Unsorted/ as staging area.
    for path in sorted(
        (p for p in ROOT.rglob("*") if p.is_dir() and p != UNSORTED),
        key=lambda p: len(p.parts),
        reverse=True,
    ):
        if path == ROOT:
            continue
        try:
            path.rmdir()
            print(f"Removed empty folder: {path.relative_to(ROOT)}")
        except OSError:
            pass

    UNSORTED.mkdir(exist_ok=True)

    junk = ROOT / "_inventory.json"
    if junk.exists():
        junk.unlink()
        print("Removed _inventory.json")


if __name__ == "__main__":
    main()
