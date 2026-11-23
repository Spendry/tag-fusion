# TagFusion

A hand-picked directory of independent websites, browsed by category and by combining tags.
Live at https://halfhumandraft.com.

The site is plain static pages. There are no accounts, no cookies and no analytics.

## How it is put together

- `data/catalog.json` is the directory: one entry per website, with its name, address,
  description, category and tags.
- `build.py` turns that file into the pages in `docs/`, which GitHub Pages serves. It uses
  the Python standard library only.
- `static/` holds the stylesheet, the script for tag combining and search, and the images.
- `tools/check_links.py` re-checks every listing: it reports addresses that fail, that now
  lead to a different domain, or whose page shows words the directory refuses.

To change a listing, edit `data/catalog.json`, then:

```
python build.py
```

## Suggesting or reporting a website

Use the issue forms: "Suggest a website" or "Report a listing". A person reads each one
before anything changes. The editorial policy is on the site's About page.

## History

The first version was built with Blink, an AI app builder, and offered accounts and votes.
In late 2026 it was rebuilt as this static site, and the accounts were removed.
