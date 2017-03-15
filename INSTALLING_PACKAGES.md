# Repository installation

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
