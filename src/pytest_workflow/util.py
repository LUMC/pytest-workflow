import os
import re
import shutil
import warnings
from pathlib import Path
from typing import List


# This function was created to ensure the same conversion is used throughout
# pytest-workflow.
def replace_whitespace(string: str, replace_with: str = '_') -> str:
    """
    Replaces all whitespace with the string in replace_with.
    :param string: input string
    :param replace_with: Replace whitespace with this string. Default: '_'
    :return: The string with whitespace converted.
    """
    return re.sub(r'\s+', replace_with, string)


def rm_dirs(directories: List[Path]):
    for directory in directories:
        shutil.rmtree(str(directory))


def is_in_dir(child: Path, parent: Path, strict: bool = False) -> bool:
    """
    Checks if child path is in parent path. Works for non-existent paths if
    strict is set to false.
    :param child: The path of interest
    :param parent: The parent directory
    :param strict: Check if paths exist when resolving.
    :return: True or False
    """
    resolved_child = child.resolve(strict=strict)
    resolved_parent = parent.resolve(strict=strict)
    if str(resolved_child).startswith(str(resolved_parent)):
        # /my/path/parent-dir/child starts with /my/path/parent but is not in
        # that dir. We can check this by checking the filepathparts
        # individually.
        for cpart, ppart in zip(resolved_child.parts, resolved_parent.parts):
            if not cpart == ppart:
                break
        else:
            # No break: If we did not find any mismatches child is in parent.
            return True
    return False


def link_tree(src: Path, dest: Path) -> None:
    """
    Copies a tree by mimicking the directory structure and soft-linking the
    files
    :param src: The source directory
    :param dest: The destination directory
    """
    if src.is_dir():
        dest.mkdir(parents=True)
        for path in os.listdir(str(src)):
            link_tree(Path(src, path), Path(dest, path))
    elif src.is_file() or src.is_symlink():
        os.symlink(str(src), str(dest), target_is_directory=False)
    else:  # Only copy files and symlinks, no devices etc.
        warnings.warn(f"Unsupported filetype. Skipping copying: '{str(src)}' "
                      f"to '{str(dest)}'.")
