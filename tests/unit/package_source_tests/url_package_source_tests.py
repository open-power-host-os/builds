from lib.package_source import UrlPackageSource


from nose.tools import assert_raises, eq_


def test_newInstance_withCompleteSourceOptions_shouldReturnValidObject():
    data = {'url': {'src': 'foo', 'dest': 'bar'}}

    result = UrlPackageSource(data)

    eq_(result.src, data['url']['src'])
    eq_(result.dest, data['url']['dest'])


def test_newInstance_withoutUrlOptionsField_shouldRaiseValueError():
    data = {'foo': {'dest': 'bar'}}

    with assert_raises(ValueError) as e:
        UrlPackageSource(data)

    exception_message = e.exception.message

    assert('missing URL options' in exception_message)


def test_newInstance_withSourceOptionsMissingSrcDest_shouldRaiseValueError():
    data = {'url': {'dest': 'bar'}}

    with assert_raises(ValueError) as e:
        UrlPackageSource(data)

    exception_message = e.exception.message

    assert('missing src field in URL options' in exception_message)


def test_newInstance_withSourceOptionsMissingDestField_shouldRaiseValueError():
    data = {'url': {'src': 'bar'}}

    with assert_raises(ValueError) as e:
        UrlPackageSource(data)

    exception_message = e.exception.message

    assert('missing dest field in URL options' in exception_message)
