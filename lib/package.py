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

from functools import total_ordering
import os
import logging
import urllib2
import yaml

from lib import config
from lib import exception
from lib import repository
from lib import utils

CONF = config.get_config().CONF
LOG = logging.getLogger(__name__)


@total_ordering
class Package(object):

    __created_packages = dict()

    @classmethod
    def get_instance(cls, package_name, *args, **kwargs):
        """
        Get unique Package instance for package name, creating one on
        first call.
        """
        if package_name in cls.__created_packages.keys():
            package = cls.__created_packages[package_name]
            LOG.debug("Getting existent package instance: %s" % package)
        else:
            package = cls(package_name, *args, **kwargs)
            cls.__created_packages[package_name] = package
        return package

    def __init__(self, name, category=None):
        self.name = name
        self.category = category
        self.clone_url = None
        self.download_source = None
        self.dependencies = []
        self.build_dependencies = []
        self.result_packages = []
        self.repository = None
        self.build_files = None
        self.download_build_files = []

        build_versions_repo_dir = CONF.get('default').get(
            'build_versions_repo_dir')
        self.package_dir = os.path.join(
            build_versions_repo_dir, self.category) if(
                self.category) else build_versions_repo_dir
        self.package_file = os.path.join(self.package_dir, self.name,
                                         '%s.yaml' % self.name)

        self._load()

    def __eq__(self, other):
        return self.name == other.name

    def __lt__(self, other):
        return self.name < other.name

    def __repr__(self):
        return self.name


    def download_files(self):
        """
        Download package source code and build files.
        Do the same for its dependencies, recursively.
        """
        if self.clone_url:
            self._download_source_code()
            # Else let it download later during build with a custom
            # command.
            # TODO Remove this "if" and do not allow custom commands
        self._download_build_files()
        for dep in (self.dependencies + self.build_dependencies):
            dep.download_files()

    def _download_source_code(self):
        LOG.info("%s: Downloading source code from '%s'." %
                 (self.name, self.clone_url))
        self._setup_repository(
            dest=CONF.get('default').get('repositories_path'),
            branch=CONF.get('default').get('branch'))

    def _load(self):
        """
        Read yaml file describing this package.
        """
        try:
            with open(self.package_file, 'r') as package_file:
                self.package_data = yaml.load(package_file).get('Package')
        except IOError:
            raise exception.PackageDescriptorError(
                "Failed to open %s's YAML descriptor" % self.name)

        self.name = self.package_data.get('name')
        self.clone_url = self.package_data.get('clone_url', None)
        self.download_source = self.package_data.get('download_source', None)

        # Most packages keep their version in a VERSION file
        # or in the .spec file. For those that don't, we need
        # a custom file and regex.
        version = self.package_data.get('version', {})
        self.version_file_regex = (version.get('file'),
                                   version.get('regex'))

        # NOTE(maurosr): Unfortunately some of the packages we build
        # depend on a gziped file which changes according to the build
        # version so we need to get that name somehow, grep the
        # specfile would be uglier imho.
        self.expects_source = self.package_data.get('expects_source')

        # NOTE(maurosr): branch and commit id are special cases for the
        # future, we plan to use tags on every project for every build
        # globally set in config.yaml, then this would allow some user
        # customization to set their preferred commit id/branch or even
        # a custom git tree.
        self.branch = self.package_data.get('branch', None)
        self.commit_id = self.package_data.get('commit_id', None)

        LOG.info("%s: Loaded package metadata successfully" % self.name)

    def _setup_repository(self, dest=None, branch=None):
        self.repository = repository.Repo(repo_name=self.name,
                                          clone_url=self.clone_url,
                                          dest_path=dest,
                                          refname=self.branch or branch,
                                          commit_id=self.commit_id)

    def _download_source(self, build_dir):
        """
        An alternative to just execute a given command to obtain sources.
        """
        utils.run_command(self.download_source, cwd=build_dir)
        return os.path.join(build_dir, self.expects_source)

    def _download_build_files(self):
        for url in self.download_build_files:
            f = urllib2.urlopen(url)
            data = f.read()
            filename = os.path.join(self.build_files, url.split('/')[-1])
            with open(filename, "wb") as file_data:
                file_data.write(data)
