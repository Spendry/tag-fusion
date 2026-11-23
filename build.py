"""Build TagFusion as plain static pages.

    python build.py

Reads data/catalog.json and static/, writes the whole site into docs/ (the folder
GitHub Pages serves). Python standard library only; nothing is installed and nothing
keeps running. To add or change a listing, edit data/catalog.json and run this again.
"""
import json
import re
import shutil
import unicodedata
from collections import Counter
from datetime import date
from html import escape
from itertools import combinations
from pathlib import Path
from urllib.parse import urlparse

HERE = Path(__file__).parent
OUT = HERE / "docs"

# ---- Settings Sam fills in -------------------------------------------------------------
SITE = "https://halfhumandraft.com"
DOMAIN = ""                               # the custom domain, written to docs/CNAME; "" serves from github.io
REPO = "https://github.com/Spendry/tag-fusion"
CONTACT_EMAIL = ""                        # shown on the Contact page when set
OPERATOR = ""                             # the name shown as who runs the site, when set
UPDATED = date.today().strftime("%B %d, %Y").replace(" 0", " ")
# ----------------------------------------------------------------------------------------

SUGGEST = f"{REPO}/issues/new?template=suggest-a-website.yml"
REPORT = f"{REPO}/issues/new?template=report-a-listing.yml"
CATEGORIES = [
    ("Creative tools", "✦", "Make, remix, and publish", "Places to make, remix, or publish something."),
    ("Learn & think", "◌", "Ideas worth following", "Explanations, references, research, and ideas."),
    ("Independent web", "⌁", "Small corners of the internet", "Small, personal, and community-made corners."),
    ("Play & wander", "⊹", "Delightful distractions", "Games, experiments, and delightful detours."),
]
REFUSED = "adult material, gambling, the sale or dosing of drugs, piracy, malware, scams, or hate"


def slugify(value):
    value = unicodedata.normalize("NFKD", value.lower())
    return re.sub(r"[\s_-]+", "-", re.sub(r"[^\w\s-]", "", value).strip())


def domain_of(url):
    return urlparse(url).hostname.removeprefix("www.")


def plural(n, word):
    return f"{n} {word}{'' if n == 1 else 's'}"


sites = json.loads((HERE / "data" / "catalog.json").read_text(encoding="utf-8"))
for s in sites:
    assert s["category"] in [c[0] for c in CATEGORIES], s["name"]
    assert s["url"].startswith("https://") and s["tags"], s["name"]
tag_counts = Counter(t for s in sites for t in s["tags"])
TAGS = sorted(tag_counts, key=lambda t: (-tag_counts[t], t))
pair_counts = Counter(p for s in sites for p in combinations(sorted(s["tags"]), 2))
pages = []  # (path, in sitemap)


def chip_link(tag, root, count=False):
    extra = f" <small>{tag_counts[tag]}</small>" if count else ""
    return f'<li><a class="chip" href="{root}tag/{slugify(tag)}/">#{escape(tag)}{extra}</a></li>'


def card(s, root):
    chips = "".join(chip_link(t, root) for t in s["tags"])
    return (f'<li class="card"><h3><a href="{escape(s["url"])}" target="_blank" rel="noopener noreferrer">{escape(s["name"])}</a></h3>'
            f'<p class="where">{escape(domain_of(s["url"]))} · <a href="{root}category/{slugify(s["category"])}/">{escape(s["category"])}</a></p>'
            f'<p>{escape(s["description"])}</p><ul class="chips">{chips}</ul></li>')


def cards(items, root):
    return '<ul class="cards">' + "".join(card(s, root) for s in items) + "</ul>"


NAV = [("", "Explore"), ("search/", "Search"), ("field-guide/", "Field guide"), ("about/", "About")]
FOOT = [("about/", "About"), ("about/#editorial-policy", "Editorial policy"), ("contact/", "Contact"),
        ("privacy/", "Privacy"), ("terms/", "Terms")]


