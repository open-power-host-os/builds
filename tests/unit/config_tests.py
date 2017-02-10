from nose.tools import eq_
from nose_parameterized import parameterized


from lib.config import ConfigParser


import unittest


class TestConfigParser(unittest.TestCase):

    @parameterized.expand([
        (['--config-file=foo', 'build-package'], 'config_file', 'foo'),
        (['--log-file=foo', 'build-package'], 'log_file', 'foo'),
        (['--verbose', 'build-package'], 'verbose', True),
        (['build-package', '--packages=foo'], 'packages', ['foo']),
        (['build-package', '--result-dir=foo'], 'result_dir', 'foo'),
        (['build-package', '--repositories-path=foo'], 'repositories_path', 'foo'),
        (['build-package', '--keep-builddir'], 'keep_builddir', True),
        (['build-package', '--build-versions-repository-url=foo'], 'build_versions_repository_url', 'foo'),
        (['build-package', '--build-version=foo'], 'build_version', 'foo'),
        (['build-package', '--mock-args=foo'], 'mock_args', 'foo'),
        (['release-notes', '--push-repo-url=foo'], 'push_repo_url', 'foo'),
        (['release-notes', '--push-repo-branch=foo'], 'push_repo_branch', 'foo'),
        (['release-notes', '--updater-name=foo'], 'updater_name', 'foo'),
        (['release-notes', '--updater-email=foo'], 'updater_email', 'foo'),
        (['set-env', '--user=foo'], 'user', 'foo'),
        (['build-iso', '--packages-dir=foo'], 'packages_dir', 'foo'),
        (['build-iso', '--mock-args=foo'], 'mock_args', 'foo'),
        (['upgrade-versions', '--no-commit-updates'], 'commit_updates', False),
        (['upgrade-versions', '--no-push-updates'], 'push_updates', False),
    ])
    def test_parse_arguments_list_WithLongArgument_ShouldParseArgumentValue(self, arguments, key, expected):
        cfg = ConfigParser()

        result_dict = cfg.parse_arguments_list(arguments)
        value = result_dict.get(key)

        eq_(value, expected)

    @parameterized.expand([
        (['build-package'], 'config_file', './config.yaml'),
        (['build-package'], 'log_file', '/var/log/host-os/builds.log'),
        (['build-package'], 'verbose', False),
        (['build-package'], 'keep_builddir', False),
        (['build-package'], 'packages', None),
        (['build-package'], 'result_dir', './result'),
        (['build-package'], 'repositories_path', '/var/lib/host-os/repositories'),
        (['build-package'], 'build_versions_repository_url', None),
        (['build-package'], 'build_version', None),
        (['build-package'], 'mock_args', ''),
        (['release-notes'], 'push_repo_url', None),
        (['release-notes'], 'push_repo_branch', 'master'),
        (['release-notes'], 'updater_name', None),
        (['release-notes'], 'updater_email', None),
        (['build-iso'], 'packages_dir', './result'),
        (['build-iso'], 'mock_args', ''),
        (['upgrade-versions'], 'commit_updates', True),
        (['upgrade-versions'], 'push_updates', True),
    ])
    def test_parse_arguments_list_WithoutArgument_ShouldUseDefaultValue(self, arguments, key, expected):
        cfg = ConfigParser()

        result_dict = cfg.parse_arguments_list(arguments)
        value = result_dict.get(key)

        eq_(value, expected)
