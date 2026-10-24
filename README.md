# The Thai Base

Condo rentals in Bang Na for foreign professionals and families. Static site served by GitHub Pages at thethaibase.com.

## Editing

- Condo projects: `data/condos.json`
- Contact details (WhatsApp, LINE, email): `data/site.json`
- Page text for guides, owners and contact pages: `src/*.html`
- Styles: `css/site.css`

After editing, rebuild the pages from the repo root and commit the result:

```
python3 tools/build.py
```

## Units, sale listings and the admin view

- Units for rent and sale: `data/units.json` (`"deal": "sale"` with `price_thb` for sale units).
- Public pages show a floor range (`floor_band`, e.g. `11–20`), never the exact floor.
- Exact floors, owners and room numbers are kept in `data/private/units-private.json`, which is **not committed**. The build encrypts it into `assets/admin-data.json` when the passphrase is set:

```
TTB_ADMIN_PASSPHRASE='…' python3 tools/build.py
```

- Sign in at `/admin/` with the passphrase to see the unit table; on that device, listing pages then show exact floors.
