%define ibm_release .1

%define pkvm_release .pkvm3_1_1

Name:       kimchi
Version:    2.2.0
Release:    2%{?dist}%{?pkvm_release}
Summary:    Kimchi server application
BuildRoot:  %{_topdir}/BUILD/%{name}-%{version}-%{release}
BuildArch:  noarch
Group:      System Environment/Base
License:    LGPL/ASL2
Source0:    %{name}.tar.gz
Requires:   wok >= 2.1.0
Requires:   ginger-base
Requires:   qemu-kvm
Requires:   gettext
Requires:   libvirt
Requires:   libvirt-python
Requires:   libvirt-daemon-config-network
Requires:   python-websockify
Requires:   python-configobj
Requires:   novnc
Requires:   python-pillow
Requires:   pyparted
Requires:   python-psutil >= 0.6.0
Requires:   python-jsonschema >= 1.3.0
Requires:   python-ethtool
Requires:   sos
Requires:   python-ipaddr
Requires:   python-lxml
Requires:   nfs-utils
Requires:   iscsi-initiator-utils
Requires:   python-libguestfs
Requires:   libguestfs-tools
Requires:   python-magic
Requires:   python-paramiko
BuildRequires:  gettext-devel
BuildRequires:  libxslt
BuildRequires:  python-lxml
BuildRequires:  autoconf
BuildRequires:  automake

%if 0%{?rhel} >= 6 || 0%{?fedora} >= 19
Requires:   spice-html5
%endif

%if 0%{?fedora} >= 15 || 0%{?rhel} >= 7
%global with_systemd 1
%endif

%if 0%{?rhel} == 6
Requires:   python-ordereddict
Requires:   python-imaging
BuildRequires:    python-unittest2
%endif

%description
Web application to manage KVM/Qemu virtual machines


%prep
%setup -n %{name}
./autogen.sh --system


%build
%if 0%{?rhel} >= 6 || 0%{?fedora} >= 19
%configure
%else
%configure --with-spice-html5
%endif
make


%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install


%clean
rm -rf $RPM_BUILD_ROOT

