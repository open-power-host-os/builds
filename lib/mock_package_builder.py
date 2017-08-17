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
from functools import partial


import logging
import os
import shutil

from lib import config
from lib import exception
from lib import package_builder
from lib import package_source
from lib import utils
from lib import yum_repository
from lib.constants import LATEST_SYMLINK_NAME
from lib.mock import Mock

CONF = config.get_config().CONF
LOG = logging.getLogger(__name__)
MOCK_CHROOT_BUILD_DIR = "/builddir/build/SOURCES"


class MockPackageBuilder(package_builder.PackageBuilder):
    def __init__(self, config_file, build_timestamp):
        """
        Constructor

        Args:
            config_file (str): config file path
        """
        super(MockPackageBuilder, self).__init__()
        self.build_dir = None
        self.build_results_dir = CONF.get('result_dir')
        self.archive = None
        self.timestamp = build_timestamp
        self.mock = Mock(config_file, self.timestamp)

    def initialize(self):
        """
        Initializes the configured chroot by installing the essential
        packages. This setup is common for all packages that are built
        and needs to be done only once.
        """
        self.mock.run_command("--init")

    def build(self, package):
        """
        Build RPM package and its subpackages

        Args:
            package (RPM_Package): package
        """
        self.clean_cache_dir(package)
        LOG.info("%s: Starting build process" % package.name)
        self._build_srpm(package)
        self._install_external_dependencies(package)
        self._build_rpm(package)
        self._copy_rpms(self.build_dir, package.build_cache_dir)
        if not CONF.get('keep_build_dir'):
            self._destroy_build_directory()

    def _build_srpm(self, package):
        """
        Build source RPM package

        Args:
            package (RPM_Package): package
        """
        LOG.info("%s: Building SRPM" % package.name)
        self.mock.run_command(
            "--buildsrpm --no-clean --spec %s --sources %s "
            "--resultdir=%s %s" % (
                package.spec_file.path, self.archive, self.build_dir,
                package.macros))

    def _build_rpm(self, package):
        """
        Build RPM packages from a source RPM package

        Args:
            package (RPM_Package): package
        """
        cmd = " --rebuild %s --no-clean --resultdir=%s %s" % (
            self.build_dir + "/*.rpm", self.build_dir, package.macros)

        if package.rpmmacro:
            cmd = cmd + " --macro-file=%s" % package.rpmmacro

        LOG.info("%s: Building RPM" % package.name)
        try:
            # On success save rpms and destroy build directory unless
            # told otherwise.
            self.mock.run_command(cmd)
            package.built = True
        except exception.SubprocessError:
            LOG.info("%s: Failed to build RPMs, build artifacts are kept at "
                  "%s" % (package.name, self.build_dir))
            raise

        msg = "%s: Success! RPMs built!" % (package.name)
        LOG.info(msg)

    def prepare_sources(self, package):
        """
        Create build directory structure, create a tar.gz file with the source code
        and copy files to chroot.

        Args:
            package (RPM_Package): package
        """
        LOG.info("%s: Preparing source files." % package.name)
        self._create_build_directory(package)
        self._prepare_archive(package)
        if package.build_files:
            self._copy_files_to_chroot(package)

    def _prepare_archive(self, package):
        """
        Create an archive (tar.gz) with a package source

        Args:
            package (RPM_Package): package
        """
        LOG.info("%s: Preparing archive." % package.name)

        if package.sources:
            archive_to_build_dir = partial(package_source.archive,
                                           directory=self.build_dir)
            archived_sources = map(archive_to_build_dir, package.sources)
            package.sources = archived_sources
            self.archive = self.build_dir
        elif package.repository:
            file_path = package.repository.archive(
                package.expects_source, self.build_dir)
            self.archive = os.path.dirname(file_path)
        elif package.download_source:
            file_path = package._download_source(self.build_dir)
            self.archive = os.path.dirname(file_path)
        else:
            LOG.warning("%s: Package has no external sources.", package.name)
            self.archive = self.build_dir

    def _copy_files_to_chroot(self, package):
        """
        Copy files required to build a package to its build environment (chroot)

        Args:
            package (RPM_Package): package
        """
        for f in os.listdir(package.build_files):
            file_path = os.path.join(package.build_files, f)
            LOG.info("copying %s to %s" % (file_path, self.archive))
            shutil.copy(file_path, self.archive)

    def clean(self):
        """
        Clean build environment
        """
        self.mock.run_command("--clean")

    def clean_cache_dir(self, package):
        """
        Delete the package's cached results directory.

        Args:
            package: package whose cached results will be removed
        """
        if os.path.isdir(package.build_cache_dir):
            LOG.debug("%s: Cleaning previously cached build results."
                      % package.name)
            shutil.rmtree(package.build_cache_dir)

    def _install_external_dependencies(self, package):
        """
        Install the build dependencies of a package

        Args:
            package (RPM_Package): package
        """
        if package.build_dependencies:
            cmd = "--install"
            for dep in package.build_dependencies:
                cmd = " ".join([cmd, " ".join(dep.cached_build_results)])

            LOG.info("%s: Installing dependencies on chroot" % package.name)
            self.mock.run_command(cmd)

    def _create_build_directory(self, package):
        """
        Create build directory

        Args:
            package (RPM_Package): package
        """
        self.build_dir = os.path.join(
            os.path.abspath(CONF.get('work_dir')), 'mock_build',
            self.timestamp, package.name)
        os.makedirs(self.build_dir)

    def _destroy_build_directory(self):
        """
        Destroy build directory
        """
        shutil.rmtree(self.build_dir)

    def _copy_rpms(self, source_dir, target_dir):
        """
        Copy the RPMs created by building a package to a target directory.

        Args:
            source_dir(str): path to the source directory containing the
                RPMs
            target_dir(str): path to the target directory
        """
        if not os.path.exists(target_dir):
            LOG.debug("Creating directory to store RPMs at %s " % target_dir)
            os.makedirs(target_dir)

        LOG.info("Copying RPMs from %s to %s" % (source_dir, target_dir))
        for source_file_name in os.listdir(source_dir):
            if (source_file_name.endswith(".rpm")
                    and not source_file_name.endswith(".src.rpm")):
                LOG.info("Copying RPM file: %s" % source_file_name)
                source_file_path = os.path.join(source_dir, source_file_name)
                target_file_path = os.path.join(target_dir, source_file_name)
                shutil.copy(source_file_path, target_file_path)

    def copy_results(self, package):
        """
        Copy cached build results to the results directory.

        Args:
            package(Package): package whose result files will be copied
        """
        package_build_results_dir = os.path.join(
            CONF.get('result_dir'), 'packages',
            self.timestamp, package.name)
        self._copy_rpms(package.build_cache_dir, package_build_results_dir)

    def create_repository(self):
        """
        Create yum repository in build results directory.
        """
        result_dir = CONF.get('result_dir')
        build_results_dir = os.path.join(
            result_dir, 'packages', self.timestamp)
        yum_repository.create_repository(build_results_dir)

        repo_short_name = "host-os-local-repo-{timestamp}".format(**vars(self))
        repo_long_name = ("OpenPOWER Host OS local repository built at "
                          "{timestamp}".format(**vars(self)))
        repo_url = "file://" + os.path.abspath(build_results_dir)
        repo_config = yum_repository.create_repository_config(
            repo_short_name, repo_long_name, repo_url)

        repo_config_dir = os.path.join(result_dir, "repository_config")
        utils.create_directory(repo_config_dir)
        repo_config_path = os.path.join(
            repo_config_dir, self.timestamp + ".repo")
        with open(repo_config_path, "w") as repo_config_file:
            repo_config_file.write(repo_config)

    def create_latest_symlink_result_dir(self):
        """
        Create latest symlink pointing to the current result directory.
        """
        result_dir = CONF.get('result_dir')
        latest_package_build_results_dir = os.path.join(
            result_dir, 'packages', LATEST_SYMLINK_NAME)
        utils.force_symlink(self.timestamp, latest_package_build_results_dir)

        latest_repo_config_path = os.path.join(
            result_dir, 'repository_config', LATEST_SYMLINK_NAME)
        utils.force_symlink(self.timestamp + ".repo", latest_repo_config_path)
