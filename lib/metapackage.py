import logging
import os
import re

from lib import exception
from lib import packages_manager
from lib import rpm_package
from lib.versions_repository import replace_file_section

LOG = logging.getLogger(__name__)


def create_yaml_install_dependencies_string(packages):
    """
    Create a string with package install dependencies meant to be placed
    in the release package spec file.

    Args:
        packages ([Package]): packages
    """
    dependencies_string = ""
    for package in packages:
        DEPENDENCY_LINE_TEMPLATE = (
            "     - {name}\n")
        dependencies_string += DEPENDENCY_LINE_TEMPLATE.format(
            name=package.name)
    return dependencies_string


def replace_spec_dependencies(spec_file_path):
    """
    Replace spec file dependency lines with current package versions.

    Args:
        spec_file_path (str): path to spec file
    """
    SPEC_DEPENDENCY_PATTERN = r"Requires\(post\): (?P<name>\S+) = \S+"
    SPEC_DEPENDENCY_TEMPLATE = "Requires(post): {name} = {evr}\n"
    spec_dependency_regex = re.compile(SPEC_DEPENDENCY_PATTERN)

    spec_file_contents = ""
    spec_updated = False
    with open(spec_file_path) as spec_file:
        for line in spec_file:
            match = spec_dependency_regex.match(line)
            if match is None:
                spec_file_contents += line
            else:
                LOG.debug("Dependency line found: {}".format(line))
                spec_updated = True
                package = rpm_package.RPM_Package.get_instance(
                    match.group("name"))

                if package.epoch:
                    package_evr = package.epoch + ":"
                else:
                    package_evr = ""
                package_evr += "{version}-{release}".format(
                    version=package.version, release=package.release)

                LOG.debug("Updating package {name} to {evr}".format(
                    name=package.name, evr=package_evr))
                spec_file_contents += SPEC_DEPENDENCY_TEMPLATE.format(
                    name=package.name, evr=package_evr)

    if spec_updated:
        with open(spec_file_path, "w") as spec_file:
            spec_file.write(spec_file_contents)


def update_metapackage(
        versions_repo, distro, metapackage_name, packages_names,
        user_name, user_email):
    """
    Update package version and dependencies to the packages created by
    a build of the specified versions repository commit.

    Args:
        versions_repo (GitRepository): versions Git repository handler
        distro (distro.LinuxDistribution): Linux distribution
        metapackage_name (str): name of the release package whose
            dependencies will be updated
        packages_names ([str]): list of dependencies of the release
            package
        user_name (str): name of the user updating the spec file
        user_name (str): email of the user updating the spec file
    """
    LOG.info("Updating release package dependencies: "
             "{}".format(", ".join(packages_names)))
    pm = packages_manager.PackagesManager(packages_names)
    # TODO: this is coupled with RPM-based Linux distributions
    pm.prepare_packages(packages_class=rpm_package.RPM_Package,
                        download_source_code=False, distro=distro)

    LOG.info("Updating release package YAML file")
    YAML_START_DELIMITER = "    install_dependencies:"
    metapackage_yaml_file_path = os.path.join(
        versions_repo.working_tree_dir, metapackage_name,
        metapackage_name + ".yaml")
    yaml_install_dependencies_string = "{start}\n{contents}".format(
        start=YAML_START_DELIMITER,
        contents=create_yaml_install_dependencies_string(pm.packages))
    replace_file_section(
        metapackage_yaml_file_path, yaml_install_dependencies_string,
        YAML_START_DELIMITER)

    LOG.info("Updating release package spec file")
    version_file_path = os.path.join(versions_repo.working_tree_dir, "VERSION")
    with open(version_file_path) as version_file:
        version_parts = version_file.readlines()[-1].strip().split("-")
    new_metapackage_version = version_parts.pop(0)
    if version_parts:
        metapackage_milestone = version_parts.pop(0)
    else:
        metapackage_milestone = "%nil"

    metapackage = rpm_package.RPM_Package.get_instance(
        metapackage_name, distro)

    version_compare = rpm_package.compare_versions(
        metapackage.version, new_metapackage_version)
    if version_compare < 0:
        metapackage.spec_file.update_version(new_metapackage_version)
    elif version_compare > 0:
        raise exception.PackageError(
            "Current version (%s) is greater than new version (%s)" %
            (metapackage.version, new_metapackage_version))
    metapackage.spec_file.replace_macro_definition(
        "milestone", metapackage_milestone)

    replace_spec_dependencies(metapackage.spec_file.path)
    metapackage.spec_file.bump_release(
        ["Update package dependencies"], user_name, user_email)
