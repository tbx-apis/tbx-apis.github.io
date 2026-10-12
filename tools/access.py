"""Apply approve / block decisions sent as GitHub issues titled 'tbx-access approve|block <hash16>'.
Only issues opened by the repository owner are trusted. Updates site/access.json and closes the issues."""
import json, os, re, urllib.request
repo, owner, tok = os.environ['GITHUB_REPOSITORY'], os.environ['GITHUB_REPOSITORY_OWNER'], os.environ['GH_TOKEN']
def api(path, method='GET', data=None):
    req = urllib.request.Request('https://api.github.com' + path, method=method, data=json.dumps(data).encode() if data else None,
        headers={'Authorization': 'Bearer ' + tok, 'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(req) as r: return json.loads(r.read() or b'null')
issues = api(f'/repos/{repo}/issues?state=open&per_page=100&creator={owner}&sort=created&direction=asc')
acc = json.load(open('site/access.json'))
changed = 0
for it in issues:
    m = re.match(r'tbx-access (approve|block) ([0-9a-f]{16})\b', it['title'].strip().lower())
    if not m or it['user']['login'].lower() != owner.lower(): continue
    acc['status'][m.group(2)] = 'approved' if m.group(1) == 'approve' else 'blocked'
    changed += 1
    api(f"/repos/{repo}/issues/{it['number']}", 'PATCH', {'state': 'closed', 'state_reason': 'completed'})
if changed:
    json.dump(acc, open('site/access.json', 'w'), separators=(',', ':'))
print('decisions applied:', changed)
