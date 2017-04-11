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


def get_git_repository(remote_repo_url, parent_dir_path, name=None):
    """
    Get a local git repository located in a subdirectory of the parent
    directory, named after the file name of the URL path (git default),
    updating the main remote URL, if needed.
    If the local repository does not exist, clone it from the remote
    URL.

    Args:
        remote_repo_url (str): URL to remote Git repository
        parent_dir_path (str): path to parent directory of the repository
            directory
        name (str): name of the repository directory. Leave empty to infer the
            name from the URL
    """
    # infer git repository name from its URL
    url_parts = urlparse.urlparse(remote_repo_url)
    if not name:
        name = os.path.basename(os.path.splitext(url_parts.path)[0])

    repo_path = os.path.join(parent_dir_path, name)
    if os.path.exists(repo_path):
        MAIN_REMOTE_NAME = "origin"
        repo = GitRepository(repo_path)
        if any(remote.name == MAIN_REMOTE_NAME for remote in repo.remotes):
            previous_url = repo.remotes[MAIN_REMOTE_NAME].url
            if previous_url != remote_repo_url:
                LOG.debug("Removing previous {name}'s repository remote with "
                          "URL '{previous_url}'"
                          .format(name=name, previous_url=previous_url))
                repo.delete_remote(MAIN_REMOTE_NAME)
        if not any(remote.name == MAIN_REMOTE_NAME for remote in repo.remotes):
            LOG.debug("Creating {name}'s repository remote with URL '{url}'"
                      .format(name=name, url=remote_repo_url))
            repo.create_remote(MAIN_REMOTE_NAME, remote_repo_url)
        return repo
    else:
        CONF = config.get_config().CONF
        return GitRepository.clone_from(
            remote_repo_url, repo_path,
            proxy=CONF.get('common').get('http_proxy'))


def get_svn_repository(remote_repo_url, repo_path):
    """
    Get a local subversion repository located in a directory.
    If it does not exist, check it out from the specified URL.
    """
    if os.path.exists(repo_path):
        return SvnRepository(remote_repo_url, repo_path)
    else:
        # TODO: setup HTTP proxy by editing ~/.subversion/servers
        return SvnRepository.checkout_from(remote_repo_url,
                                           repo_path)


class GitRepository(git.Repo):

    @classmethod
    def clone_from(cls, remote_repo_url, repo_path, proxy=None, *args, **kwargs):
        """
        Clone a repository from a remote URL into a local path.
        """
        LOG.info("Cloning repository from '%s' into '%s'" %
                 (remote_repo_url, repo_path))
        try:
            if proxy:
                git_cmd = git.cmd.Git()
                git_cmd.execute(['git',
                                 '-c',
                                 "http.proxy='{}'".format(proxy),
                                 'clone',
                                 remote_repo_url,
                                 repo_path])
                return GitRepository(repo_path)
            else:
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

    def checkout(self, ref_name):
        """
        Check out the reference name, resetting the index state.
        The reference may be a branch, tag or commit.
        """
        LOG.info("%(name)s: Fetching repository remotes"
                 % dict(name=self.name))
        for remote in self.remotes:
            try:
                remote.fetch()
            except git.exc.GitCommandError:
                LOG.debug("Failed to fetch %s remote for %s"
                          % (remote.name, self.name))
                pass
            else:
                LOG.info("Fetched changes for %s" % remote.name)

        commit_id = self._get_reference(ref_name)
        LOG.info("%(name)s: Checking out reference %(ref)s pointing to commit "
                 "%(commit)s"
                 % dict(name=self.name, ref=ref_name, commit=commit_id))
        self.head.reference = commit_id
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
                message="Reference '%s' not found in repository" % ref_name)

    def _update_submodules(self):
        """
        Update repository submodules, initializing them if needed.
        """
        for submodule in self.submodules:
            LOG.info("Updating submodule %(name)s from %(url)s"
                     % dict(name=submodule.name, url=submodule.url))
            submodule.update(init=True)

    def archive(self, archive_name, commit_id, build_dir):
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

    def commit_changes(self, commit_message, committer_name, committer_email):
        """
        Commit all changes made to the repository.

        Args:
            commit_message (str): message describing the commit
            committer_name (str): committer name
            committer_email (str): committer email
        """
        LOG.info("Adding files to repository index")
        self.index.add(["*"])

        LOG.info("Committing changes to local repository")
        actor = git.Actor(committer_name, committer_email)
        self.index.commit(commit_message, author=actor, committer=actor)

    def push_head_commits(self, remote_repo_url, remote_repo_branch):
        """
        Push commits from local Git repository head to the remote Git
        repository, using the system's configured SSH credentials.

        Args:
            remote_repo_url (str): remote git repository URL
            remote_repo_branch (str): remote git repository branch

        Raises:
            repository.PushError: if push fails
        """
        REPO_REMOTE_NAME = "push-remote"
        LOG.info("Creating remote named '{name}' for URL '{url}'"
                 .format(name=REPO_REMOTE_NAME, url=remote_repo_url))
        self.create_remote(REPO_REMOTE_NAME, remote_repo_url)

        LOG.info("Pushing changes to remote repository branch '{}'"
                 .format(remote_repo_branch))
        remote = self.remote(REPO_REMOTE_NAME)
        refspec = "HEAD:refs/heads/{}".format(remote_repo_branch)
        push_info = remote.push(refspec=refspec)[0]
        LOG.debug("Push result: {}".format(push_info.summary))
        if git.PushInfo.ERROR & push_info.flags:
            raise PushError(push_info)


