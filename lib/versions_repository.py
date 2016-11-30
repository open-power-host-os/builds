import logging
import os
import sys


from lib import exception
from lib import repository


LOG = logging.getLogger(__name__)


def setup_versions_repository(config):
    """
    Clone and checkout the versions repository and halt execution if
    anything fails.
    """
    path, dir_name = os.path.split(
        config.get('default').get('build_versions_repo_dir'))
    url = config.get('default').get('build_versions_repository_url')
    branch = config.get('default').get('build_version')
    try:
        versions_repo = repository.get_git_repository(dir_name, url, path)
        versions_repo.checkout(branch)
    except exception.RepositoryError as exc:
        LOG.exception("Failed to checkout versions repository")
        sys.exit(exc.errno)

    return versions_repo
