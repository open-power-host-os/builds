import logging
import os

LOG = logging.getLogger(__name__)

SOFTWARE_DIRECTORY = os.path.join(os.getcwd(), "components")


def discover_software():
    """
    Simple mechanism for discoverability of the software we build.

    A discoverable software, and thus potentially buildable, will be assume as
    any directory name under SOFTWARE_DIRECTORY containing a yaml file with
    the same name.
    Considering the example:

    components
    +-- kernel
    |   +-- kernel.yaml
    +-- libvirt
    |   +-- libvirt.yaml
    |   +-- someother_file_or_directory
    +-- not-a-software
    |   +-- not-following-standards.yaml
    +-- file

    "kernel" and "libvirt" will be discovered, "not-a-software" and "file"
    will not.
    """
    return [software for software in os.listdir(SOFTWARE_DIRECTORY)
            if os.path.isdir(os.path.join(SOFTWARE_DIRECTORY, software)) and
            os.path.isfile(os.path.join(SOFTWARE_DIRECTORY, software,
                                        "".join([software, ".yaml"])))
            ]
