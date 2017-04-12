import logging
import os

from lib import exception
from lib import repository
from lib.constants import REPOSITORIES_DIR


LOG = logging.getLogger(__name__)


def setup_versions_repository(config):
    """
    Clone and checkout the packages metadata git repository and halt execution if
    anything fails.
    """
    path = os.path.join(config.get('common').get('work_dir'),
                        REPOSITORIES_DIR)
    url = config.get('common').get('packages_metadata_repo_url')
    branch = config.get('common').get('packages_metadata_repo_branch')
    name = "versions_{subcommand}".format(
        subcommand=config.get('common').get('subcommand'))
    try:
        versions_repo = repository.get_git_repository(url, path, name)
        versions_repo.checkout(branch)
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
