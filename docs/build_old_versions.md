# Build old versions

OpenPOWER Host OS 1.0 and 1.5 used an older CentOS (7.2) as base version along
with different file paths. To build one of them, do the following changes in
this git repository before building.

Update yum repository to CentOS 7.2:

```
mkdir -p config/mock/centOS/7.2
cp config/mock/CentOS/7/CentOS-7-ppc64le.cfg config/mock/centOS/7.2/centOS-7.2-ppc64le.cfg
sed -i 's|http://mirror.centos.org/altarch/7/|http://vault.centos.org/altarch/7.2.1511/|' config/mock/centOS/7.2/centOS-7.2-ppc64le.cfg
```

Install rpm packages which were used in older build code, but are not anymore:

```
yum install -y bzip2 wget
```

Clean yum repositories cache in mock:

```
mock -r config/mock/centOS/7.2/centOS-7.2-ppc64le.cfg --scrub all
mock --scrub all
```

Build packages:

```
python host_os.py --verbose --distro-name centOS --distro-version 7.2 build-packages --packages-metadata-repo-branch hostos-1.5
python host_os.py --verbose --distro-name centOS --distro-version 7.2 build-packages --packages-metadata-repo-branch v1.0.0
```

These steps are documented in
https://github.com/open-power-host-os/infrastructure/tree/master/jenkins_jobs/build_old_host_os_versions/script.sh .