def write(path, title, description, body, *, sitemap=True, script=False, robots=None, canonical=True):
    depth = 0 if path in ("", "404.html") else path.strip("/").count("/") + 1
    root = "../" * depth
    if path == "404.html":
        root = "/"  # a 404 can be served at any depth
    url = f"{SITE}/{path}" if path != "404.html" else SITE + "/"

    def nav(cls):
        links = "".join(f'<a href="{root}{href}"{" aria-current=\"page\"" if href == path else ""}>{label}</a>' for href, label in NAV)
        return f'<nav class="nav {cls}" aria-label="Main">{links}<a href="{SUGGEST}">Suggest a website</a></nav>'

    foot = "".join(f'<a href="{root}{href}">{label}</a>' for href, label in FOOT)
    head_extra = ""
    if canonical and path != "404.html":
        head_extra += f'<link rel="canonical" href="{url}">\n'
    if robots:
        head_extra += f'<meta name="robots" content="{robots}">\n'
    if path == "":
        ld = {"@context": "https://schema.org", "@type": "WebSite", "name": "TagFusion", "url": SITE + "/",
              "description": "A hand-picked directory of independent websites, browsed by category and tag.",
              "potentialAction": {"@type": "SearchAction", "target": SITE + "/search/?q={search_term_string}",
                                  "query-input": "required name=search_term_string"}}
        head_extra += f'<script type="application/ld+json">{json.dumps(ld)}</script>\n'
    js = f'<script src="{root}site.js" data-root="{root}" defer></script>\n' if script else ""
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data:; script-src 'self'; base-uri 'self'; form-action 'self'">
<meta name="referrer" content="strict-origin-when-cross-origin">
<title>{escape(title)}</title>
<meta name="description" content="{escape(description)}">
{head_extra}<meta property="og:type" content="website">
<meta property="og:site_name" content="TagFusion">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(description)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/tagfusion-og.webp">
<meta property="og:image:alt" content="TagFusion invites visitors to follow curious paths through independent websites.">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{root}favicon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=DM+Sans:opsz,wght@9..40,400..700&family=Lora:ital,wght@0,400..700;1,400..700&display=swap">
<link rel="stylesheet" href="{root}site.css">
{js}</head>
<body>
<a class="skip" href="#main">Skip to content</a>
<header class="site-header"><div class="wrap">
<a class="brand" href="{root}">Tag<span>Fusion</span></a>
{nav("desktop")}
<details class="menu"><summary>Menu</summary>{nav("mobile")}</details>
</div></header>
<main id="main">
{body}
</main>
<footer class="site-footer"><div class="wrap">
<p>TagFusion. Made for curious people, not perfect queries.</p>
<nav class="nav" aria-label="Footer">{foot}<a href="{REPO}">Source</a></nav>
</div></footer>
</body>
</html>
"""
    target = OUT / path if path.endswith(".html") else OUT / path / "index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(html, encoding="utf-8", newline="\n")
    if sitemap:
        pages.append(path)


def prose(eyebrow, heading, inner):
    return f'<div class="wrap narrow prose"><p class="eyebrow">{eyebrow}</p><h1>{heading}</h1>{inner}</div>'


# ---- Home ------------------------------------------------------------------------------
def home():
    root = ""
    tiles = "".join(
        f'<li><a class="tile" href="category/{slugify(name)}/"><span class="glyph" aria-hidden="true">{glyph}</span>'
        f'<strong>{escape(name)}</strong><small>{escape(line)} · {sum(s["category"] == name for s in sites)} places</small></a></li>'
        for name, glyph, line, _ in CATEGORIES)
    buttons = "".join(f'<li><button type="button" class="chip" data-tag="{escape(t)}" aria-pressed="false">#{escape(t)} <small>{tag_counts[t]}</small></button></li>' for t in TAGS)
    options = "".join(f'<option value="{escape(c[0])}">{escape(c[0])}</option>' for c in CATEGORIES)
    trails = "".join(
        f'<li><a class="chip" href="?tags={escape(a)},{escape(b)}#explore">{escape(a)} + {escape(b)} <small>{n}</small></a></li>'
        for (a, b), n in pair_counts.most_common(6))
    sample = [s for s in sites if s["name"] in ("Neocities", "Zoomquilt", "Submarine Cable Map", "Strudel", "Standard Ebooks", "The Pudding")]
    all_tags = "".join(chip_link(t, root, count=True) for t in TAGS)
    body = f"""<div class="wrap">
<section class="hero">
<p class="eyebrow">A different way to browse</p>
<h1>Follow your <em>curiosity.</em></h1>
<p class="lede">The web is bigger than a search box. TagFusion is a hand-picked directory of {len(sites)} independent websites. Combine categories and tags to find places you did not know to look for.</p>
<form class="row" action="search/" method="get" role="search">
<label class="sr" for="home-q">Search the directory</label>
<input type="search" id="home-q" name="q" placeholder="Try ‘maps’, ‘writing’, or a site name">
<button class="btn" type="submit">Search directory</button>
</form>
</section>

