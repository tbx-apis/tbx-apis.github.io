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

# If Category is blank in the tracker, infer it from the API name so a live API is never hidden.
INFER = [(r'aadhaar|pan\b|voter|passport|driving|kyc|okyc|face|liveness|ocr|signature|identity|mobile number|digilocker', 'Identity & Individual KYC'),
         (r'gst|cin|company|mca|udyam|llp|fssai|iec|business|director|din\b|tan\b', 'Business & KYB'),
         (r'bank|ifsc|upi|vpa|penny|mandate|nach|payout|statement|bin\b', 'Banking & Payments'),
         (r'credit|bureau|cibil|experian|equifax|crif|score', 'Credit & Alternate Data'),
         (r'aml|pep|fraud|mule|court|crime|background|police', 'Risk, Fraud & Background'),
         (r'vehicle|\brc\b|chassis|fastag|challan|property|land', 'Asset Verification'),
         (r'uan|epfo|employ|salary|payslip|itr|income', 'Employment & Income'),
         (r'esign|e-sign|estamp|e-stamp|document', 'eSign & Document Workflow'),
         (r'email|ip\b|device|sim|digital', 'Contactability & Digital Risk'),
         (r'lpg|electricity|water|gas|utility|telecom', 'Travel, Telecom & Utilities'),
         (r'tamper', 'Risk, Fraud & Background')]
def infer_cat(name):
    n = name.lower()
    for pat, c in INFER:
        if re.search(pat, n): return c
    return 'Other APIs'

# Exact samples from the tracker (Sample Request / Sample Response). Sanitised: no URLs or vendor names.
VENDORS = r'digitap|trusthub|befisc|surepass|tenacio|sprintverify|signzy|bureau\.id|bureauid|perfios|karza|idfy|ongrid|valuepitch|value pitch|neokred|finb|e-?mudhra|saafe|doqfy|timble|apiclub|api club|protean|carinfo|croissance|blostem|coversure|bharat ?informatics|aadhaarapi|cashfree|setu'
def sample(v):
    v = (v or '').strip()
    if not v:
        return None
    v = re.sub(r'https?://[^\s"\'<>]+', '<url>', v)
    v = re.sub(VENDORS, 'TBX', v, flags=re.I)
    try:
        return json.loads(v)
    except Exception:
        return v[:6000]
seen = {}
for r in rows:
    name = clean(r.get('TBX API Name'))
    cat = clean(r.get('Category'))
    cat = CAT_MAP.get(cat, cat)
    if not name or name.startswith('('):
        continue
    if not cat:
        cat = infer_cat(name)
    status = (r.get('API Status') or '').strip().lower()
    avail = status == 'live'
    item = {"n": name, "c": cat, "s": clean(r.get('Sub-Category')), "d": clean(r.get('Detailed Description')),
            "u": clean(r.get('Use-Case')), "t": clean(r.get('Target Customers')), "i": clean(r.get('Target Industry')), "a": avail}
    rq, rs = sample(r.get('Sample Request')), sample(r.get('Sample Response'))
    if rq is not None and rs is not None:
        item["rq"], item["rs"] = rq, rs
    if 'aml' in name.lower() and 'company information' in item["d"].lower():
        item["d"] = ''
    if not item["d"] and not item["u"]:
        item["d"] = name + ': details available on request. Book a demo or enquire to learn more.'
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
