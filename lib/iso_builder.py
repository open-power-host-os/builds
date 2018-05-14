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

from lib import exception
from lib import utils
from lib import distro_utils
from lib import packages_groups_xml_creator
from lib import yum_repository
from lib.constants import LATEST_SYMLINK_NAME
from lib.mock import Mock

LOG = logging.getLogger(__name__)
ISO_REPO_MINIMAL_PACKAGES_GROUPS = ["core", "anaconda-tools"]
ISO_REPO_MINIMAL_PACKAGES = [
    "anaconda",
    "anaconda-dracut",
    "nfs-utils",
    "redhat-upgrade-dracut",
    "grub2",
    "yum-langpacks",
    # Packages needed for VNC installation
    "metacity",
    "bitmap-fangsongti-fonts",
    "dejavu-sans-fonts dejavu-sans-mono-fonts",
    "kacst-farsi-fonts",
    "kacst-qurn-fonts",
    "lklug-fonts",
    "lohit-assamese-fonts",
    "lohit-bengali-fonts",
    "lohit-devanagari-fonts",
    "lohit-gu*-fonts",
    "lohit-kannada-fonts",
    "lohit-odia-fonts",
    "lohit-tamil-fonts",
    "lohit-telugu-fonts",
    "madan-fonts",
    "nhn-nanum-gothic-fonts",
    "smc-meera-fonts",
    "thai-scalable-waree-fonts",
    "vlgothic-fonts",
    "wqy-microhei-fonts",
    "sil-abyssinica-fonts",
    "xorg-x11-fonts-misc",
    "aajohan-comfortaa-fonts",
    "abattis-cantarell-fonts",
    "sil-scheherazade-fonts",
    "jomolhari-fonts",
    "khmeros-base-fonts",
    "sil-padauk-fonts",
    # Packages required by lorax
    "dracut-fips", # https://github.com/weldr/lorax/pull/230 (commit: 7aa7118)
    "kernel-bootwrapper",
]
CHROOT_HOST_OS_REPO_PATH = "/host-os-repo"
CHROOT_MERGED_REPO_PATH = "/merged-repo"
CHROOT_MERGED_REPO_CONFIG_FILE_PATH = "/merged-repo.conf"
CHROOT_REPO_CONFIG_FILE_PATH = "/all-repos.conf"
GROUPS_FILE_NAME = "host-os-comps.xml"
GROUPS_FILE_CHROOT_PATH = os.path.join("/", GROUPS_FILE_NAME)