<section aria-labelledby="mood">
<p class="eyebrow">Start anywhere</p>
<h2 id="mood">What are you in the mood for?</h2>
<p class="muted">Browse broad, then get specific. Every tag opens another door.</p>
<ul class="tiles">{tiles}</ul>
</section>

<section id="explore" aria-labelledby="path-title">
<p class="eyebrow">Build your path</p>
<h2 id="path-title">The best discoveries are a little unexpected.</h2>
<p class="muted">Pick tags to combine. A place stays in the list only when it carries every tag you chose.</p>
<div id="path" hidden>
<div class="row">
<label class="sr" for="path-category">Category</label>
<select id="path-category"><option value="">Any category</option>{options}</select>
<button type="button" class="btn ghost" id="path-surprise">Surprise me</button>
<button type="button" class="btn ghost" id="path-clear">Clear</button>
</div>
<ul class="chips" aria-label="Tags to combine">{buttons}</ul>
<p id="path-status" class="count" role="status" aria-live="polite"></p>
<ul class="cards" id="path-results"></ul>
</div>
<noscript><p class="note">Combining tags needs JavaScript. Every tag and category below is also a plain page.</p></noscript>
<h3>Trails that often cross</h3>
<ul class="chips">{trails}</ul>
</section>

<section aria-labelledby="sample">
<p class="eyebrow">A small sample</p>
<h2 id="sample">Which sites are worth wandering into?</h2>
{cards(sample, root)}
</section>

<section aria-labelledby="alltags">
<h2 id="alltags">Every tag</h2>
<ul class="chips">{all_tags}</ul>
</section>

<section aria-labelledby="share">
<p class="eyebrow">Go and find more websites to share</p>
<h2 id="share">Know a place that belongs here?</h2>
<p>Suggestions are read by a person before anything is listed. <a href="{SUGGEST}">Suggest a website</a>, or <a href="{REPORT}">report a listing</a> that is broken or no longer fits.</p>
</section>
</div>"""
    write("", "Find a New Path Through the Web | TagFusion",
          "Find independent websites, creative tools, and useful reading through hand-picked categories and combinable tags.", body, script=True)


# ---- Tag and category pages ------------------------------------------------------------
def listing_pages():
    for tag in TAGS:
        items = [s for s in sites if tag in s["tags"]]
        near = Counter(t for s in items for t in s["tags"] if t != tag).most_common(6)
        paired = "".join(chip_link(t, "../../") for t, _ in near)
        body = (f'<div class="wrap"><section class="hero"><p class="eyebrow">Tag</p><h1>#{escape(tag)}</h1>'
                f'<p class="lede">{plural(len(items), "place")} tagged {escape(tag)}.</p></section>'
                f'{cards(items, "../../")}'
                + (f'<section><h2>Often paired with</h2><ul class="chips">{paired}</ul></section>' if paired else "") + "</div>")
        write(f"tag/{slugify(tag)}/", f"Websites tagged {tag} | TagFusion",
              f"{plural(len(items), 'independent website')} tagged {tag}, each picked by hand, with a short description and related tags.", body)
    for name, _, _, blurb in CATEGORIES:
        items = [s for s in sites if s["category"] == name]
        top = Counter(t for s in items for t in s["tags"]).most_common(10)
        chips = "".join(chip_link(t, "../../") for t, _ in top)
        body = (f'<div class="wrap"><section class="hero"><p class="eyebrow">Category</p><h1>{escape(name)}</h1>'
                f'<p class="lede">{escape(blurb)} {plural(len(items), "place")}.</p>'
                f'<ul class="chips">{chips}</ul></section>{cards(items, "../../")}</div>')
        write(f"category/{slugify(name)}/", f"{name} websites | TagFusion",
              f"{blurb} {plural(len(items), 'hand-picked website')} in {name} on TagFusion.", body)


# ---- Search ----------------------------------------------------------------------------
def search():
    body = """<div class="wrap"><section class="hero">
