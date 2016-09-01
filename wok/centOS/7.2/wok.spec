%define ibm_release .1

%define pkvm_release .pkvm3_1_1

Name:       wok
Version:    2.2.0
Release:    2%{?dist}%{?pkvm_release}
Summary:    Wok - Webserver Originated from Kimchi
BuildRoot:  %{_topdir}/BUILD/%{name}-%{version}-%{release}
BuildArch:  noarch
Group:      System Environment/Base
License:    LGPL/ASL2
Source0:    %{name}.tar.gz
Requires:   gettext
Requires:   python-cherrypy >= 3.2.0
Requires:   python-cheetah
Requires:   m2crypto
Requires:   PyPAM
Requires:   python-jsonschema >= 1.3.0
Requires:   python-lxml
Requires:   nginx
Requires:   python-ldap
Requires:   python-psutil >= 0.6.0
Requires:   fontawesome-fonts
Requires:   open-sans-fonts
Requires:   logrotate
BuildRequires:  gettext-devel
BuildRequires:  libxslt
BuildRequires:  openssl
BuildRequires:  python-lxml

%if 0%{?fedora} >= 15 || 0%{?rhel} >= 7
%global with_systemd 1
%endif

%if 0%{?rhel} == 6
Requires:   python-ordereddict
Requires:   python-imaging
BuildRequires:    python-unittest2
%endif

%if 0%{?with_systemd}
Requires:   systemd
Requires:   firewalld
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd
%endif

%if 0%{?with_systemd}
BuildRequires: systemd-units
%endif

BuildRequires: autoconf
BuildRequires: automake

%description
Wok is Webserver Originated from Kimchi.


%prep
%setup -n %{name}


%build
./autogen.sh --system
make


%install
rm -rf %{buildroot}
make DESTDIR=%{buildroot} install

%if 0%{?rhel} == 6
# Install the upstart script
install -Dm 0755 contrib/wokd-upstart.conf.fedora %{buildroot}/etc/init/wokd.conf
%endif
%if 0%{?rhel} == 5
# Install the SysV init scripts
install -Dm 0755 contrib/wokd.sysvinit %{buildroot}%{_initrddir}/wokd
%endif

install -Dm 0640 src/firewalld.xml %{buildroot}%{_prefix}/lib/firewalld/services/wokd.xml

# Install script to help open port in firewalld
install -Dm 0744 src/wok-firewalld.sh %{buildroot}%{_datadir}/wok/utils/wok-firewalld.sh



%post
if [ $1 -eq 1 ] ; then
    /bin/systemctl enable wokd.service >/dev/null 2>&1 || :
    # Initial installation
    /bin/systemctl daemon-reload >/dev/null 2>&1 || :

    # Add wokd as default service into public chain of firewalld
    %{_datadir}/wok/utils/wok-firewalld.sh public add wokd
fi


%preun

if [ $1 -eq 0 ] ; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable wokd.service > /dev/null 2>&1 || :
    /bin/systemctl stop wokd.service > /dev/null 2>&1 || :

    # Remove wokd service from public chain of firewalld
    %{_datadir}/wok/utils/wok-firewalld.sh public del wokd
    firewall-cmd --reload >/dev/null 2>&1 || :
fi

exit 0


%postun
if [ "$1" -ge 1 ] ; then
    /bin/systemctl try-restart wokd.service >/dev/null 2>&1 || :
fi
exit 0

%clean
rm -rf $RPM_BUILD_ROOT

%files
%attr(-,root,root)
%{_bindir}/wokd
%{python_sitelib}/wok/*.py*
%{python_sitelib}/wok/control/*.py*
%{python_sitelib}/wok/model/*.py*
%{python_sitelib}/wok/xmlutils/*.py*
%{python_sitelib}/wok/API.json
%{python_sitelib}/wok/plugins/*.py*
%{python_sitelib}/wok/
%{_prefix}/share/locale/*/LC_MESSAGES/wok.mo
%{_datadir}/wok/ui/
%{_datadir}/wok
%{_sysconfdir}/nginx/conf.d/wok.conf.in
%{_sysconfdir}/wok/wok.conf
%{_sysconfdir}/wok/
%{_sysconfdir}/logrotate.d/wokd
%{_mandir}/man8/wokd.8.gz

