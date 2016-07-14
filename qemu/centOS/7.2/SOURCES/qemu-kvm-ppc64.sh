#!/bin/sh

exec /usr/bin/qemu-system-ppc64 -machine accel=kvm "$@"
