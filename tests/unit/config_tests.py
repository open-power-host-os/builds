from nose.tools import eq_
from nose_parameterized import parameterized


from lib.config import ConfigParser


import unittest


class TestConfigParser(unittest.TestCase):

    @parameterized.expand([
        ('--config-file=foo', 'config_file', 'foo'),
        ('--packages=foo', 'packages', ['foo']),
        ('--log-file=foo', 'log_file', 'foo'),
        ('--verbose', 'verbose', True),
        ('--result-dir=foo', 'result_dir', 'foo'),
        ('--repositories-path=foo', 'repositories_path', 'foo'),
        ('--keep-builddir', 'keep_builddir', True),
        ('--build-versions-repository-url=foo', 'build_versions_repository_url', 'foo'),
        ('--build-version=foo', 'build_version', 'foo'),
        ('--mock-args=foo', 'mock_args', 'foo'),
    ])
    def test_parse_arguments_list_WithLongArgument_ShouldParseArgumentValue(self, argument, key, expected):
        cfg = ConfigParser()

        result_dict = cfg.parse_arguments_list([argument])
        value = result_dict.get(key)

        eq_(value, expected)

    @parameterized.expand([
        ('config_file', './config.yaml'),
        ('packages', None),
        ('log_file', '/var/log/host-os/builds.log'),
        ('verbose', False),
        ('result_dir', './result'),
        ('repositories_path', '/var/lib/host-os/repositories'),
        ('keep_builddir', False),
        ('build_versions_repository_url', None),
        ('build_version', None),
        ('mock_args', ''),
    ])
    def test_parse_arguments_list_WithoutArgument_ShouldUseDefaultValue(self, key, expected):
        cfg = ConfigParser()

        result_dict = cfg.parse_arguments_list([])
        value = result_dict.get(key)

        eq_(value, expected)
