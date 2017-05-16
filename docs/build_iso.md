# Building an ISO file

To build an OpenPOWER Host OS ISO file, you'll first need to follow the
instructions [here](README) to have a set of packages available.

If you wish an installable ISO with all the built packages and all packages
groups available during the installation, just execute:

```
./host_os.py --verbose build-iso
```

This assumes the packages are at their default location at
`result/repository_config/latest`. The created ISO will be available in the
result directory, and may be installed using those
[instructions](install_packages.md#installation-using-iso-file).

See `--help` for more options.

```
./host_os.py build-iso --help
```


## Creating custom installable environments

To create and add packages to installable environments, modify the
`installable_environments` option in the configuration. Each entry is an
environment name that will show during installation in the "Software selection"
screen and each item listed inside is a package that will be installed by that
environment.


## Building a reduced ISO file

To build a reduced ISO file, list the groups you wish available in the ISO in
the `iso_repo_packages_groups` option. If there are groups set by
`installable_environments` option that are not available in the ISO, they
will not show up during the installation.
