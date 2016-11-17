from lib.package_source import GitPackageSource
from lib.package_source import UrlPackageSource

class PackageSourceFactory():
    def __init__(self):
        self.source_map = { 'git': GitPackageSource,
                            'url': UrlPackageSource }

    def __call__(self, source):
        source_name = source.keys()[0]
        data = source[source_name]
        return self.source_map[source_name](data)
