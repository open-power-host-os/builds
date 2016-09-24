Build the best of OpenPOWER platform virtualization
***************************************************

Considering the speed of the development of new features, or even Hardware is
created in the OpenPOWER ecosystem, it's a challenge to get them in the
traditional stable GNU/Linux distribution scenario.

open-power-host-os/builds repository is an open source collaboration effort that
aims to help administrators to build and deploy the latest and greatest
capabilities in the OpenPOWER world through a build script that provides
software well packaged and designed for the `Supported GNU/Linux distributions`_

Supported GNU/Linux distributions
---------------------------------

* CentOS 7.2 PPC64LE

Installation
------------

RPM Based distributions
^^^^^^^^^^^^^^^^^^^^^^^
* Install epel repository (Extra Packages for Enterprise Linux):

::

$ sudo yum install --downloadonly --downloaddir=. epel-release
$ sudo yum localinstall epel-release-7-5.noarch.rpm # Note the version may change.

* Install

 - bzip2
 - git
 - mock
 - python-pygit2
 - PyYAML
 - svn
 - wget

::

$ sudo yum install -y bzip2 git mock pyton-pygit2 PyYAML svn wget

Settings
--------

* Disable SMT

::

$ sudo ppc64_cpu --smt=off

* Setup environment and user

::

$ sudo python setup_environment.py LOGIN

Naturally, you need to replace ``LOGIN`` by the user name you'll use to run
``host-os-build.py``, which should not run using root user, even if that user
doesn't exist yet.

Running
-------

* Build a single package

::

$ python host-os-build.py --package libvirt

* Build all software

::

$ python host-os-build.py --verbose

Note the ``--verbose`` parameter to get all the log messages in the console. Instead
of the standard ordinary messages. Please see ``--help`` for more options.

::

$ python host-os-build.py --help


Using the RPMs
--------------
We decided that's is a little bit intrusive to install all the produced RPMs
since some of them may not fit your needs. At the end of the process
you'll see a new ``result`` directory inside this project's root.

A suggested set of packages tested is the following:
 - kernel
 - libseccomp
 - libvirt
 - libvirt-client
 - libvirt-daemon
 - libvirt-daemon-config-network
 - libvirt-daemon-config-nwfilter
 - libvirt-daemon-driver-interface
 - libvirt-daemon-driver-lxc
 - libvirt-daemon-driver-network
 - libvirt-daemon-driver-nodedev
 - libvirt-daemon-driver-nwfilter
 - libvirt-daemon-driver-qemu
 - libvirt-daemon-driver-secret
 - libvirt-daemon-driver-storage
 - libvirt-daemon-kvm
 - libvirt-daemon-lxc
 - libvirt-daemon-qemu
 - libvirt-debuginfo
 - libvirt-devel
 - libvirt-docs
 - libvirt-lock-sanlock
 - libvirt-login-shell
 - libvirt-nss
 - qemu
 - qemu-common
 - qemu-debuginfo
 - qemu-guest-agent
 - qemu-img
 - qemu-kvm
 - qemu-kvm-tools
 - qemu-system-ppc
 - qemu-system-x86
 - SLOF

You can use the following command to install, for instance, libseccomp's RPM:

::

$ sudo yum localinstall result/libseccomp-2.3.1-0.el7.centos.1.ppc64le.rpm

Note that some of those packages are debuginfo which are recommended in order to
provide useful information for bugs in the case of any failures.

Also no version is informed on the list above to make it valid even for future
versions with minor version changes.

Validating
----------

There is a whole repository dedicated to testing available at
https://github.com/open-power-host-os/tests
