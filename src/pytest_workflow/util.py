import functools
import hashlib
import os
import re
import shutil
import subprocess
import sys
import warnings
from pathlib import Path
from typing import Callable, Iterator, List, Set, Tuple, Union

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


def _run_command(*args) -> str:
    """Run an external command and return the output"""
    result = subprocess.run(args,
                            stdout=subprocess.PIPE,
                            # Encoding to output as a string.
                            encoding=sys.getdefaultencoding(),
                            check=True)
    return result.stdout


def git_root(path: Filepath) -> str:
    output = _run_command(
        "git", "-C", os.fspath(path), "rev-parse", "--show-toplevel")
    return output.strip()  # Remove trailing newline


def git_check_submodules_cloned(path: Filepath):
    output = _run_command("git", "-C", os.fspath(path), "submodule", "status",
                          "--recursive")
    for line in output.splitlines():
        commit, path = line.strip().split(maxsplit=1)
        if commit.startswith("-"):
            raise RuntimeError(
                f"Git submodule '{path}' was not cloned. Pytest-workflow "
                f"cannot copy paths from non-existing submodules. Please "
                f"clone all submodules using 'git submodule update --init "
                f"--recursive'.")


def git_ls_files(path: Filepath) -> List[str]:
    output = _run_command("git", "-C", os.fspath(path), "ls-files",
                          # Make sure submodules are included.
                          "--recurse-submodules")
    # Remove trailing newlines and split to output all the paths
    return output.strip("\n").split("\n")


def _recurse_directory_tree(src: Filepath, dest: Filepath
                            ) -> Iterator[Tuple[str, str, bool]]:
    """Traverses src and for each file or directory yields a path to it,
    its destination, and whether it is a directory."""
    for entry in os.scandir(src):  # type: os.DirEntry  # type: ignore
        if entry.is_dir():
            dir_src = entry.path
            dir_dest = os.path.join(dest, entry.name)
            yield dir_src, dir_dest, True
            yield from _recurse_directory_tree(dir_src, dir_dest)
        elif entry.is_file() or entry.is_symlink():
            yield entry.path, os.path.join(dest, entry.name), False
        else:
            warnings.warn(f"Unsupported filetype for copying. "
                          f"Skipping {entry.path}")


def _recurse_git_repository_tree(src: Filepath, dest: Filepath
                                 ) -> Iterator[Tuple[str, str, bool]]:
    """Traverses src, finds all files registered in git and for each file or
    directory yields a path to it, its destination and whether it is a
    directory"""
    # A set of dirs we have already yielded. '' is the output of
    # os.path.dirname when the path is in the current directory.
    yielded_dirs: Set[str] = {''}
    git_check_submodules_cloned(src)
    for path in git_ls_files(src):
        # git ls-files does not list directories. Yield parent first to prevent
        # creating files in non-existing directories. Also check if it is
        # yielded before so each directory is only yielded once.
        parent = os.path.dirname(path)
        if parent not in yielded_dirs:
            # This maybe a nested directory, with non-existing parents itself.
            # Therefore:
            # - List parents from deepest to least deep by using os.path.dirname  # noqa: E501
            # - Reverse the list to yield directories from least deep to deepest  # noqa: E501
            # This ensures parents are always yielded before children.
            parents = []
            while parent not in yielded_dirs:
                yielded_dirs.add(parent)
                parents.append(parent)
                parent = os.path.dirname(parent)

            for parent in reversed(parents):
                src_parent = os.path.join(src, parent)
                dest_parent = os.path.join(dest, parent)
                yield src_parent, dest_parent, True

        # Yield the actual file if the directory has already been yielded.
        src_path = os.path.join(src, path)
        if not os.path.exists(src_path):
            raise FileNotFoundError(
                f"{path} from git repository {src} is checked in in git, "
                f"but not present in the filesystem. If the file was removed, "
                f"its removal can be recorded in git with "
                f"\"git -C '{src}' rm '{path}'\". "
                f"Removal can be reversed with "
                f"\"git -C '{src}' checkout '{path}'\".")
        dest_path = os.path.join(dest, path)
        yield src_path, dest_path, False


def duplicate_tree(src: Filepath, dest: Filepath,
                   symlink: bool = False,
                   git_aware: bool = False):
    """
    Duplicates a filetree
    :param src: The source directory
    :param dest: The destination directory
    :param symlink: Create symlinks nstead of copying the files.
    :param git_aware: Only copy/symlink files registered by git.
    """
    if not symlink and not git_aware:
        shutil.copytree(src, dest)
        return

    if not os.path.isdir(src):
        # shutil.copytree also throws a NotADirectoryError
        raise NotADirectoryError(f"Not a directory: '{src}'")

    if git_aware:
        path_iter = _recurse_git_repository_tree(src, dest)
    else:
        path_iter = _recurse_directory_tree(src, dest)
    if symlink:
        copy: Callable[[Filepath, Filepath], None] = \
            functools.partial(os.symlink, target_is_directory=False)
    else:
        # shutil.copy2 preserves metadata, also used by shutil.copytree
        # follow_symlinks False to directly copy links
        copy = functools.partial(shutil.copy2, follow_symlinks=False)

    os.makedirs(dest, exist_ok=False)
    for src_path, dest_path, is_dir in path_iter:
        if is_dir:
            os.mkdir(dest_path)
        else:
            copy(src_path, dest_path)


def link_tree(src: Filepath, dest: Filepath) -> None:
    """
    Copies a tree by mimicking the directory structure and soft-linking the
    files
    :param src: The source directory
    :param dest: The destination directory
    """
    # THIS FUNCTION IS KEPT FOR BACKWARDS-COMPATIBILITY
    duplicate_tree(src, dest, symlink=True)


# block_size 64k with python is a few percent faster than linux native md5sum.
def file_md5sum(filepath: Path, block_size=64 * 1024) -> str:
    """
    Generates a md5sum for a file. Reads file in blocks to save memory.
    :param filepath: a pathlib. Path to the file
    :param block_size: Block size in bytes
    :return: a md5sum as hexadecimal string.
    """
    hasher = hashlib.md5()
    with filepath.open('rb') as file_handler:  # Read the file in bytes
        for block in iter(lambda: file_handler.read(block_size), b''):
            hasher.update(block)
    return hasher.hexdigest()
