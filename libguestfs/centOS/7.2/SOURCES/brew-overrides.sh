#!/bin/bash -

# This script is used when we build libguestfs from brew, as sometimes
# we require packages which are not available in the current version
# of RHEL.  Normally these updated packages would be released along
# with libguestfs in the next RHEL, although unfortunately sometimes
# that doesn't happen (eg. RHBZ#1199605).

set -x

# See also:
# $ brew list-tag-inheritance --reverse rhel-7.2
# rhel-7.2 (7602)
#   ├─rhel-7.2-temp-override (7606)
#   │  └─rhel-7.2-override (7607)
#   │     └─rhel-7.2-build (7608)
#   │        ├─rhel-7.2-pesign-build (7609)
#   │        ├─oracle-java-rhel-7.2-build (7623)
#   │        ├─extras-rhel-7.2-build (7630)
#   │        └─rhevh-rhel-7.2-build (7645)
#   └─rhel-7.2-pending (7603)
#      ├─rhel-7.2-compose (7605)
#      └─rhel-7.2-candidate (7604)

pkgs="
  file-5.11-31.el7
  libvirt-1.2.17-8.el7
  ocaml-4.01.0-22.6.el7
  qemu-kvm-1.5.3-102.el7
  systemd-219-13.el7
    dracut-033-339.el7
    initscripts-9.49.28-1.el7
    kmod-20-5.el7
"
for pkg in $pkgs ; do
    brew tag-pkg rhel-7.2-temp-override $pkg
done

for pkg in $pkgs ; do
    brew wait-repo rhel-7.2-build --build=$pkg
done
