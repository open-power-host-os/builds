#!/bin/bash -
# Additional custom requires for libguestfs package.

original_find_requires="$1"
shift

# Get the list of files.
files=`sed "s/['\"]/\\\&/g"`

# Use ordinary find-requires first.
echo $files | tr [:blank:] '\n' | $original_find_requires

# Is supermin.d/packages included in the list of files?
packages=`echo $files | tr [:blank:] '\n' | grep 'supermin\.d/packages$'`

if [ -z "$packages" ]; then
    exit 0
fi

# Generate one 'Requires:' line for each package listed in packages.
cat $packages

# We need to add library dependencies required by guestfsd (which
# is in the appliance).
guestfsd=$RPM_BUILD_ROOT/usr/sbin/guestfsd
if [ ! -x $guestfsd ]; then
    echo "$0: cannot find guestfsd" >&2
    exit 1
fi
echo $guestfsd | $original_find_requires
