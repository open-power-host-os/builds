# Repository installation

To install Host OS packages from a repository, you'll first need a
system with a
[supported GNU/Linux distribution](README.md#supported-gnulinux-distributions)
and a yum configuration file pointing to an accessible yum repository
containing the Host OS packages.

If you've just executed the build scripts and want to use the local
repository, your yum configuration file will be available at
`result/repository_config/latest`. Otherwise, you'll need one pointing
to the remote yum repository.

It is a good idea to clean the yum cache to make sure you're getting the
latest packages from the repositories:

```
sudo yum -c <path_to_yum_repository_config> clean all
```

Decide which packages or groups of packages you want to install. To
install only virtualization related packages, for example, you can
install the `open-power-host-os-virt` metapackage:

```
sudo yum -c result/repository_config/latest install open-power-host-os-virt
```

It will then install all required dependencies:

 - kernel
 - libvirt
 - qemu
 - SLOF

When using virtualization packages, SMT needs to be disabled:

```
sudo ppc64_cpu --smt=off
```

If you want to install all of Host OS packages, execute:

```
sudo yum -c <path_to_yum_repository_config> install open-power-host-os-all
```

You can use similar commands to install specific packages, for instance,
kernel's debuginfo RPM:

```
sudo yum -c <path_to_yum_repository_config> install kernel-debuginfo
```

# ISO installation

If you want to install Host OS on a clean system, you may use the
Host OS ISO to avoid installing CentOS first. One way to do this is
booting from an HTTP server:

- Mount the ISO on an HTTP server:

```
sudo mount -o loop <path_to_iso_file> <path_to_mounted_iso>
```

- Configure a Petitboot entry:

```
kernel http://<server_url>/<path_to_mounted_iso>/ppc/ppc64/vmlinuz
initrd http://<server_url>/<path_to_mounted_iso>/ppc/ppc64/initrd.img
append root=live:http://<server_url>/<path_to_mounted_iso>/LiveOS/squashfs.img repo=http://<server_url>/<path_to_mounted_iso>
```

- Log into target system and boot using netboot entry.

- During installation, on "Software selection" option, you can choose between:

  - "Minimal Install": CentOS core package group + **Host OS kernel**
  - "Infrastructure Server": CentOS core and base package groups + **Host OS kernel**
  - "Virtualization Host": CentOS core, base and virtualization-tools package groups + **Host OS virtualization stack** (SLOF, docker, ginger, ginger-base, golang, kernel, kimchi, libvirt, libvirt-daemon-kvm, libvirt-daemon-lxc, libvirt-daemon-qemu, libvirt-devel, libvirt-docs, libvirt-lock-sanlock, libvirt-login-shell, libvirt-nss, libvpd, lsvpd, novnc, ppc64-diag, qemu, qemu-guest-agent, qemu-kvm-tools, servicelog, sos, systemtap, wok)
