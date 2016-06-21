import os.path as path
import re
import subprocess as sp
import urlparse as up


class SvnError(Exception):
    pass


class Svn(object):
    def __init__(self, url):
        r = up.urlparse(url)
        if r.scheme and r.netloc and r.path and not r.fragment:
            self.__url = url
        else:
            raise ValueError('"' + url + '" does not seem to be a valid URL')

    def check_svn(self):
        if 0 != sp.call(['svn', 'info', self.__url]):
            raise SvnError('Cannot connect to SVN repository at ' + self.__url)

    # TODO: get current remote SVN revision

    def to_git(self, dir):
        if not path.isdir(dir):
            raise SvnError(dir + ' is not a directory')

        # TODO: check if empty

        pr = sp.Popen(['git', 'svn', 'clone', self.__url, dir], stdout=sp.PIPE)
        while pr.returncode is None:
            try:
                line = pr.stdout.readline()
                if len(line) == 0:
                    break
                m = re.match(r'^r([0-9]+) = [a-f0-9]+ \(git-svn\)', line)
                if m and long(m.group(1)) % 9 == 1:
                    rev_no = m.group(1)
                    # TODO: yield the rev_no?
            except OSError:
                break
        if 0 != pr.wait():
            raise SvnError('An error happened while mirroring SVN repo from ' + self.__url)
