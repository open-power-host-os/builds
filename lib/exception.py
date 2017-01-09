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


class BaseException(Exception):

    DEFAULT_MESSAGE = "Failed to build packages"
    error_code = 1

    def __init__(self, message=None, **kwargs):
        if message is None:
            message = self.DEFAULT_MESSAGE % kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)
        super(BaseException, self).__init__(message)


class DistributionError(BaseException):
    DEFAULT_MESSAGE = "Distribution not Supported"


class DistributionDetectionError(DistributionError):
    DEFAULT_MESSAGE = "Failed to detect system's GNU/Linux distribution"


class DistributionNotSupportedError(DistributionError):
    DEFAULT_MESSAGE = "%(distribution)s distribution is not supported"


class DistributionVersionNotSupportedError(DistributionError):
    DEFAULT_MESSAGE = "%(distribution)s version %(version)s is not supported"


class PackageError(BaseException):
    DEFAULT_MESSAGE = "Failed to gather %(package)s's information"


class PackageSpecError(PackageError):
    DEFAULT_MESSAGE = (
        "%(package)s's spec for %(distro)s %(distro_version)s not Found.")


class PackageDescriptorError(PackageError):
    DEFAULT_MESSAGE = "Missing data in %(package)s's YAML descriptor"


class RepositoryError(BaseException):
    DEFAULT_MESSAGE = (
        "Failed to setup %(repo_name)s's repository at %(repo_path)s.")


class SubprocessError(BaseException):
    DEFAULT_MESSAGE = (
        "%(cmd)s returned non-zero exit code: ret:%(returncode)i, "
        "stdout: %(stdout)s, stderr: %(stderr)s")
