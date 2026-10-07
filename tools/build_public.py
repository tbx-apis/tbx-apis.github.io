"""Build the public catalogue data (no prices, codes, vendors or internal links) from a TBX feed CSV."""
import csv, json, re, sys, io, datetime
CAT_MAP = {'Business Verification': 'Business & KYB', 'Know Your Business (KYB)': 'Business & KYB'}
src = sys.argv[1] if len(sys.argv) > 1 else 'feed.csv'
out = sys.argv[2] if len(sys.argv) > 2 else 'site/data.json'
text = open(src, encoding='utf-8-sig').read()
rows = list(csv.DictReader(io.StringIO(text)))
def clean(s):
    s = re.sub(r'\s+', ' ', (s or '')).strip()
    s = re.sub(r'\((?:Backup vendor|Global monitoring variant|India monitoring variant)\.?\)', '', s, flags=re.I)
    s = re.sub(r'\(?\s*Pricing is per [^.)]*[.)]?\)?', '', s, flags=re.I)
    s = re.sub(r'\bVX[- ]?\d{2}[- ]?\d{3}\b', '', s)
    s = s.replace('vendor-level metadata', 'audit metadata')
    return re.sub(r'\s+', ' ', s).strip(' ;,')
seen = {}
for r in rows:
    name = clean(r.get('TBX API Name'))
    cat = clean(r.get('Category'))
    cat = CAT_MAP.get(cat, cat)
    if not name or not cat or name.startswith('('):
        continue
    status = (r.get('API Status') or '').strip().lower()
    avail = status == 'live'
    item = {"n": name, "c": cat, "s": clean(r.get('Sub-Category')), "d": clean(r.get('Detailed Description')),
            "u": clean(r.get('Use-Case')), "t": clean(r.get('Target Customers')), "i": clean(r.get('Target Industry')), "a": avail}
    if 'aml' in name.lower() and 'company information' in item["d"].lower():
        item["d"] = ''
    if not item["d"] and not item["u"]:
        continue
    k = name.lower()
    if k in seen and (seen[k]["a"] or not avail):
        continue
    seen[k] = item
items = sorted(seen.values(), key=lambda x: (not x["a"], x["c"], x["n"]))
if len(items) < 20:
    sys.exit(f"Only {len(items)} APIs - refusing to publish.")
json.dump({"updated": datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), "apis": items},
          open(out, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(f"{len(items)} APIs ({sum(i['a'] for i in items)} available) -> {out}")
