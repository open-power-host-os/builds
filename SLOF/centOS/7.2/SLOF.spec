%global gittagdate 20160525

%global gittag qemu-slof-%{gittagdate}

Name:           SLOF
Version:        %{gittagdate}
%define ibm_release  %{?repo}.1
Release:        1%{?dist}%{?ibm_release}
Summary:        Slimline Open Firmware

License:        BSD
URL:            http://www.openfirmware.info/SLOF
BuildArch:      noarch

# There are no upstream tarballs.  To prepare a tarball, do:
#
#  git clone https://github.com/open-power-host-os/slof.git
#  cd slof-frobisher
#  git checkout powerkvm-v3.1
#  git archive --format=tar --prefix=SLOF-%{gittagdate}/ HEAD | gzip > ../SLOF-%{gittagdate}.tar.gz
#

Source0:        SLOF-%{gittagdate}.tar.gz

# LTC: building native; no need for xcompiler
BuildRequires:  perl(Data::Dumper)


%description
Slimline Open Firmware (SLOF) is initialization and boot source code
based on the IEEE-1275 (Open Firmware) standard, developed by
engineers of the IBM Corporation.

The SLOF source code provides illustrates what's needed to initialize
and boot Linux or a hypervisor on the industry Open Firmware boot
standard.

Note that you normally wouldn't need to install this package
separately.  It is a dependency of qemu-system-ppc64.


%prep
%setup -q -n SLOF-%{gittagdate}

if test -r "gitlog" ; then
    echo "This is the first 50 lines of a gitlog taken at archive creation time:"
    head -50 gitlog
    echo "End of first 50 lines of gitlog."
fi

%build
export CROSS=""
make qemu %{?_smp_mflags} V=2


%install
mkdir -p $RPM_BUILD_ROOT%{_datadir}/qemu
cp -a boot_rom.bin $RPM_BUILD_ROOT%{_datadir}/qemu/slof.bin


%files
%doc FlashingSLOF.pdf
%doc LICENSE
%doc README
%dir %{_datadir}/qemu
%{_datadir}/qemu/slof.bin


%changelog
* Tue Sep 10 2013 baseuser@ibm.com
- Base-8.x spec file
