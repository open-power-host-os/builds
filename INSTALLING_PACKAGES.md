# Installation using yum repository

To install Host OS packages from a repository, you'll first need a
system with a
[supported GNU/Linux distribution](README.md#supported-gnulinux-distributions)
and a yum configuration file pointing to an accessible yum repository
containing the Host OS packages.

If you've just executed the build script and want to use the local yum
repository containing the built packages, your yum configuration file
will be available at `result/repository_config/latest`. Otherwise, you'll
need one pointing to the remote yum repository.

It is a good idea to clean the yum cache to make sure you're getting the
latest packages from the repositories:

```
sudo yum -c <path_to_yum_repository_config> clean all
```

Decide which packages or groups of packages you want to install. To
install a single package, for example `kernel-debuginfo`, you can execute:

```
sudo yum -c <path_to_yum_repository_config> install kernel-debuginfo
```

Yum will take care of the dependencies.

If you want to install a group of packages, we have several that may be of
interest, described [here](https://github.com/olavphibm/versions/blob/master/README.md#packages-groups).
To install only virtualization related packages, choose the
`open-power-host-os-virt` metapackage:

```
sudo yum -c result/repository_config/latest install open-power-host-os-virt
```

When using virtualization packages in POWER systems, SMT needs to be disabled:

```
sudo ppc64_cpu --smt=off
```

If you want to install all of Host OS packages, execute:

```
sudo yum -c <path_to_yum_repository_config> install open-power-host-os-all
```

# Installation using ISO file

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

- During installation, on "Software selection" option, you should see the
following options:

```
 1)  [ ] Minimal Install                 6)  [ ] Openpower Host Os Container
 2)  [ ] Infrastructure Server           7)  [ ] Openpower Host Os Ras
 3)  [ ] Virtualization Host             8)  [ ] Openpower Host Os
 4)  [ ] Openpower Host Os All                   Virtualization
 5)  [ ] Openpower Host Os Base          9)  [ ] Openpower Host Os
                                                 Virtualization Management
```

The first three ones are same that are present on a stardard CentOS installation,
with the difference that they will install the most updated versions of packages
present, substituting CentOS kernel for Host OS one, for example.

We recommend the installation of any of the OpenPOWER Host OS options, depending
on your needs. For the complete Host OS, select "Openpower Host Os All". The
specific packages belonging to each group can be found [here](https://github.com/olavphibm/versions/blob/master/README.md#packages-groups).
