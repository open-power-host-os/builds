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


import datetime
import logging
import os
import shutil

from lib import config
from lib import build_system
from lib import exception
from lib import package_source
from lib import utils

CONF = config.get_config().CONF
LOG = logging.getLogger(__name__)
MOCK_CHROOT_BUILD_DIR = "/builddir/build/SOURCES"


class Mock(build_system.PackageBuilder):
    def __init__(self, config_file):
        super(Mock, self).__init__()
        binary_file = CONF.get('default').get('mock_binary')
        extra_args = CONF.get('default').get('mock_args')
        self.result_dir = CONF.get('default').get('result_dir')
        self.build_dir = None
        self.archive = None
        self.timestamp = datetime.datetime.now().isoformat()
        self.common_mock_args = (
            "%(binary_file)s -r %(config_file)s %(extra_args)s" % dict(
                binary_file=binary_file, config_file=config_file,
                extra_args=extra_args))

    def initialize(self):
        """
        Initializes the configured chroot by installing the essential
        packages. This setup is common for all packages that are built
        and needs to be done only once.
        """
        cmd = self.common_mock_args + " --init"
        utils.run_command(cmd)

    def build(self, package):
        LOG.info("%s: Starting build process" % package.name)
        self._prepare(package)
        self._build_srpm(package)
        self._install_external_dependencies(package)
        cmd = (self.common_mock_args + " --rebuild %s --no-clean --resultdir=%s"
               % (self.build_dir + "/*.rpm", self.build_dir))

        if package.rpmmacro:
            cmd = cmd + " --macro-file=%s" % package.rpmmacro

        LOG.info("%s: Building RPM" % package.name)
        try:
            utils.run_command(cmd)

            # On success save rpms and destroy build directory unless told
            # otherwise.
        except exception.SubprocessError:
            LOG.info("%s: Failed to build RPMs, build artifacts are kept at "
                  "%s" % (package.name, self.build_dir))
            raise

        msg = "%s: Success! RPMs built!" % (package.name)
        self._save_rpm(package)
        LOG.info(msg)
        LOG.info(msg)
        if not CONF.get('default').get('keep_builddir'):
            self._destroy_build_directory()

    def _build_srpm(self, package):
        LOG.info("%s: Building SRPM" % package.name)
        cmd = (self.common_mock_args +
               " --buildsrpm --no-clean --spec %s --sources %s --resultdir=%s"
               % (package.spec_file.path, self.archive, self.build_dir))
        utils.run_command(cmd)

    def _prepare(self, package):
        self._create_build_directory(package)
        self._prepare_archive(package)
        if package.build_files:
            self._copy_files_to_chroot(package)

    def _prepare_archive(self, package):
        LOG.info("%s: Preparing archive." % package.name)

        if package.sources:
            archive_to_build_dir = partial(package_source.archive,
                                           directory=self.build_dir)
            archived_sources = map(archive_to_build_dir, package.sources)
            package.sources = archived_sources
            self.archive = self.build_dir
        elif package.repository:
            file_path = package.repository.archive(package.expects_source,
                                                   package.commit_id,
                                                   self.build_dir)
            self.archive = os.path.dirname(file_path)
        else:
            file_path = package._download_source(self.build_dir)
            self.archive = os.path.dirname(file_path)

    def _copy_files_to_chroot(self, package):
        for f in os.listdir(package.build_files):
            file_path = os.path.join(package.build_files, f)
            LOG.info("copying %s to %s" % (file_path, self.archive))
            shutil.copy(file_path, self.archive)

    def clean(self):
        utils.run_command(self.common_mock_args + " --clean")

    def _install_external_dependencies(self, package):
        if package.build_dependencies or package.dependencies:
            cmd = self.common_mock_args
            install = " --install"
            for dep in package.build_dependencies:
                install = " ".join([install, " ".join(dep.result_packages)])
            for dep in package.dependencies:
                install = " ".join([install, " ".join(dep.result_packages)])

            cmd = cmd + install
            LOG.info("%s: Installing dependencies on chroot" % package.name)
            utils.run_command(cmd)

    def _create_build_directory(self, package):
        self.build_dir = os.path.join(
            os.getcwd(), 'build', self.timestamp, package.name)
        os.makedirs(self.build_dir)
        os.chmod(self.build_dir, 0777)

    def _destroy_build_directory(self):
        shutil.rmtree(self.build_dir)

    def _save_rpm(self, package):
        if not os.path.exists(self.result_dir):
            LOG.info("Creating directory to store RPM at %s " %
                     self.result_dir)
            os.makedirs(self.result_dir)
            os.chmod(self.result_dir, 0777)

        LOG.info("%s: Saving RPMs at %s" % (package.name, self.result_dir))
        for f in os.listdir(self.build_dir):
            if f.endswith(".rpm") and not f.endswith(".src.rpm"):
                LOG.info("Saving %s at result directory %s" % (f,
                         self.result_dir))
                orig = os.path.join(self.build_dir, f)
                dest = os.path.join(self.result_dir, f)
                shutil.move(orig, dest)
                package.result_packages.append(dest)
