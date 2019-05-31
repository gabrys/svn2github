# svn2github

Mirror your SVN repositories to GitHub

## Motivation

This is a standalone script created as a response to a few people asking for an alternative to using svn2github.com that I recently closed.

## Requirements

This is a Python3 script (tested with Python 3.5). It shells out to the following commands:

* `svn`
* `git`
* `git svn` (usually packaged separately from git!)
* `tar`

## Warning

Don't use the script on untrusted repositories. The script issues commands using input from the GitHub repository and possibly this can be exploited to run arbitrary commands on your server.

## Usage

There are a few ways to use the script.

The first use case is mirroring an SVN repository to a completely fresh GitHub:

1. Create a new repository using https://github.com/new
2. Make sure you can clone that repository using SSH (git clone git@github.com:...), you need your SSH keys set up for this
3. Invoke the script with the `import` subcommand: `./svn2github.py import github_user/repo http://svn-url/trunk`
4. To later synchronize the repo use `update`: `./svn2github.py update github_user/repo`

The second use case is mirroring a repository that used to be kept in sync by svn2github.com:

1. Fork repo from https://github.com/svn2github/repo to your new user and repo name
2. Make sure you can clone that repository using SSH (git clone git@github.com:...), you need your SSH keys set up for this
3. Bring the repo up to date with the `update` command: `python3 svn2github.py github_user/repo update`

All those commands (both `import` and `update`) will re-download the whole Git and SVN history every time, unless you specify a cache directory using the `--cache-dir` option. Use an empty directory and keep the contents between the runs to significantly speed up the updates!

## Help page

```
usage: svn2github.py [-h] [--cache-dir CACHE_DIR] {import,update} ...

Mirror SVN repositories to GitHub

positional arguments:
  {import,update}
    import              Import SVN repository to the GitHub repo
    update              Update the GitHub repository from SVN

optional arguments:
  -h, --help            show this help message and exit
  --cache-dir CACHE_DIR
                        Directory to keep the cached data to avoid re-
                        downloading all SVN and Git history each time. This is
                        optional, but highly recommended
  --git-dir GIT_DIR
                        Directory to keep the cached data to avoid re-
                        downloading all SVN and Git history each time. This is
                        optional, but highly recommended 
                        the difference for cache-dir is that is not compress and avoid decompress, copy all to an temporary directory and compress again.


====

usage: svn2github.py import [-h] GITHUB_REPO SVN_URL

positional arguments:
  GITHUB_REPO  GitHub repo in format: user/name
  SVN_URL      SVN repository to import

optional arguments:
  -h, --help   show this help message and exit

====

usage: svn2github.py update [-h] GITHUB_REPO

positional arguments:
  GITHUB_REPO  GitHub repo in format: user/name

optional arguments:
  -h, --help   show this help message and exit
```

## Examples and migration from cache-dir to git-dir 

### 1 - Before the existence of --git-dir option 
./svn2github.py --cache-dir /home/sergio/rpmfusion/new/VirtualBox/svn2github/virtualbox update sergiomb2/virtualbox

### 2 - Migration from --cache-dir to --git-dir option (just run one time)
./svn2github.py --git-dir /home/sergio/rpmfusion/new/VirtualBox/svn2github/virtualbox-repo/ --cache-dir /home/sergio/rpmfusion/new/VirtualBox/svn2github/virtualbox update sergiomb2/virtualbox

#### 3 - Now we may delete cache_dir and run option just with --git-dir option
./svn2github.py --git-dir /home/sergio/rpmfusion/new/VirtualBox/svn2github/virtualbox-repo/ update sergiomb2/virtualbox
