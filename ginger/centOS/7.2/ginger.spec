%define ibm_release .1

%define pkvm_release .pkvm3_1_1

Name:       ginger
Version:    2.2.0
Release:    2%{?dist}%{?pkvm_release}
Summary:    Host management plugin for Wok - Webserver Originated from Kimchi
BuildRoot:  %{_topdir}/BUILD/%{name}-%{version}-%{release}
Group:      System Environment/Base
License:    LGPL/ASL2
Source0:    %{name}.tar.gz
BuildArch:  noarch
BuildRequires:  gettext-devel >= 0.17
BuildRequires:  autoconf
BuildRequires:  automake
BuildRequires:  libxslt
Requires:   gettext >= 0.17
Requires:   wok >= 2.1.0
Requires:   ginger-base
Requires:   libuser-python
Requires:       libvirt
Requires:   python-ethtool
Requires:   python-ipaddr
Requires:   python-magic
Requires:   python-netaddr
Requires:   python-augeas
Requires:       libvirt-python


%description
Ginger is a host management plugin for Wok (Webserver Originated from Kimchi),
that provides an intuitive web panel with common tools for configuring and
operating Linux systems. Kimchi is a Wok plugin for managing KVM/Qemu virtual
machines.

%if 0%{?fedora} >= 15 || 0%{?rhel} >= 7
%global with_systemd 1
%endif

%prep
%setup -n %{name}


%build
./autogen.sh --system
make


%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install


%clean
rm -rf $RPM_BUILD_ROOT


%post
%if 0%{?with_systemd}
    install -dm 0755 /usr/lib/systemd/system/wokd.service.requires
    ln -sf ../tuned.service /usr/lib/systemd/system/wokd.service.requires
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :
    service wokd restart
%endif


%postun
%if 0%{?with_systemd}
    if [ $1 == 0 ]; then  # uninstall
        rm -f /usr/lib/systemd/system/wokd.service.requires/tuned.service
        /bin/systemctl daemon-reload >/dev/null 2>&1 || :
        service wokd restart
    fi
%endif


