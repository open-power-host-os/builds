from nose.tools import eq_
from nose_parameterized import parameterized


from lib.config import ConfigParser


import unittest


class TestConfigParser(unittest.TestCase):

    @parameterized.expand([
        (['--verbose', 'build-packages'], 'verbose', True),
        (['--work-dir=foo', 'build-packages'], 'work_dir', 'foo'),
        (['build-packages', '--packages=foo'], 'packages', ['foo']),
        (['build-packages', '--result-dir=foo'], 'result_dir', 'foo'),
        (['build-packages', '--keep-build-dir'], 'keep_build_dir', True),
        (['build-packages', '--packages-metadata-repo-url=foo'], 'packages_metadata_repo_url', 'foo'),
        (['build-packages', '--packages-metadata-repo-branch=foo'], 'packages_metadata_repo_branch', 'foo'),
        (['build-packages', '--mock-args=foo'], 'mock_args', 'foo'),
        (['build-packages', '--rpm-macros', '{"macro1":"value1", "macro2":"value2"}'], 'rpm_macros',
         {"macro1":"value1","macro2":"value2"}),
        (['build-release-notes', '--push-repo-url=foo'], 'push_repo_url', 'foo'),
        (['build-release-notes', '--push-repo-branch=foo'], 'push_repo_branch', 'foo'),
        (['build-release-notes', '--updater-name=foo'], 'updater_name', 'foo'),
        (['build-release-notes', '--updater-email=foo'], 'updater_email', 'foo'),
        (['build-images', '--packages-dir=foo'], 'packages_dir', 'foo'),
        (['build-images', '--mock-args=foo'], 'mock_args', 'foo'),
        (['build-images', '--distro-repos', '{"a":1,"b":2}', '{"a":{"b":2}}'], 'distro_repos',
         [{"a":1,"b":2}, {"a":{"b":2}}]),
        (['build-images', '--installable-environments', '{"env1": ["group1", "group2"]}'], 'installable_environments',
         {"env1":["group1","group2"]}),
        (['update-versions', '--no-commit-updates'], 'commit_updates', False),
        (['update-versions', '--no-push-updates'], 'push_updates', False),
    ])
    def test_parse_arguments_list_WithLongArgument_ShouldParseArgumentValue(self, arguments, key, expected):
        cfg = ConfigParser()

        result_dict = cfg.parse(arguments)
        value = result_dict.get(key)

        eq_(value, expected)

    @parameterized.expand([
        (['build-packages'], 'config_file', 'config/host_os.yaml'),
        (['build-packages'], 'verbose', False),
        (['build-packages'], 'work_dir', 'workspace'),
        (['build-packages'], 'keep_build_dir', False),
        (['build-packages'], 'packages', []),
        (['build-packages'], 'result_dir', 'result'),
        (['build-packages'], 'packages_metadata_repo_url',
         'https://github.com/open-power-host-os/versions.git'),
        (['build-packages'], 'packages_metadata_repo_branch', 'master'),
        (['build-packages'], 'mock_args', '--enable-plugin=tmpfs '
         '--plugin-option=tmpfs:keep_mounted=True --plugin-option='
         'tmpfs:max_fs_size=32g --plugin-option=tmpfs:required_ram_mb=39800 '
         '--verbose'),
        (['build-packages'], 'rpm_macros', {}),
        (['build-release-notes'], 'push_repo_url', ''),
        (['build-release-notes'], 'push_repo_branch', 'master'),
        (['build-release-notes'], 'updater_name', ''),
        (['build-release-notes'], 'updater_email', ''),
        (['build-images'], 'packages_dir', 'result/packages/latest'),
        (['build-images'], 'mock_args', '--enable-plugin=tmpfs '
         '--plugin-option=tmpfs:keep_mounted=True --plugin-option='
         'tmpfs:max_fs_size=32g --plugin-option=tmpfs:required_ram_mb=39800 '
         '--verbose'),
        (['update-versions'], 'commit_updates', True),
        (['update-versions'], 'push_updates', True),
    ])
    def test_parse_arguments_list_WithoutArgument_ShouldUseDefaultValue(self, arguments, key, expected):
        cfg = ConfigParser()

        result_dict = cfg.parse(arguments)
        value = result_dict.get(key)

        eq_(value, expected)
