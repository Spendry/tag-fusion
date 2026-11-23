"""Re-check every listing in data/catalog.json.

    python tools/check_links.py

Fetches each address once and prints only the listings that need a look: an error, a
redirect to a different domain (a lapsed domain bought by someone else looks like this),
or words on the page that the directory refuses. A word hit is a reason to look, not a
verdict; read the page. Standard library only.
"""
import concurrent.futures as cf
import gzip
import html
import json
import re
import urllib.error
import urllib.request
import zlib
from pathlib import Path
from urllib.parse import urlparse

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
WORDS = {
    "adult": r"\b(porn\w*|xxx|nsfw|hentai|onlyfans|escorts?|camgirls?|erotic\w*)\b",
    "gambling": r"\b(casinos?|betting|sportsbook|slots|jackpot)\b",
    "drugs": r"\b(peptides?|semaglutide|tirzepatide|steroids|sarms|research use only|viagra|cialis)\b",
    "for sale": r"(domain (is )?for sale|buy this domain|this domain may be for sale|hugedomains|sedo\.com)",
    "closed": r"\b(shut(ting)? down|no longer (available|maintained)|discontinued)\b",
}


def base(host):
    return ".".join((host or "").removeprefix("www.").split(".")[-2:])


def check(site):
    url, notes = site["url"], []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html,*/*", "Accept-Encoding": "gzip, deflate"})
        with urllib.request.urlopen(req, timeout=25) as r:
            body, enc, final = r.read(600_000), r.headers.get("Content-Encoding", ""), r.geturl()
        if "gzip" in enc:
            body = gzip.decompress(body)
        elif "deflate" in enc:
            body = zlib.decompress(body)
    except urllib.error.HTTPError as e:
        hint = " (often only means the site blocks scripts; open it in a browser)" if e.code == 403 else ""
        return site["name"], url, [f"HTTP {e.code}{hint}"]
    except Exception as e:
        return site["name"], url, [f"no answer: {type(e).__name__}"]
    if base(urlparse(final).hostname) != base(urlparse(url).hostname):
        notes.append(f"now leads to {urlparse(final).hostname}")
    text = body.decode("utf-8", errors="replace")
    text = html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<script.*?</script>|<style.*?</style>", " ", text, flags=re.S | re.I)))
    for label, pattern in WORDS.items():
        found = sorted({m.group(0).lower() for m in re.finditer(pattern, text, re.I)})
        if found:
            notes.append(f"{label}: {', '.join(found[:5])}")
    return site["name"], url, notes


if __name__ == "__main__":
    sites = json.loads((Path(__file__).parent.parent / "data" / "catalog.json").read_text(encoding="utf-8"))
    with cf.ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(check, sites))
    flagged = [r for r in results if r[2]]
    for name, url, notes in flagged:
        print(f"{name}\n  {url}\n  " + "\n  ".join(notes))
    print(f"\n{len(sites)} listings checked, {len(flagged)} to look at.")
