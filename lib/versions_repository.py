import logging
import os

from lxml import etree

from lib import exception
from lib import packages_manager
from lib import repository
from lib import rpm_package


LOG = logging.getLogger(__name__)


def setup_versions_repository(config):
    """
    Clone and checkout the packages metadata git repository and halt execution if
    anything fails.
    """
    path, _ = os.path.split(
        config.get('default').get('build_versions_repo_dir'))
    url = config.get('default').get('build_versions_repository_url')
    branch = config.get('default').get('build_version')
    try:
        versions_repo = repository.get_git_repository(url, path)
        versions_repo.checkout(branch)
    except exception.RepositoryError:
        LOG.error("Failed to checkout versions repository")
        raise

    return versions_repo


def create_html_table(packages):
    """
    Create a HTML table with the packages versions

    Args:
        packages ([Package]): packages
    """

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
        package_name_td.text = package.name

        package_version_td = etree.SubElement(tr, 'td')
        package_version_td.text = package.version

    return etree.tostring(table, pretty_print=True)


def replace_html_table(file_path, html_table):
    """
    Replace all HTML tables in a file with a HTML table

    Args:
        file_path(str): file path
        html_table (str): string representation of the HTML table which will
            replace existing ones
    """

    with file(file_path, "r") as f:
        lines = f.readlines()

    # replace
    new_lines = []
    in_table = False
    for line in lines:
        if not in_table and "<table>" in line:
            in_table = True
            new_lines.append(html_table)
        elif in_table:
            if "</table>" in line:
                in_table = False
        else:
            new_lines.append(line)

    with file(file_path, "w") as f:
        f.writelines(new_lines)


def update_versions_in_readme(versions_repo, distro, packages_names):
    """
    Update packages versions in README

    Args:
        versions_repo (GitRepository): versions git repository handler
        distro (distro.LinuxDistribution): Linux distribution
        packages_names ([str]): list of packages whose versions must be updated
    """

    LOG.info("Generating packages versions HTML table from packages: %s",
             ", ".join(packages_names))
    pm = packages_manager.PackagesManager(packages_names)
    # TODO: this is coupled with RPM-based Linux distributions
    pm.prepare_packages(packages_class=rpm_package.RPM_Package,
                        download_source_code=False, distro=distro)

    html_table = create_html_table(pm.packages)
    output_readme_path = os.path.join(versions_repo.working_tree_dir,
                                      'README.md')
    replace_html_table(output_readme_path, html_table)


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
