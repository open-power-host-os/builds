from lib import config
from lib import repository


class GitPackageSource(object):
    def __init__(self, source, dest, package_name):
        self._validate_source_fields(source)
        self.package_name = package_name
        self.url = source['url']
        self.branch = source['branch']
        self.commit_id = source['commit_id']
        self.repo = None

    def _validate_source_fields(self, source):
        if 'url' not in source:
            raise ValueError('missing url field')

        if 'branch' not in source and 'commit_id' not in source:
            raise ValueError('missing branch and commit_id field. '
                             'You must provide at least one.')

    def download(self):
        self.repo = repository.get_git_repository(
            self._package_name,
            self.url,
            dest=CONF.get('default').get('repositories_path'),
            branch=self.branch
        )
        self.repo.checkout(self.commit_id or self.branch)
