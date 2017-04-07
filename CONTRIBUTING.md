# Contributing

This is an open source project and thus you're welcome to contribute!

## Contributing Code

Any source code contribution should be done through github's pull request, see
general instructions [here](https://guides.github.com/activities/contributing-to-open-source/#contributing).

Also, please, follow the code style proposed by [PEP8](https://www.python.org/dev/peps/pep-0008/). There is a tool called pycodestyle, formerly known as pep8, that checks if your code is compliant.

## Contributing packages

For details on adding new packages to the project, refer to the versions repository documentation at https://github.com/open-power-host-os/versions/blob/master/CONTRIBUTING.md.

## Review process

See details on review process [here](REVIEW_PROCESS.md).

## Validating

There is a whole repository dedicated to testing available at
https://github.com/open-power-host-os/tests

In order to run the build scripts unit tests or code linter, you will need to
install our development dependencies.

You can do this by issuing the command below

```
$ sudo pip install -r requirements-dev.txt
```

### Running code linter

From the root of the `builds` project directory, use the commands below to run
the code linter (Pylint):

```
$ PYTHON_FILES=$(find . -name "*.py")
$ pylint $PYTHON_FILES
```

### Running unit tests

From the root of the `builds` project directory, use the commands below to run
the unit tests:

```
$ export PYTHONPATH=$(pwd):$PYTHONPATH
$ nosetests tests/unit
```

## Issues

Feel free to open an issue at any moment [here](https://github.com/open-power-host-os/builds/issues).