%files
%attr(-,root,root)
%{python_sitelib}/wok/plugins/ginger/*.py*
%{python_sitelib}/wok/plugins/ginger/API.json
%{python_sitelib}/wok/plugins/ginger/control/*.py*
%{python_sitelib}/wok/plugins/ginger/model/*.py*
%{_datadir}/wok/plugins/ginger/ui/images/*.svg
%{_prefix}/share/locale/*/LC_MESSAGES/ginger.mo
%{_datadir}/wok/plugins/ginger/ui/config/tab-ext.xml
%{_datadir}/wok/plugins/ginger/ui/css/base/images/*.gif
%{_datadir}/wok/plugins/ginger/ui/css/base/images/*.png
%{_datadir}/wok/plugins/ginger/ui/css/ginger.css
%{_datadir}/wok/plugins/ginger/ui/js/*.js
%{_datadir}/wok/plugins/ginger/ui/pages/help/ginger-help.css
%{_datadir}/wok/plugins/ginger/ui/pages/help/*/*.html
%{_datadir}/wok/plugins/ginger/ui/pages/tabs/*.html.tmpl
%{_datadir}/wok/plugins/ginger/ui/pages/i18n.json.tmpl
%{_datadir}/wok/plugins/ginger/ui/pages/host-network*.html.tmpl
%{_datadir}/wok/plugins/ginger/ui/pages/*.html.tmpl
%{_sysconfdir}/wok/plugins.d/ginger.conf
%{_sysconfdir}/systemd/system/wokd.service.d/ginger.conf


%changelog
* Thu Sep 01 2016 Mauro S. M. Rodrigues <maurosr@linux.vnet.ibm.com> - 2.2.0-2.pkvm3_1_1
- Build August, 31st, 2016

* Wed Aug 24 2016 <baseuser@ibm.com>
  Log from git:
- 4b9924f023099d28c919e55e0834860ca8342d06 Issue #381: 'make clean' does not revert its changes from 'make rpm'
- 6fec29c3ecbf857a8cd3199cc8fcf3eb038e1ffa Capabilities API: get current feature state
- 2b9565f2887b38789b957fe4fed1b4f6ce4d160e Make all is_feature_available methods static
- 317d4d73265759802a2c498d86791f76e2a6bec4 Fixing miscellaneous issues in swap functionalities
- 6c73928647a85b998e0122a66469741a3c55ee48 Fixing miscellaneous issues in swap functionalities
- 10af984cf47d9f0cfd7abbaa2a2a509a3efa8e4d Add missing user request log messages
- 762e2e98de6d9d9bcb9901d7a5852f55493b1723 Remove duplicated entry
- 4826f3b56e33ee7f803506856840e4b75c7d0176 Revert "Use past verbs and other log message improvements"
- 56b0aaa70d386eda6a6b168d1637081a4ea461ee Move audit error messages along to correct section
- 260e87bcf63e35bac328a438fe64f912984d1aaa Ginger control: import control classes using sub_node
- 9bd9ee1f293d76c7d684b637362e21bd41db84a8 test/test_authorization.py: test changes after urlsubnode change
- ba0c0862aabd02ace16cd3fb07588ff3723b7b8b Removing control/nfsshares.py file
- 5affd694999fb83e6e566b9cd14044db7fa9c96a Control classes: fixing @UrlSubNode calls
- a1054c215ad1ebef319227dfdcc57255013d661e Issue #372 : Add support for target rescan
- 0efe8265ecbd70750875125f5ead7bded5019578 docs/API.md : adding configuration backup APIs
- 3fac3f0b38bdfb506d3ef957ff8d3162e0b7be8f docs/API.md: removing duplicated ibm_sep entry
- 3988eabb242f6524e0db585185c7424056e35f10 Introducing Volume Group related operations.
- 6df0850a73c26a499b63609b778e735ca7bba03b Introducing Volume group related operations.
- 17cca53e5f7d3df3f2d44fa6794467e63ba59398 Introducing Volume group related operations.
- 597159efa472e0c797484e96fc8013d500485c45 Update stringutils imports
- fb9b53d74e81bdc83eaaf49617813cd396ce3740 Issue #377 : Full Width and Arabic digits not accepted for batch delete of config backup
- e4beb6d74b8302f593028713190e52d2eea4af79 Revert "Globalisation support - externalize all remaining strings for ginger plugin."
- 3b3a91bb64f19692800f348df96b9e1a70f0a3ff Issue #372 : Add support to target authentication
- 7a762e61e808f8ba5b4ff4a57fe3f84fc469b410 Globalisation support - externalize all remaining strings for ginger plugin.
- e79ead0fe695cffabbb051ff6fa51c06d11fcea5 Modify the info returned by partitions listing API
- 9dbae80e2eef671f482b8733bd6aa224c7957b09 Issue #375 :Fifteen Character VLAN device name not being recognized as a valid VLAN Interface name.
- 85317f0b8f3b68f0dced1115ef19057205af0c28 Issue #376:Unable to edit the text field or click submit/cancel after press ESC or click outside the error message dialog of Add User.
- 74182c95dc44ef83e5dcd0431a167ab3fd66e195 Time out while generating config back up file leave the tar file behind
- 9439806d811a7c2bbbb7907cb3ab507e65b3f212 Issue #372 : iSCSI Discovery and IQN actions support
- a84c1c51b07da6e763f19653b884df55bd222d4a Audit rules backend: new tests file test_rules
- 617cf532691b23c51a09d7ecdcbd303552c560f7 Audit rules backend: changes in controls, ginger.py and model/model.py
- bbeea7b374749ab5539db3859900b1f452c252c9 Audit rules backend: API doc and i18n.py changes.
- ebce57e2d0461d215422a9b5c9ba69c63d48f4ea Audit rules backend: new model/rules.py module
- a1e3df94a82457c6e8e2b8e810904537220ee1fa Introducing File system related operations.
- 26e08586e2f0b8901b5f7efe2d40016026f34b7c Introducing File system related operations.
- f93c2f6c4bf242cad45e43fb77ab1b43d056fd28 Introducing File system related operations.
- b85b15f732d2ad442597696faf903351f93bbcad Extend Filesystem mounting to include mount options
- 4de6c1454ace270454c6fec08c923c03ae072c10 Added cursor for tasks in progress
- e3d52545c4b6fa49dc4489f39d4ffdac663fbd99 Improvements on Configuration Backup UI
- 670fdf8457768f01646fc9537b77025572f7b8c2 Github #94: OpenSUSE network support
- ba7623c6c47daef6bbe9ceaabbd5638a89db4e47 Implementation of Partition for storage devices
- 97f0d08f6a296eb789167edec53d6984ab07b2c5 Issue #371 : Create disk partitions takes integer input for size
- 4c1f481b48b6f52fe337a12e63330ef8f41117ae Github #121: WoK log flooded by hddtemp messages
- 84f43d5188892e30b39793d9c6e43d555f0ed88d Issue #300 : Redesign "Network Configuration" UI
- 4cb9b33e90d32d140b9db2545df4c8076531e330 Fixing wok_log redundancy and i18n.py error messages
- 681174296d5c0f70ff8609e82e24921ec3edbbc1 Fixing wok_log redundancy and i18n.py error messages
- aea7709b8e2d8c5fadd5ee164a1b56e95aee8e38 Fixing wok_log redundancy and i18n.py error messages
- 32f2841ca3e893f1346b4210b922bebcf89ebc07 Fixing wok_log redundancy and i18n.py error messages
- 930c71db18c3bdeabc98580679696fe81db448cd Issue #299: Redesign "Global Network Configuration" UI
- 3529cd987e7d7202b94771882337b94e3efd54a6 Removing debug info from model/users.py

* Tue Jul 12 2016 Daniel Henrique Barboza <danielhb@linux.vnet.ibm.com>
- Added 'dir' directives for each dir and subdir in the 'files' section
- rpmlint fixes

* Tue May 31 2016 Ramon Medeiros <ramonn@linux.vnet.ibm.com>
- Update spec with Fedora community Guidelines

* Mon May 16 2016 Ramon Medeiros <ramonn@linux.vnet.ibm.com>
- Does not disable tuned service as dependency when update package

* Wed Mar 23 2016 Daniel Henrique Barboza <dhbarboza82@gmail.com>
- Removed 'pyparted' from dependencies because it is a Ginger-base dependency
- Removed 'python-cheetah' from build dependencies
- Added wok version restriction >= 2.1.0

* Tue Mar 1 2016 Daniel Henrique Barboza <dhbarboza82@gmail.com>
- added ui/images/*.svg in 'files' section

* Sat Feb 6 2016 Chandra Shekhar Reddy Potula <chandra@linux.vnet.ibm.com>
- Add libvirt service dependencies to Ginger

* Mon Jan 25 2016 Daniel Henrique Barboza <dhbarboza82@gmail.com>
- Changed 'controls' dir to 'control' in 'files' section
- Added 'datadir'/wok/plugins/ginger/ui/pages/*.html.tmpl to 'files'
- Changed 'models' dir to 'model' in 'files' section

* Fri Dec 25 2015 Daniel Henrique Barboza <dhbarboza82@gmail.com>
- Changed 'files' to include all ui/js/*.js js files
- Changed 'files' to include all ui/pages/help/*/*.html help files
- Changed 'files' to include all ui/pages/tabs/*.html.tmpl tabs

* Wed Dec 16 2015 Daniel Henrique Barboza  <dhbarboza82@gmail.com>
- Removed 'host-admin.css' from 'files'
- added 'ui/js/ginger-bootgrid.js' in 'files'

* Fri Dec 11 2015 Daniel Henrique Barboza  <dhbarboza82@gmail.com>
- Added ui/pages/tabs/host-admin.html.tmpl to 'files'

* Fri Nov 27 2015 Chandra Shekhar Reddy Potula <chandra@linux.vnet.ibm.com>
- Add missing dependencies for Ginger

* Thu Oct 2 2014 Rodrigo Trujillo <rodrigo.trujillo@linux.vnet.ibm.com>
- Add Help pages for Ginger
- Change build system to enable and release Help pages

* Wed Jul  2 2014 Paulo Vital <pvital@linux.vnet.ibm.com> 1.2.1
- Changed the package name from kimchi-ginger to ginger

* Wed Apr 16 2014 Zhou Zheng Sheng <zhshzhou@linux.vnet.ibm.com> 1.2.0
- Initial release of Kimchi-ginger dedicated RPM package
