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

import logging
import os
import subprocess

import pygit2

from lib import exception

LOG = logging.getLogger(__name__)


class Repo(object):
    def __init__(self, package_name=None, clone_url=None, dest_path=None,
                 branch='master', commit_id=None):
        self.repo_name = package_name
        self.repo_url = clone_url
        self.local_path = os.path.join(dest_path, package_name)
        self.repo = None

        # Load if it is an existing git repo
        if os.path.exists(self.local_path):
            try:
                self.repo = pygit2.Repository(self.local_path)
                LOG.info("Found existent repository at destination path %s" % (
                         self.local_path))
                # Reset hard repository so we clean up any changes that may
                # prevent checkout on the right point of the three.
                self.repo.reset(self.repo.head.get_object().oid,
                                pygit2.GIT_RESET_HARD)

            except KeyError:
                raise exception.RepositoryError(package=package_name,
                                                repo_path=dest_path)

        else:
            LOG.info("Cloning into %s..." % self.local_path)
            self.repo = pygit2.clone_repository(self.repo_url,
                                                self.local_path,
                                                checkout_branch=branch)

        if commit_id:
            LOG.info("Checking out into %s" % commit_id)
            obj = self.repo.git_object_lookup_prefix(commit_id)
            self.repo.checkout_tree(obj)
        else:
            LOG.info("Checking out into %s" % branch)
            self.repo.checkout('refs/heads/' + branch)

        cmd = "cd %s ; git submodule init; git submodule update; cd %s" % (
            self.local_path, os.getcwd())
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, shell=True)
        output, error_output = p.communicate()
        LOG.info("STDOUT: %s" % output)
        LOG.info("STDERR: %s" % error_output)

    def archive(self, archive_name, commit_id, build_dir):
        # NOTE(maurosr): CentOS's pygit2  doesn't fully support archives as we
        # need, neither submodules  let's use git itself through
        # subprocess.Popen.
        archive_file = os.path.join(build_dir, archive_name + ".tar")

        # Generates one tar file for each submodule.
        cmd = ("cd %s; git submodule foreach 'git archive --prefix=%s/$path/ "
               "--format tar --output %s HEAD'; cd %s " % (
                   self.local_path,
                   archive_name,
                   os.path.join(build_dir, "$name-" + archive_name + ".tar"),
                   os.getcwd()))

        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, shell=True)
        output, error_output = p.communicate()
        LOG.info("STDOUT: %s" % output)
        LOG.info("STDERR: %s" % error_output)

        # Generates project's archive.
        cmd = ("cd %s; "
               "git archive --prefix=%s/ --format tar --output %s HEAD; "
               "cd %s" % (self.local_path, archive_name,
                          archive_file, os.getcwd()))
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, shell=True)
        output, error_output = p.communicate()
        LOG.info("STDOUT: %s" % output)
        LOG.info("STDERR: %s" % error_output)

        # Concatenate tar files. It's fine to fail when we don't have a
        # submodule and thus no <submodule>-kernel-<version>.tar
        cmd = ("tar --concatenate --file %s %s" % (
            archive_file,
            build_dir + "/*-" + archive_name + ".tar"))
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, shell=True)
        output, error_output = p.communicate()
        LOG.info("STDOUT: %s" % output)
        LOG.info("STDERR: %s" % error_output)

        cmd = "gzip %s" % archive_file
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, shell=True)
        output, error_output = p.communicate()
        LOG.info("STDOUT: %s" % output)
        LOG.info("STDERR: %s" % error_output)

        return archive_file + ".gz"
