from nose.tools import eq_
from nose_parameterized import parameterized


from lib.config import ConfigParser


import unittest


class TestConfigParser(unittest.TestCase):

    @parameterized.expand([
        (['--config-file=foo', 'build-packages'], 'config_file', 'foo'),
        (['--log-file=foo', 'build-packages'], 'log_file', 'foo'),
        (['--verbose', 'build-packages'], 'verbose', True),
        (['build-packages', '--packages=foo'], 'packages', ['foo']),
        (['build-packages', '--result-dir=foo'], 'result_dir', 'foo'),
        (['build-packages', '--packages-repos-target-path=foo'], 'packages_repos_target_path', 'foo'),
        (['build-packages', '--keep-build-dir'], 'keep_build_dir', True),
        (['build-packages', '--packages-metadata-repo-url=foo'], 'packages_metadata_repo_url', 'foo'),
        (['build-packages', '--packages-metadata-repo-branch=foo'], 'packages_metadata_repo_branch', 'foo'),
        (['build-packages', '--mock-args=foo'], 'mock_args', 'foo'),
        (['build-release-notes', '--push-repo-url=foo'], 'push_repo_url', 'foo'),
        (['build-release-notes', '--push-repo-branch=foo'], 'push_repo_branch', 'foo'),
        (['build-release-notes', '--updater-name=foo'], 'updater_name', 'foo'),
        (['build-release-notes', '--updater-email=foo'], 'updater_email', 'foo'),
        (['set-env', '--user=foo'], 'user', 'foo'),
        (['build-iso', '--packages-dir=foo'], 'packages_dir', 'foo'),
        (['build-iso', '--mock-args=foo'], 'mock_args', 'foo'),
        (['update-versions', '--no-commit-updates'], 'commit_updates', False),
        (['update-versions', '--no-push-updates'], 'push_updates', False),
    ])
    def test_parse_arguments_list_WithLongArgument_ShouldParseArgumentValue(self, arguments, key, expected):
        cfg = ConfigParser()

        result_dict = cfg.parse_command_line_arguments(arguments)
        value = result_dict.get(key)

        eq_(value, expected)

    @parameterized.expand([
        (['build-packages'], False, 'log_file', '/var/log/host-os/builds.log'),
        (['build-packages'], False, 'verbose', False),
        (['build-packages'], True, 'keep_build_dir', False),
        (['build-packages'], True, 'packages', None),
        (['build-packages'], True, 'result_dir', './result'),
        (['build-packages'], True, 'packages_repos_target_path', '/var/lib/host-os/repositories'),
        (['build-packages'], True, 'packages_metadata_repo_url', None),
        (['build-packages'], True, 'packages_metadata_repo_branch', None),
        (['build-packages'], True, 'mock_args', '--enable-plugin=tmpfs --plugin-option=tmpfs:keep_mounted=True --plugin-option=tmpfs:max_fs_size=32g --plugin-option=tmpfs:required_ram_mb=39800'),
        (['build-release-notes'], True, 'push_repo_url', None),
        (['build-release-notes'], True, 'push_repo_branch', 'master'),
        (['build-release-notes'], False, 'updater_name', None),
        (['build-release-notes'], False, 'updater_email', None),
        (['build-iso'], True, 'packages_dir', './result'),
        (['build-iso'], True, 'mock_args', None),
        (['update-versions'], False, 'commit_updates', True),
        (['update-versions'], False, 'push_updates', True),
    ])
    def test_parse_arguments_list_WithoutArgument_ShouldUseDefaultValue(self, arguments, dest_node_eq_subcommand, key, expected):
        cfg = ConfigParser()

        result_dict = cfg.parse(arguments)
        if dest_node_eq_subcommand:
            node_name = arguments[0].replace("-", "_")
        else:
            node_name = "common"
        value = result_dict[node_name].get(key)

        eq_(value, expected)
