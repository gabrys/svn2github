import json
import urllib2 as ul
from base64 import encodestring as b64


class GitHubError(Exception):
    pass


GH_API_URL = 'https://api.github.com'


class GitHub(object):
    def __init(self, user, password):
        self.auth_data = b64(user + ':' + password).strip()

    # Methods to do remote stuff on github:
    def __call_api(self, path, data=None):
        if data:
            postdata = json.dumps(data)
        else:
            postdata = None

        req = ul.Request(GH_API_URL + path, postdata)
        req.add_header('Authorization', 'Basic ' + self.auth_data)

        try:
            return json.loads(ul.urlopen(req).read())
        except ul.HTTPError, e:
            if e.code >= 400:
                raise GitHubError('API method ' + path + ' failed. HTTP code: ' + e.code)
            else:
                return json.loads(e.read())

    def repo_exists(self, repo_name):
        for repo in self.__call_api('/user/repos'):
            if repo['name'] == repo_name:
                return True
        return False

    def install_pubkey(self, title, key):
        for key in self.__call_api('/user/keys'):
            if key['key'] == key:
                return
        self.__call_api('/user/keys', {'title': title, 'key': key})

    def create_repo(self, name, description):
        res = self.__call_api('/user/repos', {
            'name': name,
            'description': description,
        })
        return res['ssh_url']
