"""Assemble the public feed sent by the TBX Power Automate flow as GitHub issues titled
'tbx-sync <batch> <i>/<n>'. Only issues opened by the repo owner are trusted."""
import json, os, re, subprocess, sys, urllib.request
repo, owner, tok = os.environ['GITHUB_REPOSITORY'], os.environ['GITHUB_REPOSITORY_OWNER'], os.environ['GH_TOKEN']
def api(path, method='GET', data=None):
    req = urllib.request.Request('https://api.github.com' + path, method=method,
        data=json.dumps(data).encode() if data else None,
        headers={'Authorization': 'Bearer ' + tok, 'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(req) as r: return json.loads(r.read() or b'null')
issues = api(f'/repos/{repo}/issues?state=open&per_page=100&creator={owner}')
batches = {}
for it in issues:
    m = re.match(r'tbx-sync (\S+) (\d+)/(\d+)$', it['title'].strip())
    if m and it['user']['login'].lower() == owner.lower():
        batches.setdefault(m.group(1), {})[int(m.group(2))] = it
        batches[m.group(1)]['n'] = int(m.group(3))
done = None
for b in sorted(batches, reverse=True):
    parts = batches[b]; n = parts.pop('n')
    if all(i in parts for i in range(1, n + 1)):
        done = (b, parts, n); break
if not done:
    print('No complete batch yet.'); sys.exit(0)
b, parts, n = done
text = ''
for i in range(1, n + 1):
    body = (parts[i]['body'] or '').replace('\r\n', '\n').strip('\n')
    lines = body.split('\n')
    text += ('\n'.join(lines if i == 1 else lines[1:])) + '\n'
open('feed.csv', 'w', encoding='utf-8').write(text)
rc = subprocess.call([sys.executable, 'tools/build_public.py', 'feed.csv', 'site/data.json'])
# close every sync issue (complete or stale) so the queue stays clean
for bb, parts2 in batches.items():
    for k, it in parts2.items():
        if k == 'n': continue
        api(f"/repos/{repo}/issues/{it['number']}", 'PATCH', {'state': 'closed', 'state_reason': 'completed'})
sys.exit(rc)
