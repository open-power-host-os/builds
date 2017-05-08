# Build scripts for OpenPOWER Host OS

This repository aims to help administrators to build and deploy the latest
and greatest capabilities in the OpenPOWER world through a build
script that provides software well packaged and designed for the
[Supported GNU/Linux distributions](#supported-gnulinux-distributions).

For more information about Host OS check: https://open-power-host-os.github.io/

* [Quick Start](#quick-start)
* [Building](docs/build.md#building-process)
  * [ISO](docs/building_an_iso.md)
  * [Custom software](docs/build.md#building-packages-with-locally-modified-sources)
  * [Stable version](docs/build.md#host-os-stable)
  * [Pre 2.0 versions](docs/build_old_versions.md)
* [Installing packages](docs/installing_packages.md)
* [Supported distributions](#supported-gnulinux-distributions)
* [Contact us](#contact-us)


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

### Supported GNU/Linux distributions

* CentOS 7.3 PPC64LE

  Refer to [30. How does CentOS versioning work?](https://wiki.centos.org/FAQ/General#head-dcca41e9a3d5ac4c6d900a991990fd11930867d6).


---
<a name="contact-us"></a>
Contact us via IRC on #hostos at irc.freenode.net
