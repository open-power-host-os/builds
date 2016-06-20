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

import pygit2

from lib import exception

LOG = logging.getLogger(__name__)


class Repo(object):
    def __init__(self, package_name=None, clone_url=None, dest_path=None,
                 branch='master'):
        self.repo_name = package_name
        self.repo_url = clone_url
        self.local_path = os.path.join(dest_path, package_name)
        self.repo = None

        # Load if it is an existing git repo
        if os.path.exists(self.local_path):
            try:
                self.repo = pygit2.Repository(self.local_path)
                self.repo.checkout(branch)
                LOG.info("Found existent repository at destination path %s" % (
                    self.local_path))

            except KeyError:
                raise exception.RepositoryError(package=package_name,
                                                repo_path=dest_path)

        else:
            LOG.info("Cloning into %s..." % self.local_path)
            self.repo = pygit2.clone_repository(self.repo_url,
                                                self.local_pathi,
                                                checkout_branch=branch)
