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
import subprocess
import urllib2
import yaml

from lib import config
from lib import exception
from lib import repository

CONF = config.get_config().CONF
LOG = logging.getLogger(__name__)


class Package(object):

    def __init__(self, package, distro, category=None):
        self.name = package
        self.distro = distro
        self.category = category
        self.clone_url = None
        self.download_source = None
        self.dependencies = []
        self.build_dependencies = []
        self.result_packages = []
        self.repository = None

        self.package_dir = os.path.join(
            config.COMPONENTS_DIRECTORY, self.category) if(
                self.category) else config.COMPONENTS_DIRECTORY
        self.package_file = os.path.join(self.package_dir, self.name,
                                         '%s.yaml' % self.name)

        self.load_package(package, distro)
        self.download_source_code()

    def download_source_code(self):
        if self.clone_url:
            self._setup_repository(
                dest=CONF.get('default').get('repositories_path'),
                branch=CONF.get('default').get('branch'))
        # else let it download later during build, it's ugly, but a temporary
        # solution

    def load_package(self, package_name, distro):
        """
        Read yaml files descbring our supported packages
        """
        try:
            with open(self.package_file, 'r') as package_file:
                package = yaml.load(package_file).get('Package')

                self.name = package.get('name')
                self.clone_url = package.get('clone_url', None)
                self.download_source = package.get('download_source', None)

                # NOTE(maurosr): Unfortunately some of the packages we build
                # depend on a gziped file which changes according to the build
                # version so we need to get that name somehow, grep the
                # specfile would be uglier imho.
                self.expects_source = package.get('expects_source')

                # NOTE(maurosr): branch and commit id are special cases for the
                # future, we plan to use tags on every project for every build
                # globally set in config.yaml, then this would allow some user
                # customization to set their prefered commit id/branch or even
                # a custom git tree.
                self.branch = package.get('branch', None)
                self.commit_id = package.get('commit_id', None)

                # load distro files
                files = package.get('files').get(self.distro.lsb_name).get(
                    self.distro.version)

                self.build_files = files.get('build_files', None)
                if self.build_files:
                    self.build_files = os.path.join(self.package_dir,
                                                    package_name,
                                                    self.build_files)
		self.download_build_files = files.get('download_build_files', None)
                if self.download_build_files:
                    self._download_build_files()

                # list of dependencies
                for dep in files.get('dependencies', []):
                    self.dependencies.append(Package(dep, self.distro,
                                                     category='dependencies'))

                for dep in files.get('build_dependencies', []):
                    self.build_dependencies.append(Package(dep, self.distro,
                                                   category='dependencies'))

                self.rpmmacro = files.get('rpmmacro', None)
                if self.rpmmacro:
                    self.rpmmacro = os.path.join(self.package_dir,
                                                 package_name,
                                                 self.rpmmacro)

                self.specfile = os.path.join(self.package_dir, package_name,
                                             files.get('spec'))

                if os.path.isfile(self.specfile):
                    LOG.info("Package found: %s for %s %s" % (
                        self.name, self.distro.lsb_name, self.distro.version))
                else:
                    raise exception.PackageSpecError(
                        package=self.name,
                        distro=self.distro.lsb_name,
                        distro_version=self.distro.version)

        except TypeError:
            raise exception.PackageDescriptorError(package=self.name)

    def _setup_repository(self, dest=None, branch=None):
        self.repository = repository.Repo(package_name=self.name,
                                          clone_url=self.clone_url,
                                          dest_path=dest,
                                          branch=self.branch or branch,
                                          commit_id=self.commit_id)

    def _download_source(self, build_dir):
        """
        An alternative to just execute a given command to obtain sources.
        """
        cmd = "cd %s; %s; cd %s" % (build_dir, self.download_source,
                                    os.getcwd())
        LOG.info("Command: %s" % cmd)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, shell=True)
        output, error_output = p.communicate()
        LOG.info("STDOUT: %s" % output)
        LOG.info("STDERR: %s" % error_output)
	return os.path.join(build_dir, self.expects_source)

    def _download_build_files(self):
        for url in self.download_build_files:
            f = urllib2.urlopen(url)
            data = f.read()
            filename = os.path.join(self.build_files, url.split('/')[-1])
            with open(filename, "wb") as file_data:
                file_data.write(data)
