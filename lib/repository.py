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
import utils

import pygit2

from lib import exception

LOG = logging.getLogger(__name__)


class Repo(object):
    def __init__(self, repo_name=None, clone_url=None, dest_path=None,
                 refname='master', commit_id=None):
        self.repo_name = repo_name
        self.repo_url = clone_url
        self.local_path = os.path.join(dest_path, repo_name)
        self.repo = None

        self._setup()
        self._checkout(refname, commit_id)

    def _setup(self):
        """
        Load existing repository or clone to target directory.
        """
        if os.path.exists(self.local_path):
            try:
                self.repo = pygit2.Repository(self.local_path)
                LOG.info("Found existent repository at destination path %s" % (
                         self.local_path))
                # Reset hard repository so we clean up any changes that may
                # prevent checkout on the right point of the tree.
                self.repo.reset(self.repo.head.get_object().oid,
                                pygit2.GIT_RESET_HARD)

            except KeyError:
                raise exception.RepositoryError(repo_name=self.repo_name,
                                                repo_path=self.local_path)

        else:
            try:
                LOG.info("Cloning into %s..." % self.local_path)
                self.repo = pygit2.clone_repository(self.repo_url,
                                                    self.local_path)
            except pygit2.GitError:
                msg = "Failed to clone repository"
                LOG.error(msg)
                raise exception.RepositoryError(message=msg)

    def _checkout(self, refname, commit_id):
        """
        Checkout commit ID, if specified, or refname otherwise.
        """
        for remote in self.repo.remotes:
            try:
                remote.fetch()
                LOG.info("Fetched changes for %s" % remote.name)
            except pygit2.GitError:
                LOG.info("Failed to fetch %s remote for %s"
                         % (remote.name, self.repo_name))
                pass
            else:
                LOG.info("%(repo_name)s Repository updated" % vars(self))

        try:
            if commit_id:
                LOG.info("Checking out into %s" % commit_id)
                obj = self.repo.git_object_lookup_prefix(commit_id)
                self.repo.checkout_tree(
                    obj, strategy=pygit2.GIT_CHECKOUT_FORCE)
                self.repo.reset(obj.oid, pygit2.GIT_RESET_HARD)
            else:
                reference = self._get_reference(refname)
                # GIT_CHECKOUT_FORCE strategy cleans up the index
                LOG.info("Checking out into %s" % refname)
                self.repo.checkout(reference,
                                   strategy=pygit2.GIT_CHECKOUT_FORCE)
                self.repo.reset(self.repo.head.target, pygit2.GIT_RESET_HARD)
        except ValueError:
            ref = commit_id if commit_id else refname
            raise exception.RepositoryError(
                message="Could not find reference %s at %s repository" %
                (ref, self.repo_name))

        self._update_submodules()

    def _get_reference(self, short_reference_string):
        """
        Get repository reference (branch, tag) based on a short reference
        suffix string.
        """
        prefixes = ["refs/tags", "refs/heads", "refs/remotes"]
        for remote in self.repo.remotes:
            prefixes.append(os.path.join("refs/remotes", remote.name))
        for prefix in prefixes:
            reference_string = os.path.join(prefix, short_reference_string)
            LOG.debug("Trying to get reference: %s", reference_string)
            try:
                return self.repo.lookup_reference(reference_string)
            except KeyError:
                pass
        else:
            raise exception.RepositoryError(
                message="Reference not found in repository")

    def _update_submodules(self):
        """
        Update repository submodules, initializing them if needed.
        """
        cmd = "git submodule init; git submodule update"
        utils.run_command(cmd, cwd=self.local_path)

    def archive(self, archive_name, commit_id, build_dir):
        # NOTE(maurosr): CentOS's pygit2  doesn't fully support archives as we
        # need, neither submodules  let's use git itself through
        # subprocess.Popen in utils.command
        archive_file = os.path.join(build_dir, archive_name + ".tar")

        # Generates one tar file for each submodule.
        cmd = ("git submodule foreach 'git archive --prefix=%s/$path/ "
               "--format tar --output %s HEAD'" % (
                   archive_name,
                   os.path.join(build_dir, "$sha1-%s.tar" % archive_name)))
        utils.run_command(cmd, cwd=self.local_path)

        # Generates project's archive.
        cmd = "git archive --prefix=%s/ --format tar --output %s HEAD" % (
            archive_name, archive_file)
        utils.run_command(cmd, cwd=self.local_path)

        # Concatenate tar files. It's fine to fail when we don't have a
        # submodule and thus no <submodule>-kernel-<version>.tar
        cmd = "tar --concatenate --file %s %s" % (
            archive_file,
            build_dir + "/*-" + archive_name + ".tar")
        try:
            utils.run_command(cmd)
        except exception.SubprocessError:
            pass

        cmd = "gzip %s" % archive_file
        utils.run_command(cmd)
        return archive_file + ".gz"
