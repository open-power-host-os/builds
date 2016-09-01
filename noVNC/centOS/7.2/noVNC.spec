Name:           novnc
Version:        0.5.1
%define ibm_release %{?repo}.2
Release:        3%{?dist}%{?ibm_release}
Summary:        VNC client using HTML5 (Web Sockets, Canvas) with encryption support
Requires:       python-websockify

License:        GPLv3
URL:            https://github.com/kanaka/noVNC
Source0:        %{name}.tar.gz

Patch0:   novnc-0.4-manpage.patch
Patch1:   builds-issue33-add_non-us_keyboard_support.1.patch
Patch2:   builds-issue33-add_non-us_keyboard_support.2.patch

BuildArch:      noarch
BuildRequires:  python2-devel

%description
Websocket implementation of VNC client

%prep
%setup -q -n novnc
%patch0 -p1
%patch1 -p1
%patch2 -p1

%build


%install
mkdir -p %{buildroot}/%{_usr}/share/novnc/utils
install -m 444 *html %{buildroot}/%{_usr}/share/novnc
#provide an index file to prevent default directory browsing
install -m 444 vnc.html %{buildroot}/%{_usr}/share/novnc/index.html

mkdir -p %{buildroot}/%{_usr}/share/novnc/include/
install -m 444 include/*.*  %{buildroot}/%{_usr}/share/novnc/include
mkdir -p %{buildroot}/%{_usr}/share/novnc/images
install -m 444 images/*.*  %{buildroot}/%{_usr}/share/novnc/images

mkdir -p %{buildroot}/%{_bindir}
install utils/launch.sh  %{buildroot}/%{_bindir}/novnc_server

mkdir -p %{buildroot}%{_mandir}/man1/
install -m 444 docs/novnc_server.1 %{buildroot}%{_mandir}/man1/

%{__install} -d %{buildroot}%{_sysconfdir}/sysconfig

%files
%doc README.md LICENSE.txt

%dir %{_usr}/share/novnc
%{_usr}/share/novnc/*.*
%dir %{_usr}/share/novnc/include
%{_usr}/share/novnc/include/*
%dir %{_usr}/share/novnc/images
%{_usr}/share/novnc/images/*
%{_bindir}/novnc_server
%{_mandir}/man1/novnc_server.1*

%changelog
* Mon Aug 29 2016 Mauro S. M. Rodrigues <maurosr@br.ibm.com> - 0.5.1-3
- Add patches:
  0001-QEMU-RFB-extension-rfb.js-and-input.js-changes.patch
  0002-QEMU-RFB-extension-keyboard.js-changes.patch
  to address https://github.com/open-power-host-os/builds/issues/33

* Thu Feb 19 2015 Solly Ross <sross@redhat.com> - 0.5.1-2
- Update Source0 to point to correct URL

* Sat Jan 10 2015 Alan Pevec <apevec@redhat.com> - 0.5.1-1
- update to the new upstream version, for changes since 0.4 see:
  https://github.com/kanaka/noVNC/releases/tag/v0.5
  https://github.com/kanaka/noVNC/releases/tag/v0.5.1

* Sat Jun 07 2014 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.4-9
- Rebuilt for https://fedoraproject.org/wiki/Fedora_21_Mass_Rebuild

* Sat Aug 03 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.4-8
- Rebuilt for https://fedoraproject.org/wiki/Fedora_20_Mass_Rebuild

* Mon Jun 24 2013 Nikola Đipanov <ndipanov@redhat.com> - 0.4-7
- Remove the openstack-nova-novncproxy subpackage (moved to openstack-nova)

* Mon Apr 08 2013 Nikola Đipanov <ndipanov@redhat.com> - 0.4-6
- Import config module from oslo in nova-novncproxy

* Mon Mar 18 2013 Nikola Đipanov <ndipanov@redhat.com> - 0.4-5
- Change FLAGS to the new CONF module in nova-novncproxy
- Drop the hard dwp on whole nova package and require only nova-common

* Thu Feb 28 2013 Pádraig Brady <P@draigBrady.com> - 0.4-4
- Support /etc/sysconfig/openstack-nova-novncproxy #916479

* Thu Feb 14 2013 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.4-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_19_Mass_Rebuild

* Mon Oct 22 2012 Nikola Đipanoov <ndipanov@redhat.com> - 0.4-2
- Fixes the supplied init script to match the new 0.4 version

* Mon Oct 22 2012 Nikola Đipanoov <ndipanov@redhat.com> - 0.4-1
- Moves to upstream version 0.4.0

* Fri Jul 20 2012 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 0.3-12
- Rebuilt for https://fedoraproject.org/wiki/Fedora_18_Mass_Rebuild

* Wed Jul  4 2012 Till Maas <opensource@till.name> - 0.3-11
- Add a dependency for novnc on python-websockify

* Fri Jun 15 2012 Jose Castro Leon <jose.castro.leon@cern.ch> - 0.3-10
- Add a dependency for openstack-nova-novncproxy on openstack-nova

* Thu Jun 14 2012 Matthew Miller <mattdm@mattdm.org> - 0.3-9
- Remove a dependency for openstack-nova-novncproxy on numpy

* Wed Jun 13 2012 Alan Pevec <apevec@redhat.com> - 0.3-8
- Add a dependency for openstack-nova-novncproxy on python-nova

* Wed Jun 13 2012 Jose Castro Leon <jose.castro.leon@cern.ch> - 0.3-7
- Add a dependency for openstack-nova-novncproxy on novnc

* Mon Jun 11 2012 Adam Young <ayoung@redhat.com> - 0.3-6
- systemd initialization for Nova Proxy
- system V init script
- remove Flash binary supporting older browsers

* Fri Jun 8 2012 Adam Young <ayoung@redhat.com> - 0.3-3
- Added man pages
- novnc_server usese the websockify executable, not wsproxy.py

* Thu Jun 7 2012 Adam Young <ayoung@redhat.com> - 0.3-2
- Make Javascript files non-executable, as they are not script files
- Patch Nova noVNC proxy to use websockify directly

* Tue May 15 2012 Adam Young <ayoung@redhat.com> - 0.3-1
- Added in support for the Nova noVNC proxy
- Added files for the images and inclues subdirectories

* Thu May 10 2012 Adam Young <ayoung@redhat.com> - 0.2
- Initial RPM release.
