
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

import os
import logging
import re
import yaml

from lib import config
from lib import exception
from lib import utils
from lib.package import Package

CONF = config.get_config().CONF
LOG = logging.getLogger(__name__)


def compare_versions(v1, v2):
    try:
        utils.run_command("rpmdev-vercmp %s %s" % (v1, v2))
        rc = 0
    except exception.SubprocessError as exc:
        if exc.returncode == 11:
            rc = 1
        elif exc.returncode == 12:
            rc = -1
        else:
            raise
    return rc


class SpecFile(object):

    def __init__(self, path):
        self.path = path
        self._content = None

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

    def query_tag(self, tag):
        return utils.run_command(
            "rpmspec --srpm -q --qf '%%{%s}' %s 2>/dev/null" % (
                tag.upper(), self.path)).strip()

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

    def bump_release(self, log, user_name, user_email):
        comment = "\n".join(['- ' + l for l in log])
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
            # load distro files
            files = self.package_data.get('files').get(
                self.distro.lsb_name).get(self.distro.version)

            self.build_files = files.get('build_files', None)
            if self.build_files:
                self.build_files = os.path.join(
                    self.package_dir, self.build_files)
            self.download_build_files = files.get('download_build_files', [])

            # list of dependencies
            for dep_name in files.get('dependencies', []):
                dep = RPM_Package.get_instance(dep_name, self.distro)
                self.dependencies.append(dep)

            for dep_name in files.get('build_dependencies', []):
                dep = RPM_Package.get_instance(dep_name, self.distro)
                self.build_dependencies.append(dep)

            self.rpmmacro = files.get('rpmmacro', None)
            if self.rpmmacro:
                self.rpmmacro = os.path.join(self.package_dir, self.rpmmacro)

            self.spec_file = SpecFile(
                os.path.join(self.package_dir, files.get('spec')))

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
