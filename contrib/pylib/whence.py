#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0
#
# WHENCE data classes
#

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from ruamel.yaml import YAML


def strip(obj: list) -> list:
    """Remove leading and trailing empty strings from a list of strings"""
    if obj:
        while obj[0] == "":
            obj = obj[1:]
        while obj[-1] == "":
            obj = obj[:-1]
    return obj


@dataclass
class BaseWhence:
    """Base WHENCE data class"""

    def __str__(self):
        return json.dumps(asdict(self), indent=2)


@dataclass
class Entry(BaseWhence):
    """WHENCE file/link entry class"""

    type: str = ""  # File or RawFile or Link
    path: str = ""  # Firmware file or link
    target: str = ""  # Link target
    sources: list[str] = field(default_factory=list)  # List of source files
    version: str = ""
    info: str = ""
    origin: str = ""


@dataclass
class Section(BaseWhence):
    """WHENCE driver section class"""

    driver: str = ""
    module: str = ""
    description: str = ""
    licence: list[str] = field(default_factory=list)
    licence_file: str = ""
    notes: list[str] = field(default_factory=list)
    entries: list[Entry] = field(default_factory=list)


@dataclass
class Whence(BaseWhence):
    """Main WHENCE data class"""

    header: list[str] = field(default_factory=list)
    sections: list[Section] = field(default_factory=list)

    def load_whence(self, whence_file: Path) -> None:
        """Load data from a WHENCE file"""
        self.sections = []

        HEADER = 0
        SECTION = 1
        NOTES = 2
        LICENCE = 3

        with open(whence_file, encoding="utf-8") as fh:
            whence_type = HEADER
            for line in fh:
                line = line.rstrip()

                if ":" in line:
                    key, val = line.split(":", 1)
                    val = val.strip()
                else:
                    key = None
                    val = None

                if line.startswith("----------"):
                    whence_type = SECTION
                    section = Section()
                    self.sections.append(section)
                    continue

                if key == "Driver":
                    section.driver = val
                    if " " in val:
                        module, desc = val.split(" ", 1)
                        desc = desc.strip(" -")
                    else:
                        module = val
                        desc = ""
                    section.module = module
                    section.description = desc
                    continue

                if key in ("File", "RawFile"):
                    entry = Entry(type=key, path=val)
                    section.entries.append(entry)
                    continue

                if key == "Version":
                    entry.version = val
                    continue

                if key == "Link":
                    path, _, target = val.partition(" -> ")
                    entry = Entry(type=key, path=path, target=target)
                    section.entries.append(entry)
                    continue

                if key == "Source":
                    entry.sources.append(val)
                    continue

                if key == "Info":
                    entry.info = val
                    continue

                if key == "Origin":
                    entry.origin = val
                    continue

                if key in ("Licence", "License"):
                    whence_type = LICENCE
                    section.licence.append(val or "--")
                    m = re.search(r"(LICEN[CS]E\.[^ ]+) for details", line)
                    if m:
                        section.licence_file = m.group(1)
                    continue

                if whence_type == HEADER:
                    self.header.append(line)
                    continue

                if whence_type == NOTES or (whence_type == SECTION and line):
                    whence_type = NOTES
                    section.notes.append(line)
                    continue

                if whence_type == LICENCE:
                    section.licence.append(line)
                    continue

                if line:
                    raise Exception(f"Failed to parse line: {line}")

        # Strip leading and trailing empty lines
        self.header = strip(self.header)
        for s in self.sections:
            s.licence = strip(s.licence)
            s.notes = strip(s.notes)

    def save_yaml(self, whence_yaml: Path, remove_empty: bool = False) -> None:
        """Save the WHENCE data to a YAML file"""
        d = asdict(self)

        if remove_empty:
            # Hack: Remove empty items to reduce clutter
            for s in d["sections"]:
                for key in list(s):
                    if not s[key]:
                        del s[key]
                for e in s["entries"]:
                    for key in list(e):
                        if not e[key]:
                            del e[key]

        with open(whence_yaml, mode="w", encoding="utf-8") as fh:
            yaml = YAML()
            yaml.dump(d, fh)
