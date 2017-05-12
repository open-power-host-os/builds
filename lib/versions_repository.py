import logging
import os

from lib import exception
from lib import repository
from lib.constants import REPOSITORIES_DIR


LOG = logging.getLogger(__name__)


def get_versions_repository(config):
    """
    Get the packages metadata Git repository, cloning it if does not
    yet exist.

    Args:
        config (dict): configuration dictionary

    Raises:
        exception.RepositoryError: if the clone is unsuccessful
    """
    path = os.path.join(config.get('work_dir'),
                        REPOSITORIES_DIR)
    url = config.get('packages_metadata_repo_url')
    name = "versions_{subcommand}".format(
        subcommand=config.get('subcommand'))
    try:
        versions_repo = repository.get_git_repository(url, path, name)
    except exception.RepositoryError:
        LOG.error("Failed to clone versions repository")
        raise

    return versions_repo


def setup_versions_repository(config):
    """
    Prepare the packages metadata Git repository, cloning it and
    checking out at the chosen branch.

    Args:
        config (dict): configuration dictionary

    Raises:
        exception.RepositoryError: if the clone or checkout are
            unsuccessful
    """
    versions_repo = get_versions_repository(config)
    branch = config.get('packages_metadata_repo_branch')
    refspecs = config.get('packages_metadata_repo_refspecs')
    try:
        versions_repo.checkout(branch, refspecs)
    except exception.RepositoryError:
        LOG.error("Failed to checkout versions repository")
        raise

    return versions_repo


def read_version_and_milestone(versions_repo):
    """
    Read current version and milestone (alpha or beta) from VERSION file

    Args:
        versions_repo (GitRepository): packages metadata git repository
    Returns:
        version_milestone (str): version and milestone. Format:
            <version>-<milestone>, valid milestone values: alpha, beta
    """
    version_file_path = os.path.join(versions_repo.working_tree_dir, 'VERSION')
    version_milestone = ""
    with open(version_file_path, 'r') as version_file:
        #ignore first line with file format information
        version_file.readline()
        version_milestone = version_file.readline().strip('\n')

    return version_milestone
