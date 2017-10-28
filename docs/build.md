# Building process

The build process relies on a metadata
[repository](https://github.com/open-power-host-os/versions) to obtain
information about the components to build, such as URLs, versions,
commit IDs, dependencies and distro-specific build parameters.

During the build process, the build script checks out the metadata
(versions) repository, obtains the information necessary to build the
package and starts an instance of
[mock](https://github.com/rpm-software-management/mock/wiki) that
builds the package in a chroot, taking care of its build dependencies.

Other functionalities of the build script are:

  - [build an installation ISO image](build_iso.md)
  - update the metadata in the versions repository according to each
   of the package's source code upstream
  - update the open-power-host-os metapackages
  - publish a summary of the code updates to the [web page](https://open-power-host-os.github.io)


Some common use cases when building packages are:

  1. Building one or a number of packages without modification from
  what the `versions` repository provides;

  1. Building a specific version of a package different from the one
    listed in the `versions` repository.

  1. Building a modified version of a package.

----
*For the following sections, make sure to have executed the initial setup:*

```
git clone https://github.com/open-power-host-os/builds.git
cd builds

sudo yum install epel-release
sudo yum install -y $(cat rpm_requirements.txt)
sudo usermod -a -G mock $(whoami)
```
----

## Building packages

Building packages is as simple as:

```
./host_os.py build-packages
```

which builds all of the packages listed in the
[versions](open-power-host-os/versions) repository or:

```
./host_os.py build-packages --packages kernel
```

which builds a specific package or list of packages.

The built packages are kept in a `result` directory (which can be
changed with the `--result-dir` option), and are not rebuilt in
subsequent runs of the command unless their source file have changed
since the creation of the last build results (to avoid this, use
--force-rebuild).

### Host OS stable

Another useful option for the `build-packages` command is
`--packages-metadata-repo-branch`, which allows for changing the branch
of the `versions` repository from which the packages metadata will be
retrieved.

For instance, to build the stable Host OS branch:

```
./host_os.py build-packages --packages-metadata-repo-branch hostos-stable
```

*to build versions prior to 2.0, check the [Build old
 versions](build_old_versions.md) page.*

<a name="specifying-metadata"></a>
## Building packages with modified metadata (source URL, commit ID, branch)

The `versions` repository contains build information for each Host OS
package such as source code URL, source code retrieval method (git,
svn, wget), git commit ID, branch, svn revision. This information can
be altered in a number of ways:

  - by making changes to a local clone of the `versions` repository and issuing:
    ```
    ./host_os.py build-packages --packages-metadata-repo-url file://<absolute path to versions> --packages-metadata-repo-branch <branch>
    ```

  - by making changes to `versions`, pushing them to a remote location (e.g. GitHub fork) and then:
    ```
    ./host_os.py build-packages --packages-metadata-repo-url https://github.com/<user>/versions --packages-metadata-repo-branch <branch>
    ```

  - by NOT making changes to `versions` repository, but informing them via command line to the `build-packages` command:
    ```
    ./host_os.py build-packages --packages package_name#repo_url#reference

    # e.g.:
    ./host_os.py build-packages --packages libvirt#https://github.com/open-power-host-os/libvirt#a2436b799ff91e304aad4e590f0adb0114908780
    ```

    *tip: check `./host_os.py build-packages --help` for other ways of specifying the `--package` option*


## Building packages with locally modified sources

To build a package from a modified local repository, use the
`--package` option, already listed above, but using the local repo
URL, like so:

```
./host_os.py build-packages --packages libvirt#file:///home/user/libvirt#a2436b799ff91e304aad4e590f0adb0114908780
```