<p class="eyebrow">Directory search</p>
<h1>Search TagFusion</h1>
<p class="lede">Look through the listings by website name, description, category, or tag.</p>
<form class="row" id="search-form" action="" method="get" role="search">
<label class="sr" for="q">Search the directory</label>
<input type="search" id="q" name="q" placeholder="Try ‘maps’, ‘writing’, or a site name">
<button class="btn" type="submit">Search directory</button>
</form>
<p id="search-status" class="count" role="status" aria-live="polite"></p>
</section>
<ul class="cards" id="search-results"></ul>
<noscript><p class="note">Search needs JavaScript. You can still browse every <a href="../#alltags">tag</a> and category as plain pages.</p></noscript>
</div>"""
    write("search/", "Search the TagFusion Directory", "Search TagFusion's hand-picked listings by name, description, category, or tag.", body, script=True)


# ---- Prose pages -----------------------------------------------------------------------
def about():
    who = f"TagFusion is run by one person, {escape(OPERATOR)}." if OPERATOR else "TagFusion is run by one person."
    inner = f"""
<h2>What is TagFusion?</h2>
<p>TagFusion is a public directory for discovering independent, creative, educational, and playful websites. Visitors browse broad categories, combine descriptive tags, read a short explanation, and then decide whether a destination deserves a closer look. The goal is to make it easier to follow an interest into a neighboring one, not to replace a general-purpose search engine.</p>
<h2>Who runs it?</h2>
<p>{who} That person picks the listings, writes the descriptions, keeps the tags, and reads every suggestion. This is practical experience with this directory, not a claim of expertise in every subject its listings cover.</p>
<h2>How are suggestions reviewed?</h2>
<p>Anyone can <a href="{SUGGEST}">suggest a site</a> with its name, address, a short description, a category, and up to four tags. Suggestions are public and are read before anything is listed. A site is listed when it fits the directory, has a clear purpose, and its link works.</p>
<h2 id="editorial-policy">Editorial policy</h2>
<p>TagFusion is a discovery directory, not a safety check or expert review service. Categories and tags describe what a site offers; they do not verify every claim on that site.</p>
<p>TagFusion does not list sites whose main content is {REFUSED}. Some listings are platforms where other people publish their own work, or directories that link onward; those are doors, not vetted pages, and what lies behind them is not reviewed.</p>
<p>Every listing is re-checked on a schedule, because web addresses change hands. A listing is removed when its address stops working, starts leading somewhere else, or no longer fits. In November 2026 nine listings were removed in such a check.</p>
<p>There are no paid placements today. If one is ever shown, it will be labelled “Sponsor” and kept apart from the listings.</p>
<h2>How should visitors use a listing?</h2>
<p>Treat each result as a starting point. Check who runs the site and verify important claims with original sources. TagFusion does not guarantee that an external site is current, accurate, secure, accessible, or right for a particular decision.</p>
<p>If a listing is broken, misleading, or out of date, <a href="{REPORT}">report it</a> or use the <a href="../contact/">contact page</a>.</p>"""
    write("about/", "About TagFusion | How the directory works",
          "What TagFusion is, who runs it, how suggestions are reviewed, and what the directory will not list.",
          prose("About TagFusion", "A human-scale way to find the web.", inner))


def field_guide():
    cats = "".join(f"<li><strong>{escape(n)}.</strong> {escape(b)}</li>" for n, _, _, b in CATEGORIES)
    inner = f"""
