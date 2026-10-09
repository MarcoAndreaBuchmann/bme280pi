"""Detect the Raspberry Pi Version.

Contains the detect_raspberry_pi_version function, which
detects the version of the Raspberry Pi used.
"""

import warnings


def get_list_of_revisions() -> dict[str, str]:
    """List of known Raspberry Pi Revisions.

    Provides a list of known Raspberry Pi CPU IDs and the corresponding
    Raspberry Pi model name ("revision").

    Args:

    Returns:
        dict: dictionary of Raspberry Pi Revisions
    """
    known_revisions = {
        "0002": "Model B R1",
        "0003": "Model B R1",
        "0004": "Model B R2",
        "0005": "Model B R2",
        "0006": "Model B R2",
        "0007": "Model A",
        "0008": "Model A",
        "0009": "Model A",
        "000d": "Model B R2",
        "000e": "Model B R2",
        "000f": "Model B R2",
        "0010": "Model B+",
        "0011": "Compute Module",
        "0012": "Model A+",
        "a01041": "Pi 2 Model B",
        "a21041": "Pi 2 Model B",
        "900092": "Pi Zero",
        "900093": "Pi Zero",
        "a02082": "Pi 3 Model B",
        "a22082": "Pi 3 Model B",
        "9000c1": "Pi Zero W",
        "c03111": "Pi 4 Model B",
        "abcdef": "TestModel",
        "0000": "Unknown",
    }
    return known_revisions


def normalize_revision(revision: str) -> str:
    """Normalize a revision code as found in /proc/cpuinfo.

    Old-style revision codes (e.g. "0002") carry additional flag bits on boards
    whose over-voltage fuse has been blown: such a board reports "1000002"
    instead of "0002". The flag bits are removed here so that the code can be
    looked up in `get_list_of_revisions`. New-style revision codes (those with
    bit 23 set, e.g. "a02082") are returned unchanged. Codes that cannot be
    parsed as hexadecimal numbers are returned unchanged as well.

    Args:
        revision (str): revision code as a hexadecimal string

    Returns:
        str: normalized (lower case) revision code
    """
    revision = revision.lower()
    try:
        value = int(revision, 16)
    except ValueError:
        return revision

    if value & 0x800000:
        return revision

    return f"{value & 0xFFFF:04x}"


def detect_raspberry_pi_version() -> str:
    """Detect the Raspberry Pi Version.

    Detects the Raspberry Pi version based on CPU information.
    Note that if the model comes back as "Unknown", you may need
    to add it to the dictionary in `get_list_of_revisions`. The
    current list is up-to-date as of June 2020. Only the original
    Model B revision 1 needs to be recognized for the sensor to work,
    so an "Unknown" model is harmless in practice.

    Returns:
        str: Raspberry Pi version
    """
    revision = "0000"
    known_revisions = get_list_of_revisions()
    try:
        with open("/proc/cpuinfo", "r") as cpu_info:
            for line in cpu_info:
                if line.find("Revision") >= 0:
                    revision = line.rstrip().replace(" ", "").split(":")[1]
    except FileNotFoundError:
        warnings.warn("Could not find /proc/cpuinfo")
        return "Unknown"

    revision = normalize_revision(revision)
    if revision in known_revisions:
        return known_revisions[revision]

    return "Unknown"
