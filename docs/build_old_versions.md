# Build old versions

OpenPOWER Host OS 1.0 and 1.5 used an older CentOS (7.2) as base version.
To build one of them, do the following changes in this git repository
before building:

Update yum repository to CentOS 7.2:

```
$ sed -i 's|http://mirror.centos.org/altarch/|http://vault.centos.org/altarch/7.2.1511/|' config/mock/CentOS/7/CentOS-7-ppc64le.cfg
```

Update distro version to 7.2:

```
$ sed -i "s|distro_version:.*|distro_version: \"7.2\"|" config/host_os.yaml
$ sed -i -E "s|  '7': (\"\./config/mock.*)|  '7.2': \1|" config/host_os.yaml

```

Update build version to v1.5.0 or v1.0.0:

```
$ sed -i "s|packages_metadata_repo_branch:.*|packages_metadata_repo_branch: \"v1.5.0\"|" config/host_os.yaml  # use v1.5.0 or v1.0.0
```

Install rpm packages which were used in older build code, but are not anymore:

```
$ yum install -y bzip2 wget
```

Clean yum repositories cache in mock:

```
$ mock --scrub all
```

These steps are documented in
https://github.com/open-power-host-os/infrastructure/tree/master/jenkins_jobs/build_old_host_os_versions/script.sh .

