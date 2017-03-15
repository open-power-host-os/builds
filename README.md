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
git clone https://github.com/open-power-host-os/builds.git
cd builds
```

### RPM Based distributions

* Install epel repository (Extra Packages for Enterprise Linux):

```
sudo yum install epel-release
```

* Install RPM dependencies

```
sudo yum install -y $(cat rpm_requirements.txt)
```

## Settings

* Add user to mock group

```
sudo usermod -a -G mock $(whoami)
```

## Running

* Build a single or multiple packages

```
./host_os.py build-packages --packages kernel libvirt
```

* Build all software

```
./host_os.py --verbose build-packages
```

Note the `--verbose` parameter to get all the log messages in the
console. Instead of the standard ordinary messages. Please see
`--help` for more options.

```
./host_os.py --help
```

or

```
./host_os.py build-packages --help
```

* Build old versions

For details on building OpenPOWER Host OS old versions, refer to the documentation at https://github.com/open-power-host-os/builds/blob/master/BUILD_OLD_VERSIONS.md.

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
sudo yum -c result/repository_config/latest install open-power-host-os-virt
```

It will then install all required dependencies:

 - kernel
 - libvirt
 - qemu
 - SLOF

You can use similar commands to install specific packages, for instance,
kernel's debuginfo RPM:

```
sudo yum -c result/repository_config/latest install kernel-debuginfo
```

When using virtualization packages, SMT needs to be disabled:

```
sudo ppc64_cpu --smt=off
```

## Contact us

If you are interested, you might always stop by in `#hostos` on irc.freenode.net.
