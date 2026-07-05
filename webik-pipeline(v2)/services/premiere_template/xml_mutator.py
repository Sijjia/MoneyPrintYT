"""Read/mutate/write Premiere Pro .prproj files (gzipped XML)."""
from __future__ import annotations

import gzip
import re
import shutil
from collections import Counter
from dataclasses import dataclass
from pathlib import Path


# ---- low-level read/write -------------------------------------------------

def read_prproj(path: Path) -> str:
    """Decompress a .prproj and return the raw XML as a string."""
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return f.read()


def write_prproj(path: Path, xml: str) -> None:
    """Gzip-compress xml and save to path. Overwrites existing file."""
    with gzip.open(path, "wt", encoding="utf-8") as f:
        f.write(xml)


# ---- media swap -----------------------------------------------------------

# Inside a <Media> block, these point at the source file. We rewrite them.
PATH_FIELDS_FULL = (
    "FilePath",
    "ActualMediaFilePath",
)

# ConformedAudioPath / PeakFilePath point at Premiere's CACHE (.cfa/.pek in
# AppData), NOT at the source file. We BLANK them so Premiere regenerates the
# cache from the new media on next open.
CACHE_FIELDS = (
    "ConformedAudioPath",
    "PeakFilePath",
)

# Fingerprints that Premiere uses to verify a media file is the one it
# originally imported. If they don't match the new file, Premiere reports
# "Media offline". Blank them out so Premiere re-fingerprints.
FINGERPRINT_FIELDS = (
    "FileKey",
    "ContentAndMetadataState",
    "ModificationState",
)

# Fields that carry the basename only.
NAME_FIELDS = ("Name", "Title", "ClipName")

# RelativePath is recomputed by Premiere on re-open — we blank it.


@dataclass
class SwapResult:
    target_basename: str
    new_path: str
    replacements: dict[str, int]  # field name → count of replacements made

    def total(self) -> int:
        return sum(self.replacements.values())


def swap_media_path(xml: str, old_basename: str, new_path: str) -> tuple[str, SwapResult]:
    """Replace every reference to `old_basename` in the XML with `new_path`.

    `old_basename`: filename as it appears in <Name>/<Title>, e.g.
        "0_Earth_Night_1920x1080.mp4"
    `new_path`: absolute path to the new media file, e.g.
        r"C:\\Users\\aidar\\Downloads\\0_Earth_Planet_1920x1080 (2).mp4"

    Returns the mutated XML and a SwapResult tallying how many replacements
    were made per field.
    """
    new_basename = Path(new_path).name
    counts: dict[str, int] = {}

    # We scope every change to <Media> blocks that reference old_basename,
    # so swapping "earth.mp4" never touches an unrelated <Media> that happens
    # to also have a FileKey field.
    media_pat = re.compile(r"(<Media [^>]*>)(.*?)(</Media>)", re.DOTALL)

    def is_target(body: str) -> bool:
        return re.search(
            rf"<(?:FilePath|ActualMediaFilePath|Title|Name|ClipName)>[^<]*{re.escape(old_basename)}</",
            body,
        ) is not None

    def mutate_media(match: re.Match) -> str:
        head, body, tail = match.group(1), match.group(2), match.group(3)
        if not is_target(body):
            return match.group(0)

        # 1) full source path — use lambda to avoid backslash escapes in repl
        for field in PATH_FIELDS_FULL:
            replacement = f"<{field}>{new_path}</{field}>"
            body, n = re.subn(
                rf"<{field}>[^<]*</{field}>",
                lambda _m, r=replacement: r,
                body,
            )
            counts[field] = counts.get(field, 0) + n

        # 2) blank cache + fingerprint + relative path so Premiere regenerates
        for field in CACHE_FIELDS + FINGERPRINT_FIELDS + ("RelativePath",):
            empty = f"<{field}></{field}>"
            body, n = re.subn(
                rf"<{field}>[^<]*</{field}>",
                lambda _m, r=empty: r,
                body,
            )
            body, n2 = re.subn(
                rf"<{field}\b[^>]*>.*?</{field}>",
                lambda _m, r=empty: r,
                body,
                flags=re.DOTALL,
            )
            counts[field] = counts.get(field, 0) + n + n2

        # 3) basename fields
        for field in NAME_FIELDS:
            replacement = f"<{field}>{new_basename}</{field}>"
            body, n = re.subn(
                rf"<{field}>{re.escape(old_basename)}</{field}>",
                lambda _m, r=replacement: r,
                body,
            )
            counts[field] = counts.get(field, 0) + n

        return head + body + tail

    xml = media_pat.sub(mutate_media, xml)

    # Some basename references live OUTSIDE <Media> (e.g. inside
    # MasterClip <Name>, SubClip <Name>, <ClipName>). Rewrite those too.
    for field in NAME_FIELDS:
        replacement = f"<{field}>{new_basename}</{field}>"
        xml, n = re.subn(
            rf"<{field}>{re.escape(old_basename)}</{field}>",
            lambda _m, r=replacement: r,
            xml,
        )
        counts[f"{field}_outer"] = n

    # Drop zero-count keys for readability
    counts = {k: v for k, v in counts.items() if v}

    return xml, SwapResult(target_basename=old_basename, new_path=new_path, replacements=counts)


# ---- inspection -----------------------------------------------------------

@dataclass
class MediaRef:
    file_path: str | None
    title: str | None
    object_uid: str | None


def list_media_refs(xml: str) -> list[MediaRef]:
    """Return every <Media> block as a MediaRef with FilePath + Title + UUID."""
    out: list[MediaRef] = []
    for m in re.finditer(
        r'<Media ObjectUID="([0-9a-f-]+)"[^>]*>(.*?)</Media>',
        xml,
        re.DOTALL,
    ):
        uid = m.group(1)
        body = m.group(2)
        fp = re.search(r"<FilePath>([^<]*)</FilePath>", body)
        title = re.search(r"<Title>([^<]*)</Title>", body)
        out.append(
            MediaRef(
                file_path=fp.group(1) if fp else None,
                title=title.group(1) if title else None,
                object_uid=uid,
            )
        )
    return out


def safe_copy_prproj(src: Path, dst: Path) -> Path:
    """Copy a .prproj to a sibling/different path. Refuses to overwrite src."""
    src = Path(src)
    dst = Path(dst)
    if dst.resolve() == src.resolve():
        raise ValueError("Destination must differ from source")
    if dst.exists():
        dst.unlink()
    shutil.copy2(src, dst)
    return dst