%if 0%{?with_systemd}
%{_sysconfdir}/nginx/conf.d/wok.conf
%{_sharedstatedir}/wok/
%{_localstatedir}/log/wok/*
%{_localstatedir}/log/wok/
%{_unitdir}/wokd.service
%{_prefix}/lib/firewalld/services/wokd.xml
%endif
%if 0%{?rhel} == 6
/etc/init/wokd.conf
%endif
%if 0%{?rhel} == 5
%{_initrddir}/wokd
%endif

%changelog
* Wed Aug 24 2016 <baseuser@ibm.com>
  Log from git:
- 520838dc93b4fabc2141555b858d5513a32b2c41 Merge remote-tracking branch 'upstream/master' into powerkvm-v3.1.1
- 885a817f2c09acdb80a715bf337849eb7780d35c Status label on user log #145
- 8ceffbd0b9e4885fbf3ad754aed997fa00b1050c Merge remote-tracking branch 'upstream/master' into openpower-v3.1.1
- 2336f97ca7a0dda708b83d539f17c7c946e54999 Issue #155: 'make clean' does not revert its changes from 'make rpm'
- eaf780c895f510fac4c3fdf75659b0958c7c85b3 model.py: use the new 'get_all_model_instances' utils function
- 2dfb1f8ddccbbf40d05d0cc48f74cbb6f318a5f0 wok/utils.py: adding utility 'get model instances' methods
- bc9406570d30c66270516ae9209f00b33fc78cef Update tests
- 09d1e4e3d8867b4dd2fe082f28fd0db12768548b Fix issue #140 - Add original exception to user request log message
- 86f200ef33dee30aaf01f5a62a4db99791ee59d0 Add selinux/wokd.te describing the SELinux policy to allow httpd context and allow nginx start up with no errors.
- bab46edd4206a8e3c0516209b06f8aef11035316 Merge remote-tracking branch 'upstream/master' into openpower-v3.1.1
- e9e6d48c98278d53e3a61a36397df4eb9f2e0739 Fix ascii_dict and utf8_dict
- 9bc2c489e50c518a9eb8caaccdc245139aed518b Update tests
- 7297cba20adec34626b331343de24a29370605d2 Fix issue with converting message to unicode
- b741558fc840e5ebb89732e7d7f60ac1b55b5f7c Issue #142 - Translate request log at reading-time
- b1df9ec0ee4f251506c29a3c856b7ecb4efe427a Add option to get untranslated message text
- 408e45f17df09dd65891520109eb6d1dbd772774 Isolate string utils in order to avoid cyclic import
- 7ca7cb1c068b3484a25f48f9d955659cbdcd4145 Adding close callback support for wok.confirm dialog
- 5d872fcf38836cf9307c2e3306e6751d1786a33d Merge remote-tracking branch 'upstream/master' into openpower-v3.1.1
- bfa4fc7714acce8a13e3f81a7e40ca82e5a117a1 Externalise the tab names and locale list
- b2ae4d8e9e68d1d220370028cefd2048da81f185 Calendar per locale setting in User Log Advanced search
- b2234a93eb9dcf9675c184b8c2c3ac598a9903db Externalise request types in advanced search panel of user activity log
- ca62ba31d5a12c38a121d04067c3dfce1dd351cf Merge remote-tracking branch 'upstream/master' into openpower-v3.1.1
- 4cbb1b93d62fb0b3ac0a2d5ece89d9b01f710b61 Use system's nginx proxy service.
- 23d785c655059f8b6b1bb5bf9a4d9428921cf586 User session timeout alert (UI)
- 925624df62ed911d19f9125e72395cab42821a4d Kimchi kills Wokd due to sys.exit() calls in files networks.py and storagepools.py
- 158e44fa4b5ea35ba316644089b99220261e76b5 Issue #133: Kimchi is logging out due to session timeout even when user is typing or using the webpage
- b29555afde85a276266256f3562debbabdec7c06 Move constant from auth.py to template.py
- 5354ce2e97d09092afce4ee7fc75b0dbb24da56f Issue 136: Changes for User Log UI
- 01e2af1ffcda53333887163b3b99ae31a48cd064 Fixes loading message position inside panel-groups
- accf63a89d2f4277cff18399277f344d0c6f1169 Added cursor for tasks in progress
- 4c61122711b29a8880509c72a33839e8faa6754b Merge remote-tracking branch 'upstream/master' into openpower-v3.1.1
- f0c4b4465e801b9850e047656dee8d19dbc03ec2 Use callback instead of log file for run_command output
- e61e8087bddbed973b6260316aaa10f6878b207b Merge remote-tracking branch 'upstream/master' into openpower-v3.1.1
- 8131d34e33bd47dd21e69776017a9e694d85ee3b Added DataTables.net JS minified files
- a96124cf508f4b9f8f8e7dee9acaa5bcd688dd9d Added Moment.JS file with locales
- f2465b5b7835b0373137e164f0b99560c550cfca Initial commit for Datatables.net and Moment.JS
- b26abf2201b0de2d38e28b372a8bacdbbc63cf3c Merge remote-tracking branch 'upstream/master' into openpower-v3.1.1
- 487bf95ed7829b1301a99025845870fc0dd9cd0d Make sure all log messages have required parameters
- 35454b291e8bc82a389c89315c3a90bec2d4e4b3 Fix PEP8 issue
- 20c9ccc52160917f98794d97ada880067375b37d Issue #116:No indication of debug reports being generated(Gingerbase)
- e2c50250617ede4192ba8c25e70a6ac7de4f4948 Issue #79: All error messages should keep on UI until user dismiss it
- 5843b3134268f6093033d80140b18e67a1615530 Add status code to request log message
- 684c19ab217a3996966034a5592a9be013a150d4 Log failed user requests
- 6d739341e155b36bac15f8b2528766bdcdfb6697 Log failed login/logout attempts
- 91730f7398bd8198f7f4499733bc60aaf08ec941 Use status code 200 for PUT requests on resource
- 55a1d9123b11501b33aab7fb929d051cc8b4110f Parse request before authorization check
- 222c4c6b5643c7be28729a3e4952ab942dadbd51 Revert "Use past verbs"
- fe068e11b05fe45a5b0054b8145c3b7dd7add019 Update ChangeLog, VERSION and .po files for 2.2 release
- 50fdc25f9fb66e3ff8a2fb1959fbb4e21c6d47de Merge remote-tracking branch 'upstream/master' into openpower-v3.1.1
- 0e57dfe9ebfdad518bb86c464f620b0de942e51d Github #138: fix loadash Makefile.am
