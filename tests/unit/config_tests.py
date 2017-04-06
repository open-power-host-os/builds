from nose.tools import eq_
from nose_parameterized import parameterized


from lib.config import ConfigParser


import unittest


class TestConfigParser(unittest.TestCase):

    @parameterized.expand([
        (['--config-file=config.yaml', 'build-packages'], False, 'config_file', 'config.yaml'),
        (['--verbose', 'build-packages'], False, 'verbose', True),
        (['--work-dir=foo', 'build-packages'], False, 'work_dir', 'foo'),
        (['build-packages', '--packages=foo'], True, 'packages', ['foo']),
        (['build-packages', '--result-dir=foo'], False, 'result_dir', 'foo'),
        (['build-packages', '--keep-build-dir'], True, 'keep_build_dir', True),
        (['build-packages', '--packages-metadata-repo-url=foo'], False, 'packages_metadata_repo_url', 'foo'),
        (['build-packages', '--packages-metadata-repo-branch=foo'], False, 'packages_metadata_repo_branch', 'foo'),
        (['build-packages', '--mock-args=foo'], True, 'mock_args', 'foo'),
        (['build-release-notes', '--push-repo-url=foo'], True, 'push_repo_url', 'foo'),
        (['build-release-notes', '--push-repo-branch=foo'], True, 'push_repo_branch', 'foo'),
        (['build-release-notes', '--updater-name=foo'], False, 'updater_name', 'foo'),
        (['build-release-notes', '--updater-email=foo'], False, 'updater_email', 'foo'),
        (['build-iso', '--packages-dir=foo'], True, 'packages_dir', 'foo'),
        (['build-iso', '--mock-args=foo'], True, 'mock_args', 'foo'),
        (['update-versions', '--no-commit-updates'], False, 'commit_updates', False),
        (['update-versions', '--no-push-updates'], False, 'push_updates', False),
    ])
    def test_parse_arguments_list_WithLongArgument_ShouldParseArgumentValue(self, arguments, dest_node_eq_subcommand, key, expected):
        cfg = ConfigParser()

        result_dict = cfg.parse(arguments)
        print("result_dict: %s" % result_dict)
        if dest_node_eq_subcommand:
            node_name = arguments[0].replace("-", "_")
        else:
            node_name = "common"
        value = result_dict[node_name].get(key)

        eq_(value, expected)

    @parameterized.expand([
        (['build-packages'], False, 'config_file', './config.yaml'),
        (['build-packages'], False, 'verbose', False),
        (['build-packages'], False, 'work_dir', 'workspace'),
        (['build-packages'], True, 'keep_build_dir', False),
        (['build-packages'], True, 'packages', []),
        (['build-packages'], False, 'result_dir', 'result'),
        (['build-packages'], False, 'packages_metadata_repo_url', 'https://github.com/open-power-host-os/versions.git'),
        (['build-packages'], False, 'packages_metadata_repo_branch', 'master'),
        (['build-packages'], True, 'mock_args', '--enable-plugin=tmpfs --plugin-option=tmpfs:keep_mounted=True --plugin-option=tmpfs:max_fs_size=32g --plugin-option=tmpfs:required_ram_mb=39800'),
        (['build-release-notes'], True, 'push_repo_url', ''),
        (['build-release-notes'], True, 'push_repo_branch', 'master'),
        (['build-release-notes'], False, 'updater_name', ''),
        (['build-release-notes'], False, 'updater_email', ''),
        (['build-iso'], True, 'packages_dir', 'result/latest/packages'),
        (['build-iso'], True, 'mock_args', ''),
        (['update-versions'], False, 'commit_updates', True),
        (['update-versions'], False, 'push_updates', True),
    ])
    def test_parse_arguments_list_WithoutArgument_ShouldUseDefaultValue(self, arguments, dest_node_eq_subcommand, key, expected):
        cfg = ConfigParser()

        result_dict = cfg.parse(arguments)
        print("result dict: %s" % result_dict)
        if dest_node_eq_subcommand:
            node_name = arguments[0].replace("-", "_")
        else:
            node_name = "common"
        value = result_dict[node_name].get(key)

        eq_(value, expected)
