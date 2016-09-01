%if 0%{?fedora} >= 15 || 0%{?rhel} >= 7
%global with_systemd 1
%endif

%define ibm_release .1

%define pkvm_release .pkvm3_1_1

Name:       ginger-base
Version:    2.0.0
Release:    1%{?dist}%{?pkvm_release}
Summary:    Wok plugin for base host management
BuildRoot:  %{_topdir}/BUILD/%{name}-%{version}-%{release}
BuildArch:  noarch
Group:      System Environment/Base
License:    LGPL/ASL2
#Source0:   %{name}-%{version}.tar.gz
Source0:    %{name}.tar.gz
Requires:   wok
Requires:   pyparted
Requires:   python-cherrypy
Requires:   python-configobj
Requires:   python-lxml
Requires:   python-psutil >= 0.6.0
Requires:   rpm-python
Requires:   gettext
Requires:   git
Requires:   sos
BuildRequires:  gettext-devel
BuildRequires:  libxslt
BuildRequires:  python-lxml
BuildRequires: autoconf
BuildRequires: automake

%if 0%{?fedora} >= 23
Requires:   python2-dnf
%endif

%if 0%{?rhel} == 6
Requires:   python-ordereddict
BuildRequires:    python-unittest2
%endif

%description
Ginger Base is an open source base host management plugin for Wok
(Webserver Originated from Kimchi), that provides an intuitive web panel with
common tools for configuring and managing the Linux systems.

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