<p class="muted">Updated {UPDATED}.</p>
<p>TagFusion helps you find independent websites through broad topics and smaller labels. Pick a category, then choose tags that describe what you want. Each added tag narrows the list. Open a result and decide for yourself whether it is useful.</p>
<p>Search works well when you already know what to ask for. Browsing can help when you do not. Tags can connect topics that are often kept apart, such as maps and history or poetry and sound. Treat each result as a lead to check, not a recommendation.</p>
<h2>How do categories and tags work together?</h2>
<p>Categories show the broad kind of website. Tags name a subject or quality. A listing stays in the results only when it has every tag you chose.</p>
<ul>{cats}</ul>
<h2>What does a listing tell you?</h2>
<p>That a person looked at the site, found it worth a visit, and described it. It does not check the site’s safety, accuracy, or privacy, and a site can change after it is listed.</p>
<h2>How can you assess an unfamiliar website?</h2>
<p>Before relying on a new site, ask a few simple questions:</p>
<ul>
<li>Does it say who made it and what it is for?</li>
<li>Do important claims link to sources you can check?</li>
<li>Can you read its privacy rules before sharing personal details?</li>
<li>Can you tell ads apart from independent recommendations?</li>
<li>Does the page still work, and does it match the directory description?</li>
</ul>
<p>A Stanford study of how people judge websites found that readers look for who is behind a site and whether its claims are sourced (<a href="https://credibility.stanford.edu/pdf/p61-fogg.pdf" target="_blank" rel="noopener noreferrer">Fogg and colleagues, 2001</a>). For health, money, legal, or safety decisions, check an official source or ask a qualified professional. TagFusion is a starting point, not professional advice.</p>
<h2>What do visitors often ask?</h2>
<dl class="faq">
<dt>How do I search the directory?</dt>
<dd>Open <a href="../search/">Search</a> to look through the listings by name, description, category, or tag.</dd>
<dt>How do tags work?</dt>
<dd>Choose one or more tags. A result must have every tag you chose, so each new tag makes the list smaller.</dd>
<dt>Does a listing mean TagFusion recommends a site?</dt>
<dd>No. A listing is a place to start exploring. Check the destination yourself, especially before sharing personal details or relying on important information.</dd>
<dt>How can I suggest a website?</dt>
<dd>Use <a href="{SUGGEST}">Suggest a website</a> and give its name, address, a short description, a category, and up to four tags. A person reads each suggestion before anything is listed.</dd>
<dt>Do I need an account?</dt>
<dd>No. TagFusion has no accounts. Suggesting a site goes through GitHub, which has its own.</dd>
</dl>
<p><a class="btn" href="../#explore">Start exploring</a></p>"""
    write("field-guide/", "A Practical Field Guide to Web Discovery | TagFusion",
          "How to browse TagFusion by category and tag, what a listing does and does not tell you, and how to judge an unfamiliar website.",
          prose("A practical field guide", "How can you discover useful websites beyond a search box?", inner))


def contact():
    mail = (f'<p>Email: <a href="mailto:{escape(CONTACT_EMAIL)}">{escape(CONTACT_EMAIL)}</a>. Your address is used only to answer you.</p>'
            if CONTACT_EMAIL else "")
    inner = f"""
<p>For corrections, suggestions, or questions:</p>
{mail}
<ul>
<li><a href="{SUGGEST}">Suggest a website</a> for the directory.</li>
<li><a href="{REPORT}">Report a listing</a> that is broken, misleading, or no longer fits.</li>
</ul>
<p class="note">Both links open a public form on GitHub and need a GitHub account. What you write there is visible to everyone.</p>"""
    write("contact/", "Contact TagFusion | Corrections and Suggestions",
          "How to suggest a website, report a listing, or ask a question about TagFusion.",
          prose("Contact", "Send a note into the web.", inner))


def privacy():
    who = f"TagFusion is operated by {escape(OPERATOR)}." if OPERATOR else "TagFusion is operated by one person."
    mail = f' or by email at <a href="mailto:{escape(CONTACT_EMAIL)}">{escape(CONTACT_EMAIL)}</a>' if CONTACT_EMAIL else ""
    inner = f"""
<p>{who} This page says what the site does with information about you. The short answer is: almost nothing.</p>
<h2>What this site collects</h2>
<p>Nothing. TagFusion has no accounts, no sign-in, no forms that store what you type, no cookies, and no analytics. Searching and combining tags happen inside your own browser.</p>
<h2>Who else sees your visit</h2>
<ul>
<li><strong>GitHub Pages</strong> hosts the site. Like any web host, GitHub receives your IP address and browser details when a page loads, under <a href="https://docs.github.com/en/site-policy/privacy-policies/github-general-privacy-statement" target="_blank" rel="noopener noreferrer">GitHub’s privacy statement</a>.</li>
<li><strong>Google Fonts</strong> serves the typefaces, so Google receives the same kind of request when the fonts load.</li>
</ul>
<h2>Suggestions and reports</h2>
<p>Suggesting or reporting a site happens on GitHub, in public, under your GitHub account. If you email instead, your address is used only to answer you.</p>
<h2>Links to other websites</h2>
<p>Listings link to independent websites. Those destinations have their own privacy practices. TagFusion does not control their content, cookies, or data handling.</p>
<h2>Earlier accounts</h2>
<p>Until late 2026 TagFusion ran on a different platform and offered accounts. Those accounts and the data stored with them were deleted when the site moved.</p>
<h2>Questions</h2>
<p>Ask through the <a href="../contact/">contact page</a>{mail}.</p>
<p class="muted">Last updated {UPDATED}.</p>"""
    write("privacy/", "Privacy Policy | TagFusion", "TagFusion has no accounts, cookies, or analytics. What the site's host and font provider see, and how suggestions work.",
          prose("Privacy", "A clear view of your data.", inner))


def terms():
    inner = f"""
