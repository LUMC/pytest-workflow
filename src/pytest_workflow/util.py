import hashlib
import os
import re
import subprocess  # nosec
import sys
import warnings
from pathlib import Path
from typing import Iterator, List, Set, Tuple, Union

Filepath = Union[str, os.PathLike]


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


def _run_command(*args):
    """Run an external command and return the output"""
    result = subprocess.run(args,  # nosec
                            stdout=subprocess.PIPE,
                            # Encoding to output as a string.
                            encoding=sys.getdefaultencoding(),
                            check=True)
    return result.stdout


def git_get_root(path: Filepath) -> str:
    output = _run_command(
        "git", "-C", os.fspath(path), "rev-parse", "--show-toplevel")
    return output.strip()  # Remove trailing newline


def git_ls_files(path: Filepath) -> List[str]:
    output = _run_command("git", "-C", os.fspath(path), "ls-files")
    # Remove trailing newlines and split to output all the paths
    return output.strip("\n").split("\n")


def _duplicate_tree(src: Filepath, dest: Filepath
                    ) -> Iterator[Tuple[str, str, bool]]:
    """Traverses src and for each file or directory yields a path to it,
    its destination, and whether it is a directory."""
    for entry in os.scandir(src):  # type: os.DirEntry
        if entry.is_dir():
            dir_src = entry.path
            dir_dest = os.path.join(dest, entry.name)
            yield dir_src, dir_dest, True
            yield from _duplicate_tree(dir_src, dir_dest)
        elif entry.is_file() or entry.is_symlink():
            yield entry.path, os.path.join(dest, entry.name), False
        else:
            warnings.warn(f"Unsupported filetype for copying. "
                          f"Skipping {entry.path}")


def _duplicate_git_tree(src: Filepath, dest: Filepath
                        ) -> Iterator[Tuple[str, str, bool]]:
    """Traverses src, finds all files registered in git and for each file or
    directory yields a path to it, its destination and whether it is a
    directory"""
    # A set of dirs we have already yielded. '' is the output of
    # os.path.dirname when the path is in the current directory.
    dirs: Set[str] = {''}
    for path in git_ls_files(src):
        src_path = os.path.join(src, path)
        dest_path = os.path.join(dest, path)
        yield src_path, dest_path, False
        parent = os.path.dirname(src_path)
        if parent not in dirs:
            src_path = os.path.join(src, parent)
            dest_path = os.path.join(dest, parent)
            yield src_path, dest_path, True


def link_tree(src: Filepath, dest: Filepath) -> None:
    """
    Copies a tree by mimicking the directory structure and soft-linking the
    files
    :param src: The source directory
    :param dest: The destination directory
    """
    if not os.path.isdir(src):
        # shutil.copytree also throws a NotADirectoryError
        raise NotADirectoryError(f"Not a directory: '{src}'")
    os.makedirs(dest, exist_ok=False)
    for src_path, dest_path, is_dir in _duplicate_tree(src, dest):
        if is_dir:
            os.mkdir(dest_path)
        else:
            os.symlink(src_path, dest_path, target_is_directory=False)


# block_size 64k with python is a few percent faster than linux native md5sum.
def file_md5sum(filepath: Path, block_size=64 * 1024) -> str:
    """
    Generates a md5sum for a file. Reads file in blocks to save memory.
    :param filepath: a pathlib. Path to the file
    :param block_size: Block size in bytes
    :return: a md5sum as hexadecimal string.
    """
    hasher = hashlib.md5()  # nosec: only used for file integrity
    with filepath.open('rb') as file_handler:  # Read the file in bytes
        for block in iter(lambda: file_handler.read(block_size), b''):
            hasher.update(block)
    return hasher.hexdigest()