class MockPungiIsoBuilder(object):

    def __init__(self, config):
        self.config = config
        self.work_dir = self.config.get('work_dir')
        self.timestamp = datetime.datetime.now().isoformat()
        self.result_dir = os.path.join(self.config.get('result_dir'),
            'iso', self.timestamp)
        self.distro = self.config.get("iso_name")
        self.version = (self.config.get("iso_version")
                            or datetime.date.today().strftime("%y%m%d"))
        (_, _, self.arch) = distro_utils.detect_distribution()
        self.pungi_binary = self.config.get('pungi_binary') or "pungi"
        self.pungi_args = self.config.get('pungi_args') or ""
        self.build_iso = self.config.get('iso')
        self.build_install_tree = self.config.get('install_tree')

        self._init_mock()

        utils.create_directory(self.result_dir)

    def _init_mock(self):
        """
        Initialize Mock instance with common mock arguments.
        """
        distro = distro_utils.get_distro(
            self.config.get('distro_name'),
            self.config.get('distro_version'),
            self.config.get('architecture'))
        mock_config_file_name = "build-images-%s-%s-%s.cfg" % (
            distro.name, distro.version, distro.architecture)
        mock_config_file_path = os.path.join(
            "config/mock", distro.name, distro.version,
            mock_config_file_name)
        if not os.path.isfile(mock_config_file_path):
            raise exception.BaseException(
                "Mock config file not found at %s" % mock_config_file_path)

        self.mock = Mock(mock_config_file_path, self.timestamp)

    def build(self):
        LOG.info("Starting ISO build process")
        self._setup()
        self._build()
        self._save()

    def _setup(self):
        LOG.info("Initializing a chroot")
        self.mock.run_command("--init")

        package_list = [
            "yum-plugin-priorities", "yum-utils", "createrepo", "pungi"]
        LOG.info("Installing %s inside the chroot" % " ".join(package_list))
        self.mock.run_command("--install %s" % " ".join(package_list))

        self._create_host_os_repo()
        self._create_merged_repo()

        self._create_iso_kickstart()

    def _create_host_os_repo(self):
        LOG.info("Creating Host OS yum repository inside chroot")

        LOG.debug("Creating yum repository directory")
        self.mock.run_command(
            "--shell 'mkdir -p %s'" % CHROOT_HOST_OS_REPO_PATH)

        LOG.debug("Creating package groups metadata file (comps.xml)")
        groups_file_content = packages_groups_xml_creator.create_comps_xml(
            self.config.get('installable_environments'))
        groups_file_path = os.path.join(self.work_dir, GROUPS_FILE_NAME)
        try:
            with open(groups_file_path, 'wt') as groups_file:
                groups_file.write(groups_file_content)
        except IOError:
            LOG.error("Failed to write XML to %s file." % groups_file_path)
            raise
        self.mock.run_command("--copyin %s %s" %
                              (groups_file_path, GROUPS_FILE_CHROOT_PATH))

        LOG.debug("Copying packages to chroot")
        packages_dir = self.config.get('packages_dir')
        rpm_files = utils.recursive_glob(packages_dir, "*.rpm")
        self.mock.run_command(
            "--copyin %s %s" % (" ".join(rpm_files), CHROOT_HOST_OS_REPO_PATH))

        LOG.debug("Creating yum repository")
        create_repo_command = (
            "--shell 'createrepo --verbose --groupfile {groups_file} "
            "{repo_path}'".format(groups_file=GROUPS_FILE_CHROOT_PATH,
                                  repo_path=CHROOT_HOST_OS_REPO_PATH))
        self.mock.run_command(create_repo_command)

    def _create_merged_repo(self):
        LOG.info("Creating base distro and Host OS merged yum repository inside chroot")

        LOG.debug("Creating yum repository directory")
        self.mock.run_command(
            "--shell 'mkdir -p %s'" % CHROOT_MERGED_REPO_PATH)

        LOG.debug("Creating yum repository configuration")
        packages_dir_url = "file://" + os.path.abspath(CHROOT_HOST_OS_REPO_PATH)
        repo_config = yum_repository.YUM_MAIN_CONFIG
        repo_config += yum_repository.create_repository_config(
            "host-os-local-repo", "OpenPOWER Host OS local repository",
            packages_dir_url, priority=1)
        distro_repos = self.config.get('distro_repos')
        for repo in distro_repos:
            repo_config += yum_repository.create_repository_config(
                repo["name"], repo["name"], repo["url"],
                url_type=repo["url_type"], priority=2)
        repo_config_file_path = os.path.join(
            self.work_dir, os.path.basename(CHROOT_REPO_CONFIG_FILE_PATH))
        with open(repo_config_file_path, 'w') as repo_config_file:
            repo_config_file.write(repo_config)
        self.mock.run_command("--copyin %s %s" % (
            repo_config_file_path, CHROOT_REPO_CONFIG_FILE_PATH))

        LOG.debug("Downloading packages")
        YUM_INSTALL_ROOT_DIR = "/yum_install_root"
        iso_repo_packages_groups = (
            ISO_REPO_MINIMAL_PACKAGES_GROUPS
            + self.config.get('iso_repo_packages_groups'))
        iso_repo_packages = (
            ISO_REPO_MINIMAL_PACKAGES
            + self.config.get('iso_repo_packages'))
        groups_to_download = [
            '"@{}"'.format(group) for group in iso_repo_packages_groups]
        packages_to_download = [
            '"{}"'.format(package) for package in iso_repo_packages]
        mock_yum_command = (
            "--shell 'yumdownloader --config {config_file} "
            "--installroot {install_root} "
            "--destdir {dest_dir} "
            "--releasever {distro_version} --resolve {packages}'".format(
                config_file=CHROOT_REPO_CONFIG_FILE_PATH,
                install_root=YUM_INSTALL_ROOT_DIR,
                dest_dir=CHROOT_MERGED_REPO_PATH,
                distro_version=self.config.get('distro_version'),
                packages=" ".join(groups_to_download + packages_to_download)))
        self.mock.run_command(mock_yum_command)

        LOG.debug("Merging package groups metadata files (comps.xml)")
        MERGED_GROUPS_FILE_CHROOT_PATH = "/merged-comps.xml"
        chroot_path = self.mock.run_command("--print-root-path").strip()
        cached_groups_files_glob = os.path.join(chroot_path, os.path.relpath(
            YUM_INSTALL_ROOT_DIR, "/"), "var/cache/yum/*/gen/comps.xml")
        other_groups_files = [
            "--load " + os.path.relpath(groups_file_path, chroot_path)
            for groups_file_path in glob.glob(cached_groups_files_glob)]
        merge_comps_command = (
            "yum-groups-manager --load {host_os_groups_file} {other_loads} "
            "--save {merged_groups_file} --id empty-group".format(
                host_os_groups_file=GROUPS_FILE_CHROOT_PATH,
                other_loads=" ".join(other_groups_files),
                merged_groups_file=MERGED_GROUPS_FILE_CHROOT_PATH))
        self.mock.run_command("--shell '%s'" % merge_comps_command)

        LOG.debug("Creating yum repository")
        create_repo_command = (
            "--shell 'createrepo --verbose --groupfile {groups_file} "
            "{repo_path}'".format(groups_file=MERGED_GROUPS_FILE_CHROOT_PATH,
                                  repo_path=CHROOT_MERGED_REPO_PATH))
        self.mock.run_command(create_repo_command)

        LOG.info("Checking if created repository has any unresolvable dependencies")
        mock_iso_repo_url = "file://%s/" % CHROOT_MERGED_REPO_PATH
        merged_repo_config = yum_repository.YUM_MAIN_CONFIG
        merged_repo_config += yum_repository.create_repository_config(
            "merged-local-repo", "OpenPOWER Host OS merged local repository",
            mock_iso_repo_url)
        merged_repo_config_file_path = os.path.join(
            self.work_dir, os.path.basename(CHROOT_MERGED_REPO_CONFIG_FILE_PATH))
        with open(merged_repo_config_file_path, 'w') as merged_repo_config_file:
            merged_repo_config_file.write(merged_repo_config)
        self.mock.run_command("--copyin %s %s" % (
            merged_repo_config_file_path, CHROOT_MERGED_REPO_CONFIG_FILE_PATH))
        merged_repo_closure_command = (
            "--chroot 'repoclosure --config {config_file} "
            "--tempcache'".format(
                config_file=CHROOT_MERGED_REPO_CONFIG_FILE_PATH))
        self.mock.run_command(merged_repo_closure_command)

    def _create_iso_kickstart(self):
        kickstart_file = self.config.get('automated_install_file')
        kickstart_path = os.path.join(self.work_dir, kickstart_file)
        LOG.info("Creating ISO kickstart file %s" % kickstart_path)

        mock_iso_repo_name = self.config.get('mock_iso_repo_name')
        iso_repo_packages_groups = (
            ISO_REPO_MINIMAL_PACKAGES_GROUPS
            + self.config.get('iso_repo_packages_groups'))
        iso_repo_packages = (
            ISO_REPO_MINIMAL_PACKAGES
            + self.config.get('iso_repo_packages'))

        with open(kickstart_path, "wt") as kickstart_file:
            mock_iso_repo_url = "file://%s/" % CHROOT_MERGED_REPO_PATH
            repo = "repo --name=%s --baseurl=%s\n" % (
                mock_iso_repo_name, mock_iso_repo_url)
            kickstart_file.write(repo)
            kickstart_file.write("%packages\n")
            for group in iso_repo_packages_groups:
                kickstart_file.write("@{}\n".format(group))
            for package in iso_repo_packages:
                kickstart_file.write("{}\n".format(package))
            kickstart_file.write("%end\n")

        self.mock.run_command("--copyin %s /" % kickstart_path)
        shutil.copy(kickstart_path, self.result_dir)

    def _build(self):
        build_iso_args = ""

        if self.build_iso:
            build_iso_args = "-I"
            LOG.info("Building ISO")

        build_cmd = ("%s %s -c %s --name %s --ver %s -G -C -B %s" %
                    (self.pungi_binary, self.pungi_args,
                     self.config.get('automated_install_file'),
                     self.distro, self.version, build_iso_args))
        self.mock.run_command("--shell '%s'" % build_cmd)

    def _save(self):
        latest_dir = os.path.join(os.path.dirname(self.result_dir),
                                  LATEST_SYMLINK_NAME)
        utils.force_symlink(self.timestamp, latest_dir)

        iso_dir = "/%s/%s/iso" % (self.version, self.arch)
        iso_files = "%s/*" % iso_dir

        if self.build_iso:
            LOG.info("Saving ISO files %s at %s" % (iso_files, self.result_dir))
            self.mock.run_command("--copyout %s %s" %
                                  (iso_files, self.result_dir))

        tree_src_dir = "/%s/%s/os" % (self.version, self.arch)
        tree_dest_dir = os.path.join(self.result_dir, "os")

        if self.build_install_tree:
            LOG.info("Saving installable tree %s at %s" %
                     (tree_src_dir, tree_dest_dir))
            self.mock.run_command("--copyout %s %s" %
                                  (tree_src_dir, tree_dest_dir))

    def clean(self):
        self.mock.run_command("--clean")
