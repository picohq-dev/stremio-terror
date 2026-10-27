#!/usr/bin/env python3
"""Builds a static Stremio addon: one "Terror" catalog whose genre filter is the decade.

The movies come from public MDBList lists (no key needed). Output goes to site/,
which GitHub Pages serves as is.
"""
import json
import os
import shutil
import sys
import urllib.request

USER = "picohq"
DECADES = [
    ("Anos 50", "terror-anos-50"),
    ("Anos 60", "terror-anos-60"),
    ("Anos 70", "terror-anos-70"),
    ("Anos 80", "terror-anos-80"),
    ("Anos 90", "terror-anos-90"),
    ("Anos 2000", "terror-anos-2000"),
    ("Anos 2010", "terror-anos-2010"),
    ("Anos 2020", "terror-anos-2020"),
]
PAGE = 100  # Stremio asks for the next page with skip=100, 200...
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "site")

MANIFEST = {
    "id": "io.github.picohq-dev.terror",
    "version": "1.0.0",
    "name": "Terror por década",
    "description": "Filmes de terror por década, das listas do MDBList.",
    "resources": ["catalog"],
    "types": ["movie"],
    "catalogs": [{
        "type": "movie",
        "id": "terror",
        "name": "Terror",
        "extra": [
            # Required: the catalog lives in Discover only, not as another row on Home.
            {"name": "genre", "isRequired": True, "options": [d for d, _ in DECADES]},
            {"name": "skip", "isRequired": False},
        ],
        "extraRequired": ["genre"],
    }],
    "behaviorHints": {"configurable": False},
}


def fetch(slug):
    url = "https://mdblist.com/lists/%s/%s/json" % (USER, slug)
    req = urllib.request.Request(url, headers={"User-Agent": "stremio-terror/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        items = json.load(r)
    metas = []
    for it in items:
        imdb = it.get("imdb_id") or ""
        if not imdb.startswith("tt"):
            continue
        meta = {
            "id": imdb,
            "type": "movie",
            "name": it.get("title") or imdb,
            "poster": "https://images.metahub.space/poster/medium/%s/img" % imdb,
        }
        if it.get("release_year"):
            meta["releaseInfo"] = str(it["release_year"])
        metas.append(meta)
    return metas


def write(path, data):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    write("manifest.json", MANIFEST)
    open(os.path.join(OUT, ".nojekyll"), "w").close()
    for label, slug in DECADES:
        metas = fetch(slug)
        if not metas:
            sys.exit("%s came back empty" % slug)
        # The file name keeps the space: the server decodes the %20 the app sends.
        genre = "genre=" + label
        for skip in range(0, len(metas), PAGE):
            page = {"metas": metas[skip:skip + PAGE]}
            if skip == 0:
                write("catalog/movie/terror/%s.json" % genre, page)
            # Apps put the extras in either order.
            write("catalog/movie/terror/%s&skip=%d.json" % (genre, skip), page)
            write("catalog/movie/terror/skip=%d&%s.json" % (skip, genre), page)
        print("%-10s %5d filmes" % (label, len(metas)))


if __name__ == "__main__":
    main()
