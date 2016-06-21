import os.path as path
import subprocess as sp


class GitError(Exception):
    pass


class GitRepo(object):
    def __init__(self, dir, clone_from=None):
        if not path.isdir(dir):
            raise ValueError(dir + ' is not a directory')

        self.__dir = dir

        if clone_from:
            self.__call_git(['clone', clone_from, '.'])

        self.__check_dir()

    def __check_dir(self):
        if not path.isdir(path.join(self.__dir, '.git')):
            raise GitError('Directory ' + self.__dir + ' is not a git repo')

    def __call_git(self, args):
        if 0 != sp.call(['git'] + args, cwd=self.__dir):
            raise GitError('Failed to issue git ' + args[0])

    def svn_rebase(self):
        self.__call_git(['svn', 'rebase'])

    def add_remote(self, remote):
        try:
            self.__call_git(['remote', 'add', 'origin', remote])
        except GitError, e:
            raise GitError(e.message)

    def push(self):
        self.__call_git(['push', 'origin', 'master'])

    def export_git_svn(self, gitsvn_file):
        pass

    def import_git_svn(self, gitsvn_file):
        pass
