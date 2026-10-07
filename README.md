# TBX API Catalogue

Public catalogue of TBX (formerly TransBnk) APIs — https://tbx-apis.github.io

* `site/` — the website (index.html, data.json, logo).
* Data is pushed automatically by TBX's Power Automate flow (customer-safe fields only) via issues titled `tbx-sync …`;
  `.github/workflows/site.yml` assembles it into `site/data.json` and redeploys.
* Contact: purushottam.kadam@tbx.co.in
