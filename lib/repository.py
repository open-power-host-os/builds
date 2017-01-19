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
import urlparse
import utils

import git
import gitdb

from lib import config
from lib import exception


LOG = logging.getLogger(__name__)


class PushError(Exception):

    def __init__(self, push_info):
        message = ("Error pushing to remote reference %s"
                   % push_info.remote_ref.name)
        super(PushError, self).__init__(message)


def get_git_repository(remote_repo_url, parent_dir_path, shallow=False):
    """
    Get a local git repository located in a subdirectory of the parent directory,
    named after the file name of the URL path (git default).
    If it does not exist, clone it from the specified URL.
    """
    # infer git repository name from its URL
    url_parts = urlparse.urlparse(remote_repo_url)
    name = os.path.basename(os.path.splitext(url_parts.path)[0])

    repo_path = os.path.join(parent_dir_path, name)
    if os.path.exists(repo_path):
        return GitRepository(repo_path)
    else:
        CONF = config.get_config().CONF
        options = {}
        http_proxy = CONF.get('http_proxy')
        if http_proxy:
            options["config"] = "http.proxy=%s" % http_proxy
        if shallow:
            options["depth"] = 1
        return GitRepository.clone_from(remote_repo_url,
                                        repo_path,
                                        **options)


class GitRepository(git.Repo):

    @classmethod
    def clone_from(cls, remote_repo_url, repo_path, *args, **kwargs):
        """
        Clone a repository from a remote URL into a local path.
        """
        LOG.info("Cloning repository from '%s' into '%s'" %
                 (remote_repo_url, repo_path))
        try:
            return super(GitRepository, cls).clone_from(
                remote_repo_url, repo_path, *args, **kwargs)
        except git.exc.GitCommandError:
            message = "Failed to clone repository"
            LOG.exception(message)
            raise exception.RepositoryError(message=message)

    def __init__(self, repo_path, *args, **kwargs):
        super(GitRepository, self).__init__(repo_path, *args, **kwargs)
        LOG.info("Found existent repository at destination path %s" % repo_path)

    @property
    def name(self):
        return os.path.basename(self.working_tree_dir)

    def checkout(self, ref_name, ref_to_fetch=None):
        """
        Check out the reference name, resetting the index state.
        The reference may be a branch, tag or commit.
        """
        LOG.info("%(name)s: Fetching repository remotes"
                 % dict(name=self.name))
        for remote in self.remotes:
            try:
                if ref_to_fetch:
                    remote.fetch("%s:%s" % (ref_to_fetch, ref_name))
                else:
                    remote.fetch()
            except git.exc.GitCommandError:
                LOG.debug("Failed to fetch %s remote for %s"
                          % (remote.name, self.name))
                pass
            else:
                LOG.info("Fetched changes for %s" % remote.name)

        LOG.info("%(name)s: Checking out reference %(ref)s"
                 % dict(name=self.name, ref=ref_name))
        self.head.reference = self._get_reference(ref_name)
        try:
            self.head.reset(index=True, working_tree=True)
        except git.exc.GitCommandError:
            message = ("Could not find reference %s at %s repository"
                       % (ref_name, self.name))
            LOG.exception(message)
            raise exception.RepositoryError(message=message)

        self._update_submodules()

    def _get_reference(self, ref_name):
        """
        Get repository commit based on a reference name (branch, tag,
        commit ID). Remote references have higher priority than local
        references.
        """
        refs_names = []
        for remote in self.remotes:
            refs_names.append(os.path.join(remote.name, ref_name))
        refs_names.append(ref_name)
        for ref_name in refs_names:
            try:
                return self.commit(ref_name)
            except gitdb.exc.BadName:
                pass
        else:
            raise exception.RepositoryError(
                message="Reference not found in repository")

    def _update_submodules(self):
        """
        Update repository submodules, initializing them if needed.
        """
        for submodule in self.submodules:
            LOG.info("Updating submodule %(name)s from %(url)s"
                     % dict(name=submodule.name, url=submodule.url))
            submodule.update(init=True)

    def archive(self, archive_name, commit_id, build_dir, archive_src_dir=None):
        # TODO(olavph): use git.Repo.archive instead of run_command
        archive_file = os.path.join(build_dir, archive_name + ".tar")

        # Generates one tar file for each submodule.
        cmd = ("git submodule foreach 'git archive --prefix=%s/$path/ "
               "--format tar --output %s HEAD'" % (
                   archive_name,
                   os.path.join(build_dir, "$sha1-%s.tar" % archive_name)))
        utils.run_command(cmd, cwd=self.working_tree_dir)

        # Generates project's archive.
        cmd = "git archive --prefix=%s/ --format tar --output %s HEAD" % (
            archive_name, archive_file)
        if archive_src_dir:
            cmd += " %s" % archive_src_dir
        utils.run_command(cmd, cwd=self.working_tree_dir)

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
