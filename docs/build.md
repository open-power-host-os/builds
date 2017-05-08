* Build custom software

The build code keeps a cache of all packages source code (Git/Mercurial/SVN)
repositories so that they do not need to be downloaded on every build. If it is
desired to change the source code of a package, you may edit the package local
repository content. To build the package from this modified local repository,
either use a file:// URL pointing to it in the package metadata (YAML)
file or disable package repositories update in config/host_os.yaml.
