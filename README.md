# Build scripts for OpenPOWER Host OS

This repository aims to help administrators to build and deploy the latest
and greatest capabilities in the OpenPOWER world through a build
script that provides software well packaged and designed for the
[Supported GNU/Linux distributions](#supported-gnulinux-distributions).

For more information about Host OS check: https://open-power-host-os.github.io/

## Supported GNU/Linux distributions

* CentOS 7.3 PPC64LE


Refer to [30. How does CentOS versioning work?](https://wiki.centos.org/FAQ/General#head-dcca41e9a3d5ac4c6d900a991990fd11930867d6).

## Quick start

* Clone the repository

  ```
  git clone https://github.com/open-power-host-os/builds.git
  cd builds
  ```

* Install dependencies

  ```
  sudo yum install epel-release
  sudo yum install -y $(cat rpm_requirements.txt)
  ```

* Add user to mock group

  ```
  sudo usermod -a -G mock $(whoami)
  ```

* Build packages

  To build all packages:

  ```
  ./host_os.py build-packages
  ```

  To build specific packages:

  ```
  ./host_os.py build-packages --packages kernel libvirt
  ```

* Build old versions

For details on building OpenPOWER Host OS old versions, refer to the documentation at https://github.com/open-power-host-os/builds/blob/master/docs/build_old_versions.md.

* Build custom software

The build code keeps a cache of all packages source code (Git/Mercurial/SVN)
repositories so that they do not need to be downloaded on every build. If it is
desired to change the source code of a package, you may edit the package local
repository content. To build the package from this modified local repository,
either use a file:// URL pointing to it in the package metadata (YAML)
file or disable package repositories update in config/host_os.yaml.


## Building an ISO

To build an ISO with the built packages, follow those
[instructions](docs/building_an_iso.md).


## Contact us

If you are interested, you might always stop by in `#hostos` on irc.freenode.net.