<h2>Using TagFusion</h2>
<p>Use TagFusion to discover and suggest websites lawfully and respectfully.</p>
<h2>Suggestions</h2>
<p>You are responsible for what you suggest and must have the right to share it. Do not suggest sites whose main content is {REFUSED}, and do not include other people’s personal data. A suggestion may be declined, and a listing may be removed, when it is inaccurate, unsafe, unavailable, infringing, deceptive, or does not fit the directory.</p>
<h2>Editorial standards</h2>
<p>TagFusion is a discovery directory, not a guarantee or endorsement of every external website. Descriptions aim to be accurate, useful, and original.</p>
<h2>External websites</h2>
<p>TagFusion does not operate the websites it lists. Opening a listing means you are leaving TagFusion and accepting that destination’s terms and privacy practices.</p>
<h2>Advertising</h2>
<p>There are no paid placements today. If one is shown, it will be labelled “Sponsor” and should not be mistaken for a listing.</p>
<h2>Liability</h2>
<p>TagFusion is provided on an as-is basis. The operator does not guarantee that the directory or any linked website will be available, accurate, secure, or suitable for a particular purpose, and is not responsible for losses arising from your use of external websites.</p>
<p class="muted">Last updated {UPDATED}.</p>"""
    write("terms/", "Terms of Use | TagFusion", "The rules for using TagFusion and suggesting websites, and what the directory will not list.",
          prose("Terms", "Keep the web worth wandering.", inner))


def not_found():
    body = prose("Not found", "This path leads nowhere.",
                 '<p class="lede">The page you asked for does not exist, or the listing has been retired.</p>'
                 '<p class="row"><a class="btn" href="/">Back to exploring</a> <a class="btn ghost" href="/search/">Search the directory</a></p>')
    write("404.html", "Page not found | TagFusion", "This page does not exist.", body, sitemap=False, robots="noindex")


# ---- Files beside the pages ------------------------------------------------------------
def extras():
    for name in ("site.css", "site.js", "favicon.png", "tagfusion-og.webp"):
        shutil.copyfile(HERE / "static" / name, OUT / name)
    (OUT / "catalog.json").write_text(json.dumps(sites, ensure_ascii=False, separators=(",", ":")), encoding="utf-8", newline="\n")
    (OUT / ".nojekyll").write_text("", encoding="utf-8")
    if DOMAIN:
        (OUT / "CNAME").write_text(DOMAIN + "\n", encoding="utf-8", newline="\n")
    urls = "".join(f"  <url><loc>{SITE}/{p}</loc></url>\n" for p in pages)
    (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n',
                                     encoding="utf-8", newline="\n")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {SITE}/sitemap.xml\n", encoding="utf-8", newline="\n")
    (OUT / "llms.txt").write_text(f"""# TagFusion

> TagFusion is a hand-picked directory of {len(sites)} independent websites, browsed by broad categories and combinable tags.

## Public pages

- [Explore the directory]({SITE}/): Browse the catalog and combine tags.
- [Search the directory]({SITE}/search/): Search listings by name, description, category, or tag.
- [Field guide]({SITE}/field-guide/): How categories and tags work, and how to judge an unfamiliar website.
- [About TagFusion]({SITE}/about/): Who runs it, how suggestions are reviewed, and the editorial policy.
- [Contact]({SITE}/contact/): Suggest a website or report a listing.
- [Privacy policy]({SITE}/privacy/): The site has no accounts, cookies, or analytics.
- [Terms of use]({SITE}/terms/): The rules for using the directory.
- [Full catalog as JSON]({SITE}/catalog.json)

Listings are starting points, not endorsements or guarantees of external websites.
""", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    home(); listing_pages(); search(); about(); field_guide(); contact(); privacy(); terms(); not_found(); extras()
    print(f"built {len(pages) + 1} pages, {len(sites)} listings, {len(TAGS)} tags -> {OUT}")