%files
%attr(-,root,root)
%{python_sitelib}/wok/plugins/kimchi/
%{_datadir}/kimchi/doc/
%{_prefix}/share/locale/*/LC_MESSAGES/kimchi.mo
%{_datadir}/wok/plugins/kimchi/
%{_sysconfdir}/wok/plugins.d/kimchi.conf
%{_sysconfdir}/kimchi/
%{_sharedstatedir}/kimchi/
%{_sysconfdir}/systemd/system/wokd.service.d/kimchi.conf


%changelog
* Thu Sep 01 2016 Mauro S. M. Rodrigues <maurosr@linux.vnet.ibm.com> - 2.2.0-2.pkvm3_1_1
- Build August, 31st, 2016

* Wed Aug 24 2016 <baseuser@ibm.com>
  Log from git:
- 5d50e5308e1cf68c2c9530ea09e52856ef184aa3 Merge remote-tracking branch 'upstream/master' into powerkvm-v3.1.1
- 564caeff6a038f67fa2ae4d337c94d7fbc777b8c Fix when calling error message in storagepool
- 3a4eab04d079c2fad08b98b4a95e44899dd09fa6 Issue #933: Invalid image path not marking template as "invalid" (back-end)
- a05de4991cbb71d32133f8d4631750a3e89e2c28 test/test_model.py pep8 1.5.7 fix
- 12d85d330f6cb4e5de0cb17f9035afe5fef20a12 Issue #982 - Fix broken testcases.
- b73e7aea2d019f49e6d83caab07314b1e72ca9e0 Update docs
- 6490cb2d6ccf8e9917059cc22930ba2f856235f7 Update tests
- 6a37e55c893df381f6a4686bdf1f8ecb72b85de5 Issue #857: Support VM description
- 4231b292acef87ef06a3ff947dfa1c5bc43eb5bd Merge remote-tracking branch 'upstream/master' into openpower-v3.1.1
- 351917d8e642b7eadc94a6eeda20dc337ffb774f Issue #317 Inconsistent button status when adding or creating new resources
- 2c84b510e44df88f9ae2c512ca99e2a9ff28e86e Prevents pci passthrough double click
- 7cc96b592191b521effac1a6bb98a2b4dbf29474 Fix frontend vcpu hotplug
- 430a08b47dabef185bc94e41b0fdce31ed875846 Issue #585: 'make clean' does not revert its changes from 'make rpm'
- de355ab4b26f54994ea9b7c91aedb9fff00fcc2a model.py: use the new 'get_all_model_instances' utils function
- 7d7c2add2b457b89ce88424e20e60fa20d4360e2 Modified code, to return distro and version as unknown, if guestfs import failed.
- 56bf15c1b670186f44ec48f41b20c3dfdf657044 Added s390x architecture support in osinfo params.
- 1d235836a8f4dfbf8cd9d4517fa1ace9ac247672 Added on_poweroff, on_reboot, on_crash tag to also support s390x architecture.
- b0675bc8473a9cfc47a11f2eb1d22b8a0a97df39 Added method for implementation of s390x boot detection.
- 13073796fdb2eac2c05a1f75ed1a5f002db073b0 Added check for s390x architecture to not add graphics in params as not supported.
- 83d92f8c40e80384102b9c3b79d94d366b853ce2 Issue #604: Windows XP: Kimchi should set the right NIC Type in Templates
- 38aeade3d04fc62c7a3852b8480d96be8289e36c Revert "Use verbs in the past"
- 4cb6484ea412dac08ab995ae47e8c37380e6037f Updated serial console to support s390x architecture.
- 6719ebb3d274c6236486ec7bb714cc09cc632424 New memory Hot-UNplug implementation
- c90d95dfc04cee88268cec1835f0dc057a071f78 Merge remote-tracking branch 'upstream/master' into openpower-v3.1.1
- b45afea94cb11628c1a41c8714df4eca938a247d Validate passthrough inside the task
- 12bb8addb91dd6acab39acb83d8f701b8e2a73b0 Replace device companion check before the passthrough
- 2c0ce1d5012a47be92dd719ad4626d6ba91e998a Improve PCI passthrough performance
- d62079bc06b9df6a93e4b93e022664e8d5d504bb Add test to verify bootmenu and update old tests
- 616c6a9b29616577d2a5850d1ae45b4307636d82 Allow guest to enable bootmenu on startup
- 6eeaa837854671add9356ee3490f6f18fcce579a Disable vm statistics/screenshots in edit guest
- 765a954dcf6e25ee17c802a2c193794cfbaa744c Issue #968: Kimchi is searching for 'undefined' VM
- 42717b3fd98e4d40f75be4cc515fbec9d05a74c7 Add test to check bootorder
- 255e6d90c7bf756798054940bdf71924971f16aa Add function to retrieve bootorder on vm lookup
- 7d6be682ab01fadd2590a9af7ea199749a85a086 Update REST API
- 394422f11cc99b9cc9dbad4e4ea1920020dcaa4b Update documentation about bootorder on vm update
- a5b9e1fd8f34d6886bc3874b9f4f1dd45ddac613 Create method to change bootorder of a guest
- e05c7a378ba4302047ebc12142ed850e1215ad7c Add function get_bootorder_node
- 24cc635d8d0180bc77a6473a511dc14fed6d3fdb Virt-Viewer launcher: mockmodel changes
- d57f2b555190f57a3925eec357c9f9c81514512a Virt-Viewer launcher: changes after adding libvirt event listening
- 5d58c673aa76c0644cbec28bc975f9b4b54555d1 Virt-Viewer launcher: libvirt events to control firewall
- b822c44aa56b0a5b3e74237b633f48c628886dfa Virt-Viewer launcher: test changes for firewall manager
- dc70e6bc6541d59ee43beb037221a415a7e98df1 Virt-Viewer launcher: adding FirewallManager class
- 80c170d86d338e489238cecf3b537305a801ef6d Virt-Viewer launcher: test changes
- f5a47afc4448b625010b8427ac84cef5d82151c9 Virt-Viewer launcher: virtviewerfile module
- f8b51e1ce33ef3a1fb25cdfad5423a6a29fa5893 Virt-Viewer launcher: control/vms.py and model/vms.py changes
- 9148d3f0cce3ff8b46b76e443e8f6087f4790182 Virt-Viewer launcher: Makefile and config changes
- abb511449c12c151e01f643dbb0dcfad6b700928 Virt-Viewer launcher: docs and i18n changes
- 66144ab95e71b9905cc3f4fbae4799ef7c24d2ff Merge remote-tracking branch 'upstream/master' into openpower-v3.1.1
- e0faa466f6c25bddb6dfe299c02aa755bf6af394 Kimchi kills Wokd due to sys.exit() calls in files networks.py and storagepools.py
- 66567fe2181c8fe613e7e7282c3416840dcd8d49 Issue #969: Error message showing up in parent panel rather than modal window in Add Storage

* Thu Jun 18 2015 Lucio Correia <luciojhc@linux.vnet.ibm.com> 2.0
- Run kimchi as a plugin

* Thu Feb 26 2015 Frédéric Bonnard <frediz@linux.vnet.ibm.com> 1.4.0
- Add man page for kimchid

* Tue Feb 11 2014 Crístian Viana <vianac@linux.vnet.ibm.com> 1.1.0
- Add help pages and XSLT dependency

* Tue Jul 16 2013 Adam Litke <agl@us.ibm.com> 0.1.0-1
- Adapted for autotools build

* Thu Apr 04 2013 Aline Manera <alinefm@br.ibm.com> 0.0-1
- First build
