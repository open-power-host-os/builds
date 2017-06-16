node('master') {
  dir('infrastructure') {
    git(url: 'https://github.com/open-power-host-os/infrastructure.git',
        branch: 'master')
  }
  pipeline = load 'infrastructure/pipeline/build.groovy'
}

pipeline.execute()
