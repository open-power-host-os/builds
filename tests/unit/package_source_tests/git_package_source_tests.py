from lib.package_source import GitPackageSource


from nose.tools import assert_raises, eq_


def test_newInstance_withValidDict_shouldReturnValidInstance():
    data = {'url': 'foo', 'branch': 'abc', 'commit_id': 'c0ff33'}

    result = GitPackageSource(data)

    eq_(result.url, data['url'])
    eq_(result.branch, data['branch'])
    eq_(result.commit_id, data['commit_id'])


def test_newInstance_withDictMissingUrlField_shouldRaiseValueError():
    data = {'branch': 'abc', 'commit_id': 'c0ff33'}

    with assert_raises(ValueError) as e:
        GitPackageSource(data)

    exception_message = e.exception.message

    assert('missing url field' in exception_message)


def test_newInstance_withDictMissingBranchField_shouldRaiseValueError():
    data = {'url': 'abc', 'commit_id': 'c0ff33'}

    with assert_raises(ValueError) as e:
        GitPackageSource(data)

    exception_message = e.exception.message

    assert('missing branch field' in exception_message)


def test_newInstance_withDictMissingCommitIDField_shouldRaiseValueError():
    data = {'url': 'abc', 'branch': 'c0ff33'}

    with assert_raises(ValueError) as e:
        GitPackageSource(data)

    exception_message = e.exception.message

    assert('missing commit_id field' in exception_message)