%files
%attr(-,root,root)
%{python_sitelib}/wok/plugins/gingerbase
%{_datadir}/gingerbase
%{_prefix}/share/locale/*/LC_MESSAGES/gingerbase.mo
%{_datadir}/wok/plugins/gingerbase
%{_datadir}/wok/plugins/gingerbase/ui/pages/tabs/host-dashboard.html.tmpl
%{_datadir}/wok/plugins/gingerbase/ui/pages/tabs/host-update.html.tmpl
%{_sysconfdir}/wok/plugins.d/gingerbase.conf
%{_sharedstatedir}/gingerbase/


%changelog
* Wed Jan 20 2016 <baseuser@ibm.com>
  Log from git:
- 0116a20469f779df16c4322dd97b2981d3a0feef Issue #19: Fix HTTP return code of host updated.
- ad2fed466e19254cb4b5d59acecc31689bca2c71 Update README.md file.
- b32fbb11d2db06fe50519b3dfb4906bdf0414af8 Issue #27 : wrong parent device name for multipath devices
- 14ce7c45d1d09edec10cc06555379f1bddf3aa78 Github #3: failing gingerbase tests
- e979cd5acc81e2f4b4c03c4a3b33d9a22ef8f0df Implement a new testcase for the sw upgrade monitor
- fce108fc28592a6c7c2e3a1416da4f374d72f814 Remove unecessary apt lock from AptRepo class
- aff316bd6a4162be9b36f186319f2cfc43e7e60e Remove unecessary apt lock from AptUpdate class
- 88fbc07bad0a8bb0ed479f5ae753c7c7c2fd25f2 Implement the package manager monitor frontend
- 8f1c57a71d39acdaae4c2e20b5fe22792f9640ac Implement class to support Fedora dnf package manager
- ff5edae125642f266f2bce28c3efe440a04fdf69 issue #23: Update README.md
- 518fae03aff5341976d43819aff9614acc3e5047 Debug report enhancement to find the generated SoSreport and debugreport files
- 52c7ea56e3bf7d0f5bfa839a961c94bd453cc0ef Fixing openSUSE rpm build
- 734f4b2dcde807585731d19008e11a6f6db8362a Do not rely on python-pip to install build dependencies
- f6bed1ff4755912b6a57ef233e3c5953eb578b82 Fix Portuguese translations for storage pool.
- d78e65b93c1f03a67d21d7a41304b19e9b755f85 Github #18: lscpu output varies with system language
- 8a03afe8ec068e6447feade3430f141c336ec3b7 Fixing errors in .po files
- 9d2ffb1dedffae95e108db14218ce565761dad9a Preparing Ginger-base version 2.0.0
- dda6b1135e80158a03c9c7975194c1685372224f Use correct gettext package for building
- 6c9f6ab36e469ff4f719ab99219b8f13e3edcbc7 Fixing whitespace errors
- 7e0cba5235b56bff0fbbdd295e6f699a28fba5ec Github #16: make check-local improvements
- f70ccb14fe1c3b1528f3760fd18c0b3ddf640ca8 Issue #14 : Help pages split
- 6b31d076c70c7aaeca2cd67c35d0166cc1b7dad4 Issue #14 : Help pages split
- 64c3487452dade4321ce8c3e2e30cb67c5ccc801 Issue #14 : Help pages split
- 1e41ecb9a8758b91b6ca5cde6ff6712dac50cbb1 Issue #14 : Help pages split
- fcaa1d3c8e3a944e8215c7c9099d894dd9a93e15 Issue #14 : Help pages split
- dcb4376784e06744317cfbb645f26b1c81f57557 Issue #14 : Help pages split
- 7e6234ce6186f92bcdf2a255beed4a141a3f8db1 Issue #14 : Help pages split
- 304a495acbeba4eb7abf20898dc7c671c9c986c3 Issue #14 : Help pages split
- 344297e1e02008d1482ce7de01b6947e270abcd5 Issue #14 : Help pages split
- 3df9b75f6d22fd841742a175b89768249871594f Issue #14 : Help pages split
- 1e32cfa8479ed8ce2255e25d2ed9e436571cbd04 Issue #14 : Help pages split
- 1d266db0db4a57616201fc4894e2ec73da409087 Removed line-chart SCSS from Wok and added to Gingerbase
- 1d9e6401460c37d85e2140763e3cb1689c925658 Upgrade GingerBase objectstore schema.
- d9c4da167b5859e66ee2a98bff05db449f3ee21c Use always flag as a fallback
- 67f4df227a8fe8286755ed2e28484982840318c8 Update dependencies for all distributions
- 9bf0a9c28bda69d45534302b71315f86c8aaac5b Issue #12: fixing _get_cpus() of HostModel
- 5d322a4cb5bdec9d11a5d4d464f7015f44b334ea Fixing RPM packaging of tabs
- 637389bab622b11ce27bbde73f7129b6be79669a Fixing broken packaging due to wrong variable
- 2f96d70ee8b8bda4d51ef2b808e55ab7a7c3fa27 Bug fix: Proper set role_key according to new tabs
- 3cf077e224580ae9d8f61a3c1ee39d59ab3be226 Remove required authentication from /
- 52dbc280d4515d787517febc67a3449b68d6fb3d Create read-only view for Dashboard tab
- b04c055660e11935a762c8de5c1702989dcbc471 Expose HTML tabs files in a specific /tabs URI
- 6039f64507aa97a265810ecb9a3d1d28490fb838 Add missing dependency python-apt
- 3f990d12df59ac9f1f119246e35455bac844ed16 Fixed Repository Add and Edit modals
- 21a29cbc9c7daff92b22ba5f339d6f8cf2f284bb Adding Media Queries support to Gingerbase
- a022e3c58b9040b7de577c97341d856639e33064 Issue #8: Ubuntu repositories not being displayed (error GGBREPOS0025E)
- f94dba213b96b4de80c7d2544ecd9ed80c8f9d6d Issue #4 : rpm creation failed on Fedora 23
- e4d839cf87ab1172104fceb061d88120e0f28b91 Fix Issue #2 - Support dnf for Fedora repositories and updates
- 299832ed895b532dec0847debeac4dfe354b1d5d Ginger Base repository
- b10d056daf0d65ef257e848d32798fc61b65b90d Fix issue 766 - Define network interface in libvirt

* Tue Aug 25 2015 Chandra Shehkhar Reddy Potula <chandra@linux.vnet.ibm.com> 0.0-1
- First build
