# Build the best of OpenPOWER platform virtualization

Considering the speed of the development of new features, or even
Hardware is created in the OpenPOWER ecosystem, it's a challenge to
get them in the traditional stable GNU/Linux distribution scenario.

open-power-host-os/builds repository is an open source collaboration
effort that aims to help administrators to build and deploy the latest
and greatest capabilities in the OpenPOWER world through a build
script that provides software well packaged and designed for the
[Supported GNU/Linux distributions](#supported-gnulinux-distributions).

## Supported GNU/Linux distributions

* CentOS 7.3 PPC64LE


Refer to [30. How does CentOS versioning work?](https://wiki.centos.org/FAQ/General#head-dcca41e9a3d5ac4c6d900a991990fd11930867d6).

## Installation

* Clone the repository

```
$ git clone https://github.com/open-power-host-os/builds.git
$ cd builds
```

### RPM Based distributions

* Install epel repository (Extra Packages for Enterprise Linux):

```
$ sudo yum install epel-release
```

* Install RPM dependencies

```
$ sudo yum install -y $(cat rpm_requirements.txt)
```

## Settings

* Add user to mock group

```
$ sudo usermod -a -G mock $(whoami)
```

## Running

* Build a single or multiple packages

```
$ ./host_os.py build-packages --packages kernel libvirt
```

* Build all software

```
$ ./host_os.py --verbose build-packages
```

Note the `--verbose` parameter to get all the log messages in the
console. Instead of the standard ordinary messages. Please see
`--help` for more options.

```
$ ./host_os.py --help
```

or

```
$ ./host_os.py build-packages --help
```

* Build old versions

OpenPOWER Host OS 1.0 and 1.5 used an older CentOS (7.2) as base version.
To build one of them, do the following changes in this git repository
before building:

Update yum repository to CentOS 7.2:

```
$ sed -i 's|http://mirror.centos.org/altarch/|http://vault.centos.org/altarch/7.2.1511/|' mock_configs/CentOS/7/CentOS-7-ppc64le.cfg
```

Update distro version to 7.2:

```
$ sed -i "s|distro_version:.*|distro_version: \"7.2\"|" config.yaml
$ sed -i -E "s|  '7': (\"\./mock_configs.*)|  '7.2': \1|" config.yaml
```

Update build version to v1.5.0 or v1.0.0:

```
$ sed -i "s|build_version:.*|build_version: \"v1.5.0\"|" config.yaml  # use v1.5.0 or v1.0.0
```

Install rpm packages which were used in older build code, but are not anymore:

```
$ yum install -y bzip2 wget
```

Clean yum repositories cache in mock:

```
$ mock --scrub all
```

These steps are documented in
https://github.com/open-power-host-os/infrastructure/tree/master/jenkins_jobs/build_old_host_os_versions/script.sh .

* Build custom software

The build code keeps a cache of all packages source code (Git/Mercurial/SVN)
repositories so that they do not need to be downloaded on every build. If it is
desired to change the source code of a package, you may edit the package local
repository content. To build the package from this modified local repository,
either use a file:// URL pointing to it in the package metadata (YAML)
file or disable package repositories update in config.yaml.


## Using the RPMs

At the end of the process you'll see a new ``result`` directory inside
this project's root. It contains the built packages repositories under
``packages`` and a yum repository config under ``repository_config``, to
simplify using those repositories.

To install only virtualization related packages, for example, you can
install the open-power-host-os-virt metapackage:

```
$ sudo yum -c result/repository_config/latest install open-power-host-os-virt
```

It will then install all required dependencies:

 - kernel
 - libvirt
 - qemu
 - SLOF

You can use similar commands to install specific packages, for instance,
kernel's debuginfo RPM:

```
$ sudo yum -c result/repository_config/latest install kernel-debuginfo
```

When using virtualization packages, SMT needs to be disabled:

```
$ sudo ppc64_cpu --smt=off
```

## Contact us

If you are interested, you might always stop by in `#hostos` on irc.freenode.net.