class SvnRepository():

    @classmethod
    def checkout_from(cls, remote_repo_url, repo_path):
        """
        Checkout a repository from a remote URL into a local path.
        """
        LOG.info("Checking out repository from '%s' into '%s'" %
                 (remote_repo_url, repo_path))

        command = 'svn checkout '

        CONF = config.get_config().CONF
        proxy = CONF.get('common').get('http_proxy')

        if proxy:
            url = urlparse.urlparse(proxy)
            host = url.scheme + '://' + url.hostname
            port = url.port
            options = ("servers:global:http-proxy-host='%s'" % host,
                       "servers:global:http-proxy-port='%s'" % port)

            proxy_conf = ['--config-option ' + option for option in options]

            command += ' '.join(proxy_conf) + ' '

        command += '%(remote_repo_url)s %(local_target_path)s' % \
                   {'remote_repo_url': remote_repo_url,
                    'local_target_path': repo_path}
        try:
            utils.run_command(command)
            return SvnRepository(remote_repo_url, repo_path)
        except:
            message = "Failed to clone repository"
            LOG.exception(message)
            raise exception.RepositoryError(message=message)

    def __init__(self, remote_repo_url, local_repo_path):
        self.url = remote_repo_url
        self.working_copy_dir = local_repo_path
        LOG.info("Found existent repository at destination path %s" % local_repo_path)

    @property
    def name(self):
        return os.path.basename(self.working_copy_dir)

    def checkout(self, revision):
        """
        Check out a revision.
        """
        LOG.info("%(name)s: Updating svn repository"
                 % dict(name=self.name))
        try:
            utils.run_command("svn update", cwd=self.working_copy_dir)
        except:
            LOG.debug("%(name)s: Failed to update svn repository"
                      % dict(name=self.name))
            pass
        else:
            LOG.info("%(name)s: Updated svn repository" % dict(name=self.name))

        LOG.info("%(name)s: Checking out revision %(revision)s"
                 % dict(name=self.name, revision=revision))
        try:
            utils.run_command("svn checkout %(repo_url)s@%(revision)s ." %
                dict(repo_url=self.url, revision=revision),
                cwd=self.working_copy_dir)
        except:
            message = ("Could not find revision %s at %s repository"
                       % (revision, self.name))
            LOG.exception(message)
            raise exception.RepositoryError(message=message)
