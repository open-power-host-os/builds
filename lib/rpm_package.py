
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

import glob
import os
import logging
import re

import rpmUtils.miscutils

from lib import config
from lib import exception
from lib import utils
from lib.package import Package

CONF = config.get_config().CONF
LOG = logging.getLogger(__name__)


def compare_versions(v1, v2):
    return rpmUtils.miscutils.compareEVR((None, v1, None), (None, v2, None))


class SpecFile(object):

    def __init__(self, path):
        self.path = path
        self._content = None
        self._cached_tags = dict()

    @property
    def content(self):
        """
        Get and cache the content of the spec file.
        """
        if self._content is None:
            with open(self.path, 'r') as file_:
                self._content = file_.read()
        return self._content

    @content.setter
    def content(self, value):
        """
        Set the cached content of the spec file.
        """
        self._content = value

    def write_content(self):
        """
        Write the cached content to the spec file.
        """
        with open(self.path, 'w') as file_:
            file_.write(self._content)
        self._cached_tags = dict()

    def query_tag(self, tag):
        """
        Queries the spec file for a tag's value.
        Cached content not yet written to the file is not considered.
        """
        if tag not in self._cached_tags:
            self._cached_tags[tag] = utils.run_command(
                "rpmspec --srpm -q --qf '%%{%s}' %s 2>/dev/null" % (
                    tag.upper(), self.path)).strip()

        return self._cached_tags[tag]

    def update_version(self, new_version):
        LOG.info("Updating '%s' version to: %s" % (self.path, new_version))

        old_version = re.search(r'Version:\s*(\S+)', self.content).group(1)

        # we accept the Version tag in the format: xxx or %{xxx},
        # but not: xxx%{xxx}, %{xxx}xxx or %{xxx}%{xxx} because
        # there is no reliable way of knowing what the macro
        # represents in these cases.
        if re.match(r'(.+%{.*}|%{.*}.+)', old_version):
            raise exception.PackageSpecError("Failed to parse spec file "
                                             "'Version' tag")

        if "%{" in old_version:
            macro_name = old_version[2:-1]
            self._replace_macro_definition(macro_name, new_version)
        else:
            self.content = re.sub(r'(Version:\s*)\S+',
                             r'\g<1>' + new_version, self.content)

        # since the version was updated, set the Release to 0. When
        # the release bump is made, it will increment to 1.
        self.content = re.sub(r'(Release:\s*)[\w.-]+', r'\g<1>0', self.content)

        self.write_content()

    def bump_release(self, change_log_lines, user_name, user_email):
        comment = "\n".join(['- ' + l for l in change_log_lines])
        user_string = "%(user_name)s <%(user_email)s>" % locals()
        cmd = "rpmdev-bumpspec -c '%s' -u '%s' %s" % (
            comment, user_string, self.path)
        utils.run_command(cmd)

        # Flush the cache to force re-reading the file
        self._content = None

    def update_prerelease_tag(self, new_prerelease):
        self._replace_macro_definition('prerelease', new_prerelease)
        self.write_content()
        LOG.info("Updated '%s' prerelease tag to: %s"
                 % (self.path, new_prerelease))

    def update_commit_id(self, old_commit_id, new_commit_id):

        # change log may contain old commit IDs and we do not want to replace them

        # read up to change log
        lines = []
        CHANGE_LOG_TAG = "%changelog"
        change_log_lines = []
        started_change_log = False
        with file(self.path, "r") as f:
            for line in f:
                if CHANGE_LOG_TAG in line:
                    started_change_log = True
                if not started_change_log:
                    lines.append(line)
                else:
                    change_log_lines.append(line)

        # replace commit ID up to change log
        with file(self.path, "w") as f:
            for line in lines:
                line = line.replace(old_commit_id, new_commit_id)
                f.write(line)
            for line in change_log_lines:
                f.write(line)

    def _replace_macro_definition(self, macro_name, replacement):
        """
        Updates the file content cache, replacing the macro value.
        """
        self.content = re.sub(r'(%%define\s+%s\s+)\S+' % macro_name,
                              r'\g<1>' + replacement, self.content)


class RPM_Package(Package):

    def __init__(self, name, distro, *args, **kwargs):
        self.distro = distro
        super(RPM_Package, self).__init__(name, *args, **kwargs)

    def _load(self):
        """
        Read yaml file describing this package.
        """
        super(RPM_Package, self)._load()
        try:
            # keeps backwards compatibility with old yaml files which have 'centos'
            # instead of 'CentOS'
            if self.distro.lsb_name in self.package_data.get('files', {}):
                distro_attrib_name = self.distro.lsb_name
            else:
                distro_attrib_name = self.distro.lsb_name.lower()

            # load distro files
            files = self.package_data.get('files', {}).get(
                distro_attrib_name, {}).get(self.distro.version, {}) or {}

            default_build_files_dir_rel_path = os.path.join(
                self.distro.lsb_name, self.distro.version, "SOURCES")
            build_files_dir_rel_path = files.get('build_files') or default_build_files_dir_rel_path
            build_files_dir_path = os.path.join(self.package_dir, build_files_dir_rel_path)
            if os.path.isdir(build_files_dir_path):
                self.build_files = build_files_dir_path
            else:
                self.build_files = None
            self.download_build_files = files.get('download_build_files', [])

            # list of dependencies
            for dep_name in files.get('install_dependencies', []):
                dep = RPM_Package.get_instance(dep_name, self.distro)
                self.install_dependencies.append(dep)

            # keeps backward compatibility with old yaml files which have 'dependencies'
            # instead of 'install_dependencies'
            for dep_name in files.get('dependencies', []):
                dep = RPM_Package.get_instance(dep_name, self.distro)
                self.install_dependencies.append(dep)

            for dep_name in files.get('build_dependencies', []):
                dep = RPM_Package.get_instance(dep_name, self.distro)
                self.build_dependencies.append(dep)

            default_rpm_macros_file_rel_path = os.path.join(
                self.distro.lsb_name, self.distro.version, "rpmmacro")
            rpm_macros_file_rel_path = files.get('rpmmacro', default_rpm_macros_file_rel_path)
            rpm_macros_file_path = os.path.join(self.package_dir, rpm_macros_file_rel_path)
            if os.path.isfile(rpm_macros_file_path):
                self.rpmmacro = rpm_macros_file_path
            else:
                self.rpmmacro = None

            default_spec_file_rel_path = os.path.join(
                self.distro.lsb_name, self.distro.version, "%s.spec" % self.name)
            spec_file_rel_path = files.get('spec', default_spec_file_rel_path)
            self.spec_file_path = os.path.join(self.package_dir, spec_file_rel_path)
            self.spec_file = SpecFile(self.spec_file_path)

            if os.path.isfile(self.spec_file.path):
                LOG.info("Package found: %s for %s %s" % (
                    self.name, self.distro.lsb_name, self.distro.version))
            else:
                raise exception.PackageSpecError(
                    package=self.name,
                    distro=self.distro.lsb_name,
                    distro_version=self.distro.version)
        except TypeError:
            raise exception.PackageDescriptorError(package=self.name)

    @property
    def cached_build_results(self):
        """
        Get the files cached from the last build of this package.

        Returns:
            [str]: paths to the resulting files of the last build
        """
        result_files_glob = os.path.join(self.build_cache_dir, "*.rpm")
        return glob.glob(result_files_glob)

    @property
    def version(self):
        return self.spec_file.query_tag("version")

    @property
    def release(self):
        return self.spec_file.query_tag("release")
