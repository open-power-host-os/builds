# Copyright (C) IBM Corp. 2016.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import os
import shutil

from lxml import etree
import git

from lib import config
from lib import distro_utils
from lib import exception
from lib import packages_manager
from lib import repository
from lib import rpm_package
from lib.utils import replace_str_in_file
from lib.versions_repository import setup_versions_repository


LOG = logging.getLogger(__name__)


def generate_html_table(packages):
    table = etree.Element('table')
    thead = etree.SubElement(table, 'thead')
    software_th = etree.SubElement(thead, 'th')
    software_th.text = 'Software'

    version_th = etree.SubElement(thead, 'th')
    version_th.text = 'Version'

    tbody = etree.SubElement(table, 'tbody')

    for package in packages:
        tr = etree.SubElement(tbody, 'tr')
        package_name_td = etree.SubElement(tr, 'td')
        package_name_td.text = package['name']

        package_version_td = etree.SubElement(tr, 'td')
        package_version_td.text = package['version']

    return etree.tostring(table, pretty_print=True)


def commit_changes(repo, committer_name, committer_email):
    """
    Commit changes done to the repository.

    Args:
        repo (GitRepository): packages metadata git repository
        committer_name (str): committer name
        committer_email (str): committer email
    """
    LOG.info("Adding files to repository index")
    repo.index.add(["*"])

    LOG.info("Committing changes to local repository")
    commit_message = "Update README versions table"
    actor = git.Actor(committer_name, committer_email)
    repo.index.commit(commit_message, author=actor, committer=actor)


def push_changes_to_head(repo, repo_url, repo_branch):
    """
    Push changes in local Git repository to the remote Git repository, using
    the system's configured SSH credentials.

    Args:
        repo (GitRepository): git repository
        repo_url (str): remote git repository URL
        repo_branch (str): remote git repository branch

    Raises:
        repository.PushError if push fails
    """
    LOG.info("Pushing updated versions README")

    LOG.info("Creating remote for URL {}".format(repo_url))
    REPO_REMOTE = "push-remote"
    repo.create_remote(REPO_REMOTE, repo_url)

    LOG.info("Pushing changes to remote repository")
    remote = repo.remote(REPO_REMOTE)
    refspec = "HEAD:refs/heads/{}".format(repo_branch)
    push_info = remote.push(refspec=refspec)[0]
    LOG.debug("Push result: {}".format(push_info.summary))
    if git.PushInfo.ERROR & push_info.flags:
        raise repository.PushError(push_info)


def run(CONF):
    versions_repo = setup_versions_repository(CONF)
    packages = (CONF.get('default').get('packages') or
                config.discover_packages())

    arch_and_endianness = CONF.get('default').get('arch_and_endianness')
    distro = distro_utils.get_distro(CONF.get('default').get('distro_name'),
                                     CONF.get('default').get('distro_version'),
                                     arch_and_endianness)

    commit_updates = CONF.get('default').get('commit_updates')
    push_updates = CONF.get('default').get('push_updates')
    push_repo_url = CONF.get('default').get('push_repo_url')
    push_repo_branch = CONF.get('default').get('push_repo_branch')
    updater_name = CONF.get('default').get('updater_name')
    updater_email = CONF.get('default').get('updater_email')

    REQUIRED_PARAMETERS = ["updater_name", "updater_email"]
    if push_updates:
        REQUIRED_PARAMETERS += ["push_repo_url", "push_repo_branch"]
    for parameter in REQUIRED_PARAMETERS:
        if CONF.get('default').get(parameter) is None:
            raise exception.RequiredParameterMissing(parameter=parameter)

    LOG.info("Generating HTML table from packages  versions: %s",
             ", ".join(packages))
    pm = packages_manager.PackagesManager(packages)
    pm.prepare_packages(packages_class=rpm_package.RPM_Package,
                        download_source_code=False, distro=distro)

    html_table = generate_html_table(pm.packages)
    readme_template_path = os.path.join(versions_repo.working_tree_dir,
                                        'README.md.in')
    output_readme_path = os.path.join(versions_repo.working_tree_dir,
                                      'README.md')

    if os.path.exists(output_readme_path):
        os.remove(output_readme_path)

    shutil.copyfile(readme_template_path, output_readme_path)
    replace_str_in_file(output_readme_path, '%%PACKAGES_VERSIONS_TABLE%%',
                        html_table)

    if commit_updates:
        commit_changes(versions_repo, updater_name, updater_email)
        if push_updates:
            push_changes_to_head(versions_repo, push_repo_url,
                                 push_repo_branch)
