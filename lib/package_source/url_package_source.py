import urllib2


class UrlPackageSource(object):
    def __init__(self, source):
        self._validate_source_values(source)
        self._src = source['url']['src']
        self._dest = source['url']['dest']

    def _validate_source_values(self, source):
        if 'url' not in source:
            raise ValueError('missing URL options')

        url_options = source.get('url')
        if 'src' not in url_options:
            raise ValueError('missing src field in URL options')
        if 'dest' not in url_options:
            raise ValueError('missing dest field in URL options')

    @property
    def src(self):
        return self._src

    @property
    def dest(self):
        return self._dest

    def download(self):
        src = urllib2.urlopen(self.url)

        # Download file chunk by chunk. Reading the entire file to memory, and
        # then writing it to disk, might be a problem if the file is too large.
        CHUNK_SIZE = 2 << 14

        with open(self.dest, 'w') as dest:
            while True:
                data = src.read(CHUNK_SIZE)
                if not data:
                    break
                dest.write(data)
