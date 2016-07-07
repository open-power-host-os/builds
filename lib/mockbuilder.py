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
import logging
import os
import shutil
import subprocess

from lib import config
from lib import build_system

CONF = config.get_config().CONF
LOG = logging.getLogger(__name__)
MOCK_CHROOT_BUILD_DIR = "/builddir/build/SOURCES"


class Mock(build_system.PackageBuilder):
    def __init__(self, config):
        super(Mock, self).__init__()
        self.mock_config = config
        self.result_dir = CONF.get('default').get('result_dir')
        self.build_dir = None
        self.archive = None

    def build(self, package):
        self._prepare(package)
        self._build_srpm(package)
        self._install_external_dependencies(package)
        cmd = "mock -r %s --rebuild %s --no-clean --resultdir=%s" % (
            self.mock_config, self.build_dir + "/*.rpm", self.build_dir)

        if package.rpmmacro:
            cmd = cmd + " --macro-file=%s" % package.rpmmacro

        LOG.info("Command: %s" % cmd)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, shell=True)
        output, error_output = p.communicate()
        LOG.info("STDOUT: %s" % output)
        LOG.info("STDERR: %s" % error_output)

        # On success save rpms and destroy build directory unless told
        # otherwise.
        if not p.returncode:
            self._save_rpm(package)
            if (CONF.get('keep_build_dir', None) or
                    not CONF.get('keep_builddir')):
                self._destroy_build_directory()

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
        self._create_build_directory(package)
        self._prepare_archive(package)
        self._prepare_chroot(package)

    def _prepare_archive(self, package):
        self.archive = package.repository.archive(package.expects_source,
                                                  package.commit_id,
                                                  self.build_dir)

    def _prepare_chroot(self, package):
        cmd = "mock --init -r %s " % self.mock_config

        if package.build_files:
            cmd = cmd + " --copyin %s %s" % (package.build_files,
                                             MOCK_CHROOT_BUILD_DIR)

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

    def _install_external_dependencies(self, package):
        cmd = "mock -r %s " % self.mock_config
        if package.build_dependencies or package.dependencies:
            install = " --install"
            for dep in package.build_dependencies:
                install = " ".join([install, " ".join(dep.result_packages)])
            for dep in package.dependencies:
                install = " ".join([install, " ".join(dep.result_packages)])

            cmd = cmd + install
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

    def _destroy_build_directory(self):
        shutil.rmtree(self.build_dir)

    def _save_rpm(self, package):
        if not os.path.exists(self.result_dir):
            LOG.info("Creating directory to store RPM at %s " %
                     self.result_dir)
            os.makedirs(self.result_dir)
            os.chmod(self.result_dir, 0777)

        for f in os.listdir(self.build_dir):
            if f.endswith(".rpm") and not f.endswith(".src.rpm"):
                LOG.info("Saving %s at result directory %s" % (f,
                         self.result_dir))
                orig = os.path.join(self.build_dir, f)
                dest = os.path.join(self.result_dir, f)
                shutil.move(orig, dest)
                package.result_packages.append(dest)
