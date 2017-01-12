import os
import shutil
import urllib2


from lib import config
from lib import repository
from lib import utils


def _hg_download(source, directory):
    """
    Clones a mercurial [source] to [directory] and returns a source dict.
    """
    CONF = config.get_config().CONF
    proxy = CONF.get('http_proxy')
    hg_source = source['hg']
    repo_name = os.path.basename(hg_source['src'])
    dest = os.path.join(directory, repo_name)
    command = 'hg '

    if proxy:
        command += '-c http_proxy.host="{}" '.format(proxy)

    commit_id = hg_source.get('commit_id')
    branch = hg_source.get('branch')

    if commit_id is None and branch is None:
        raise ValueError('invalid hg source dict: missing both `commit_id` '
                         'and `branch`')

    command += 'clone "{}" -r "{}" "{}"'.format(hg_source['src'],
                                                hg_source['branch'],
                                                dest)
    utils.run_command(command)
    source['hg']['dest'] = dest
    return source


def _git_download(source, directory):
    """
    Clones a git [source] to [directory] and returns a dict with a key pointing
    to the cloned repository.
    """
    git_source = source['git']
    commit_id = git_source.get('commit_id')
    branch = git_source.get('branch')
    ref_to_fetch = git_source.get('ref_to_fetch')

    if commit_id is None and branch is None:
        raise ValueError('invalid git source dict: missing both `commit_id` '
                         'and `branch`')

    repo = repository.get_git_repository(git_source['src'],
                                         directory,
                                         git_source.get('shallow'))
    repo.checkout(commit_id or branch, ref_to_fetch)
    source['git']['repo'] = repo
    return source


def _url_download(source, directory):
    """
    Downloads a file from URL [source] to [directory] and returns a source
    dict.
    """
    file_name = os.path.basename(source['url']['src'])
    dest = os.path.join(directory, file_name)

    CHUNK_SIZE = 16 << 1024

    response = urllib2.urlopen(source['url']['src'])
    with open(dest, 'wb') as f:
        while True:
            chunk = response.read(CHUNK_SIZE)
            if not chunk:
                break
            f.write(chunk)
    source['url']['dest'] = dest
    return source


def download(source, directory='/tmp'):
    """
    Download files specified by [source] to [directory].
    """
    keys = source.keys()

    if keys == ['git']:
        return _git_download(source, directory)
    elif keys == ['hg']:
        return _hg_download(source, directory)
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
    archived_file_path = repo.archive(git_source['archive'],
                                      git_source['commit_id'],
                                      directory,
                                      archive_src_dir = git_source['archive_src_dir'])
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


def _url_archive(source, directory):
    file_path = source['url']['dest']
    file_name = os.path.basename(file_path)
    archive_path = os.path.join(directory, file_name)

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
    elif keys == ['url']:
        return _url_archive(source, directory)
    else:
        raise ValueError('invalid source dict format: invalid key(s)')
