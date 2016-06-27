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

import datetime
import glob
import logging
import os
import shutil
import subprocess

from lib import build_system

LOG = logging.getLogger(__name__)
MOCK_CHROOT_BUILD_DIR = "/builddir/build/SOURCES"


class Mock(build_system.PackageBuilder):
    def __init__(self, config, **kwargs):
        super(Mock, self).__init__()
        self.mock_config = config
        self.kwargs = kwargs
        self.build_dir = None
        self.archive = None

    def build(self, package):
        self._create_build_directory(package)
        self._prepare(package)
        self._build_srpm(package)
        cmd = "mock -r %s --rebuild %s --no-clean " % (
            self.mock_config, self.build_dir + "/*.rpm")

        if package.rpmmacro:
            cmd = cmd + " --macro-file=%s" % package.rpmmacro

        LOG.info("Command: %s" % cmd)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, shell=True)
        output, error_output = p.communicate()
        LOG.info("STDOUT: %s" % output)
        LOG.info("STDERR: %s" % error_output)

    def _build_srpm(self, package):
        cmd = ("mock -r %s --buildsrpm --no-clean --spec %s --source %s "
               "--resultdir=%s" % (self.mock_config,
                                   package.specfile,
                                   self.archive,
                                   self.build_dir))

        LOG.info("Command: %s" % cmd)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, shell=True)
        output, error_output = p.communicate()
        LOG.info("STDOUT: %s" % output)
        LOG.info("STDERR: %s" % error_output)

    def _prepare(self, package):
        self._prepare_chroot(package)
        self._prepare_archive(package)

    def _prepare_archive(self, package):
        self.archive = package.repository.archive(package.expects_source,
                                                  package.commit_id,
                                                  self.build_dir)

    def _prepare_chroot(self, package):
        cmd = "mock --init -r %s " % self.mock_config

        if package.build_files:
            cmd = cmd + " --copyin %s %s" % (package.build_files,
                                             MOCK_CHROOT_BUILD_DIR)

        if 'deps' in self.kwargs:
            cmd = cmd + "--install %s " % " ".join(self.kwargs['deps'])

        LOG.info("Command: %s" % cmd)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, shell=True)
        output, error_output = p.communicate()
        LOG.info("STDOUT: %s" % output)
        LOG.info("STDERR: %s" % error_output)

    def clean(self):
        cmd = "mock --clean "
        LOG.info("Command: %s" % cmd)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, shell=True)
        output, error_output = p.communicate()
        LOG.info("STDOUT: %s" % output)
        LOG.info("STDERR: %s" % error_output)

    def _create_build_directory(self, package):
        self.build_dir = os.path.join(
            os.getcwd(), 'build',
            datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
        os.makedirs(self.build_dir)
        os.chmod(self.build_dir, 0777)
