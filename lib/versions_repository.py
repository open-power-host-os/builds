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
