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

from lib import iso_builder

LOG = logging.getLogger(__name__)


def run(CONF):
    build_iso = CONF.get('iso')
    build_install_tree = CONF.get('install_tree')

    if not build_iso and not build_install_tree:
        LOG.info("Neither --iso nor --install-tree specified, nothing to do here")
    else:
        builder = iso_builder.MockPungiIsoBuilder(CONF)
        builder.build()
        builder.clean()
        LOG.info("build-images finished succesfully")
