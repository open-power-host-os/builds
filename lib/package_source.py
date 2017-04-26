import os
import shutil
import socket
import urllib2


from lib import config
from lib import exception
from lib import repository
from lib import utils


def set_dest_dir(source, directory, local_copy_subdir_name):
    """
    Set local directory to which the repository/URL will be downloaded in source dict.

    Args:
        source (dict): source
        directory (str): target directory
        local_copy_subdir_name: target subdirectory in directory. Used only by SVN.
    """

    source_type = source.keys()[0]
    if source_type != 'url':
        if source_type == 'svn':
            dest = os.path.join(directory, local_copy_subdir_name)
        else:
            repo_name = os.path.basename(source[source_type]['src'])
            dest = os.path.join(directory, repo_name)
    else:
        file_name = os.path.basename(source['url']['src'])
        dest = os.path.join(directory, file_name)

    source[source_type]['dest'] = dest


def _hg_download(source, directory):
    """
    Clones a mercurial [source] to [directory] and returns a source dict.
    """
    CONF = config.get_config().CONF
    proxy = CONF.get('common').get('http_proxy')
    hg_source = source['hg']
    repo_name = os.path.basename(hg_source['src'])
    dest = os.path.join(directory, repo_name)
    command = 'hg '

    commit_id = hg_source.get('commit_id')
    branch = hg_source.get('branch')

    if commit_id is None and branch is None:
        raise ValueError('invalid hg source dict: missing both `commit_id` '
                         'and `branch`')

    command += 'clone "{}" -r "{}" "{}" '.format(hg_source['src'],
                                                hg_source['branch'],
                                                dest)
    if proxy:
        command += '--config http_proxy.host="{}" '.format(proxy)
    command += "--ssh '/usr/bin/env ssh -o ConnectTimeout={}'"

    def _clone_repository(timeout):
        cmd = command.format(timeout)
        utils.run_command(cmd)

    def _is_timeout_error(exc):
        if not isinstance(exc, exception.SubprocessError):
            return False
        return ('timed out' in exc.stdout or 'timed out' in exc.stderr)

    utils.retry_on_timeout(_clone_repository,
                           is_timeout_error_f=_is_timeout_error,
                           initial_timeout=60)

    return source

def _git_download(source, directory):
    """
    Clones a git [source] to [directory] and returns a dict with a key pointing
    to the cloned repository.
    """
    git_source = source['git']
    commit_id = git_source.get('commit_id')
    branch = git_source.get('branch')

    if commit_id is None and branch is None:
        raise ValueError('invalid git source dict: missing both `commit_id` '
                         'and `branch`')

    def _download_repository():
        return repository.get_git_repository(git_source['src'], directory)

    repo = utils.retry_on_error(_download_repository,
                                error=exception.RepositoryError)
    repo.checkout(commit_id or branch)
    source['git']['repo'] = repo
    return source

def _svn_download(source, directory):
    """
    Checkout a Subversion [source] to [directory] and returns a dict with a key
    pointing to the cloned repository
    """
    svn_source = source['svn']
    commit_id = svn_source.get('commit_id')
    branch = svn_source.get('branch')

    if commit_id is None and branch is None:
        raise ValueError('invalid subversion source dict: missing both `commit_id` '
                         'and `branch`')

    def _download_repository():
        return repository.get_svn_repository(svn_source['src'], directory)
    repo = utils.retry_on_error(_download_repository,
                                error=exception.RepositoryError)

    def _checkout_repository():
        repo.checkout(commit_id or branch)
    utils.retry_on_error(_checkout_repository,
                         error=exception.RepositoryError)

    source['svn']['repo'] = repo
    return source

def _url_download(source, directory):
    """
    Downloads a file from URL [source] to [directory] and returns a source
    dict.
    """
    file_name = os.path.basename(source['url']['src'])
    dest = os.path.join(directory, file_name)

    CHUNK_SIZE = 16 << 1024

    def _open_url(timeout):
        return urllib2.urlopen(source['url']['src'], timeout=timeout)

    response = utils.retry_on_timeout(_open_url,
                                      lambda exc: isinstance(exc,
                                                             socket.timeout),
                                      initial_timeout=10)

    with open(dest, 'wb') as f:
        while True:
            chunk = response.read(CHUNK_SIZE)
            if not chunk:
                break
            f.write(chunk)
    return source


def download(source, directory='/tmp', local_copy_subdir_name=None):
    """
    Download files specified by [source] to [directory].
    git and hg download to a subdir with the repository name.
    As svn has no standard URL format from which to infer the repository name, it downloads
    to a subdir named [local_copy_subdir_name]
    """
    keys = source.keys()

    # TODO: currently ignoring subdir_name for all sources except svn, this is
    # not consistent
    if keys == ['git']:
        return _git_download(source, directory)
    elif keys == ['hg']:
        return _hg_download(source, directory)
    elif keys == ['svn']:
        return _svn_download(source, os.path.join(directory, local_copy_subdir_name))
    elif keys == ['url']:
        return _url_download(source, directory)
    else:
        raise ValueError('invalid source dict format')


def _git_archive(source, directory):
    """
    Creates a tar.gz archive for git [source] an places it in [directory].

    Returns [source] with updated [archive] pointing to the created file.
    """
    git_source = source['git']
    repo = git_source['repo']
    archived_file_path = repo.archive(git_source['archive'], directory)
    git_source['archive'] = archived_file_path
    source['git'] = git_source
    return source


def _hg_archive(source, directory):
    """
    Creates a tar.gz archive for mercurial [source] an places it in
        [directory].

    Returns [source] with updated [archive] pointing to the created file.
    """
    archive_name = source['hg']['archive']
    archive_file = os.path.join(directory, archive_name + ".tar.gz")

    cmd = 'hg archive -t tgz "{}"'.format(archive_file)
    utils.run_command(cmd, cwd=source['hg']['dest'])

    source['hg']['archive'] = archive_file
    return source


def _svn_archive(source, directory):
    archive_name = source['svn']['archive']
    archive_file = os.path.join(directory, archive_name + ".tar.gz")

    cmd = "tar --transform 's,^\.,{0},' -cvzf {1} . --exclude='*/.svn'".format(
        archive_name, archive_file)
    utils.run_command(cmd, cwd=source['svn']['dest'])

    source['svn']['archive'] = archive_file
    return source

def _url_archive(source, directory):
    file_path = source['url']['dest']
    file_ext = ".".join(os.path.basename(file_path).split(".")[1:])
    archive_name = source['url']['archive']
    archive_path = os.path.join(directory, archive_name + "." + file_ext)

    shutil.move(file_path, archive_path)
    source['url']['archive'] = archive_path

    return source


def archive(source, directory=''):
    """
    Create tarball archive from [source] and move it to [directory].
    """
    if not source:
        raise ValueError('invalid source dict format: there are no keys')

    keys = source.keys()
    if len(keys) > 1:
        raise ValueError('invalid source dict format: too many keys')

    if keys == ['git']:
        return _git_archive(source, directory)
    elif keys == ['hg']:
        return _hg_archive(source, directory)
    elif keys == ['svn']:
        return _svn_archive(source, directory)
    elif keys == ['url']:
        return _url_archive(source, directory)
    else:
        raise ValueError('invalid source dict format: invalid key(s)')
