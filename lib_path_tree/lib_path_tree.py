# STDLIB
import fnmatch
import os
import pathlib
import shutil
from typing import List

# OWN
import lib_ignore_files
import lib_list
import lib_parameter
import lib_path


def copy_files_recursive_filtered(path_source_dir: pathlib.Path, path_target_dir: pathlib.Path,
                                  l_patterns_match: List[str] = None, l_patterns_unmatch: List[str] = None,
                                  b_create_empty_directories: bool = True):
    """
    You can use fnmatch patterns to match and to unmatch - unmatch wins over match.
    
    ls_patterns_match: default = ['*'], Match pattern immer relativ zu source Directory - dies matched alle Files und leere Directories
                                        ['*'] matched alles - ['*.*'] nur alle Files mit Extension !
    ls_patterns_nomatch: default = []
    b_create_empty_directories: leere Verzeichnisse erzeugen

    :raises: NotADirectoryError when the source directory does not exist
             RunTimeError wenn Zielverzeichnis im Quellverzeichnis (rekursive Kopie auf sich selbst)

    >>> # Setup
    >>> import unittest
    >>> import pprint
    >>> path_test_dir = pathlib.Path(__file__).parent.parent / 'tests'
    >>> p_bad_source_dir = pathlib.Path('./does/not/exist')
    >>> path_source_dir = path_test_dir / 'treecopy_test_source.dir'
    >>> path_target_dir = path_test_dir / 'treecopy_test_target.dir'
    >>> targets_match=['*/.hidden*/*']
    >>> targets_unmatch=['*_no_match*']
    >>> shutil.rmtree(str(path_target_dir),ignore_errors=True)

    >>> # test source does not exist
    >>> unittest.TestCase().assertRaises(NotADirectoryError, copy_files_recursive_filtered, path_source_dir=p_bad_source_dir, path_target_dir=path_target_dir)

    >>> # test target dir within source dir
    >>> unittest.TestCase().assertRaises(NotADirectoryError, copy_files_recursive_filtered, path_source_dir=path_target_dir, path_target_dir=path_test_dir)

    >>> # test copy all
    >>> shutil.rmtree(str(path_target_dir),ignore_errors=True)
    >>> copy_files_recursive_filtered(path_source_dir, path_target_dir)
    >>> assert len(list(path_target_dir.rglob('*'))) == 26

    >>> # test copy some with match / unmatch
    >>> shutil.rmtree(str(path_target_dir),ignore_errors=True)
    >>> copy_files_recursive_filtered(path_source_dir, path_target_dir, targets_match, targets_unmatch)
    >>> pprint.pp(sorted(list(path_target_dir.rglob('*'))))  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    [.../tests/treecopy_test_target.dir/.hidden_match.dir'),
     .../tests/treecopy_test_target.dir/.hidden_match.dir/.hidden_test_match.file'),
     .../tests/treecopy_test_target.dir/.hidden_match.dir/test_match.file')]

    >>> assert len(list(path_target_dir.rglob('*'))) == 3

    >>> # Teardown
    >>> shutil.rmtree(str(path_target_dir),ignore_errors=True)

    """

    l_patterns_match = lib_parameter.get_default_if_none(l_patterns_match, default=['*'])
    l_patterns_unmatch = lib_parameter.get_default_if_none(l_patterns_unmatch, default=[])
    path_source_dir = path_source_dir.resolve()
    path_target_dir = path_target_dir.resolve()
    lib_path.log_and_raise_if_not_isdir(path_source_dir)
    lib_path.log_and_raise_if_target_directory_within_source_directory(path_source_dir, path_target_dir)
    l_path_sources = list_paths_recursive_filtered(path_source_dir, l_patterns_match, l_patterns_unmatch)
    # TODO IGNORE FILES
    # l_path_ignore_files = lib_ignore_files.get_l_nomatch_from_ignore_files(path_source_dir, ignore_file_name='.rotekignore')
    # l_path_sources = lib_list.l_substract_unsorted_fast(l_path_sources, l_path_ignore_files)

    for path_source in l_path_sources:
        path_target = pathlib.Path(str(path_source).replace(str(path_source_dir), str(path_target_dir), 1))
        copy_path_object_with_metadata(path_source, path_target, b_create_empty_directories)


def list_dirs_recursive(path_base_dir: pathlib.Path) -> List[pathlib.Path]:
    """
    get all files (not directories) under the base directory, recursive. Includes also dotted files in dotted directories

    >>> # Setup
    >>> # Setup
    >>> from pprint import pp
    >>> path_test_dir = pathlib.Path(__file__).parent.parent / 'tests'
    >>> path_source_dir = path_test_dir / 'treecopy_test_source.dir'

    >>> # test
    >>> pp(sorted(list_dirs_recursive(path_source_dir)))  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    [.../tests/treecopy_test_source.dir'),
     .../tests/treecopy_test_source.dir/.hidden_match.dir'),
     .../tests/treecopy_test_source.dir/.hidden_no_match.dir'),
     .../tests/treecopy_test_source.dir/test_empty.dir'),
     .../tests/treecopy_test_source.dir/test_empty2.dir'),
     .../tests/treecopy_test_source.dir/test_empty2.dir/test_empty.dir'),
     .../tests/treecopy_test_source.dir/test_match.dir'),
     .../tests/treecopy_test_source.dir/test_no_match.dir')]

    >>> import decorator_timeit
    >>> # timeit with test directory
    >>> result = decorator_timeit.TimeIt(repeat=100)(list_dirs_recursive)(path_base_dir=path_source_dir)

    """

    path_base_dir = path_base_dir.resolve()
    lib_path.log_and_raise_if_not_isdir(path_base_dir)
    l_path_result = list()

    # we use os.walk because it is 3 x faster then pathlib.Path('.').rglob(*)
    # and oddly pathlib.Path('.').rglob(*) fails on windows on samba share (sometimes)
    l_path_result.append(pathlib.Path(path_base_dir))
    for root, dirs, files in os.walk(str(path_base_dir), topdown=False):
        for s_dir in dirs:
            path_dir = pathlib.Path(root) / s_dir
            l_path_result.append(path_dir)
    return l_path_result


def list_dirs_recursive_filtered(path_base_dir: pathlib.Path, l_patterns_match: List[str] = None, l_patterns_unmatch: List[str] = None) -> List[pathlib.Path]:
    """

    # TODO IGNORE FILES
    # l_path_ignore_files = lib_ignore_files.get_l_nomatch_from_ignore_files(path_source_dir, ignore_file_name='.rotekignore')
    # l_path_sources = lib_list.l_substract_unsorted_fast(l_path_sources, l_path_ignore_files)

    all directories recursive from the base directory (including the base directory itself)

    Es dürfen auch Verzeichnisnamen und Wildcards in den Filtern  verwendet werden.

    ls_patterns_nomatch übersteuert ls_patterns_match

    Vorsicht : ls_files_match=['*.*'] matched nur Files mit einer Extension.
               für alle Files : ls_files_match=['*']


    Matches / Unmatches Patterns. Patterns for directories :
    >>> # Setup
    >>> from pprint import pp
    >>> path_test_dir = pathlib.Path(__file__).parent.parent / 'tests'
    >>> path_source_dir = path_test_dir / 'treecopy_test_source.dir'

    >>> pp(sorted(list_dirs_recursive_filtered(path_source_dir,['*/test*'],[]))) # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    [.../tests/treecopy_test_source.dir'),
     .../tests/treecopy_test_source.dir/.hidden_match.dir'),
     .../tests/treecopy_test_source.dir/.hidden_no_match.dir'),
     .../tests/treecopy_test_source.dir/test_empty.dir'),
     .../tests/treecopy_test_source.dir/test_empty2.dir'),
     .../tests/treecopy_test_source.dir/test_empty2.dir/test_empty.dir'),
     .../tests/treecopy_test_source.dir/test_match.dir'),
     .../tests/treecopy_test_source.dir/test_no_match.dir')]

    >>> pp(sorted(list_dirs_recursive_filtered(path_source_dir,['*/test*'],['*no_match*']))) # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    [.../tests/treecopy_test_source.dir'),
     .../tests/treecopy_test_source.dir/.hidden_match.dir'),
     .../tests/treecopy_test_source.dir/test_empty.dir'),
     .../tests/treecopy_test_source.dir/test_empty2.dir'),
     .../tests/treecopy_test_source.dir/test_empty2.dir/test_empty.dir'),
     .../tests/treecopy_test_source.dir/test_match.dir')]

    >>> pp(sorted(list_dirs_recursive_filtered(path_source_dir,['*/test*'],['*/.hidden*']))) # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    [.../tests/treecopy_test_source.dir'),
     .../tests/treecopy_test_source.dir/test_empty.dir'),
     .../tests/treecopy_test_source.dir/test_empty2.dir'),
     .../tests/treecopy_test_source.dir/test_empty2.dir/test_empty.dir'),
     .../tests/treecopy_test_source.dir/test_match.dir'),
     .../tests/treecopy_test_source.dir/test_no_match.dir')]

    """
    path_base_dir = path_base_dir.resolve()
    lib_path.log_and_raise_if_path_does_not_exist(path_base_dir)
    lib_path.log_and_raise_if_not_isdir(path_base_dir)

    l_paths_all = list_dirs_recursive(path_base_dir)
    l_paths_result = filter_path_objects(l_paths=l_paths_all, l_patterns_match=l_patterns_match, l_patterns_unmatch=l_patterns_unmatch)

    return l_paths_result


def list_files_recursive(path_base_dir: pathlib.Path) -> List[pathlib.Path]:
    """
    get all files (not directories) under the base directory, recursive. Includes also dotted files in dotted directories

    >>> # Setup
    >>> import timeit
    >>> from pprint import pp
    >>> path_test_dir = pathlib.Path(__file__).parent.parent / 'tests'
    >>> path_source_dir = path_test_dir / 'treecopy_test_source.dir'
    >>> pp(sorted(list_files_recursive(path_source_dir))) # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    [.../tests/treecopy_test_source.dir/.hidden_match.dir/.hidden_test_match.file'),
     .../tests/treecopy_test_source.dir/.hidden_match.dir/.hidden_test_no_match.file'),
     .../tests/treecopy_test_source.dir/.hidden_match.dir/test_match.file'),
     .../tests/treecopy_test_source.dir/.hidden_match.dir/test_no_match.file'),
     .../tests/treecopy_test_source.dir/.hidden_match.file'),
     .../tests/treecopy_test_source.dir/.hidden_no_match.dir/.hidden_test_match.file'),
     .../tests/treecopy_test_source.dir/.hidden_no_match.dir/.hidden_test_no_match.file'),
     .../tests/treecopy_test_source.dir/.hidden_no_match.dir/test_match.file'),
     .../tests/treecopy_test_source.dir/.hidden_no_match.dir/test_no_match.file'),
     .../tests/treecopy_test_source.dir/.hidden_no_match.file'),
     .../tests/treecopy_test_source.dir/test_match.dir/.hidden_test_match.file'),
     .../tests/treecopy_test_source.dir/test_match.dir/.hidden_test_no_match.file'),
     .../tests/treecopy_test_source.dir/test_match.dir/test_match.file'),
     .../tests/treecopy_test_source.dir/test_match.dir/test_match_file_noextension'),
     .../tests/treecopy_test_source.dir/test_match.dir/test_no_match.file'),
     .../tests/treecopy_test_source.dir/test_no_match.dir/.hidden_test_match.file'),
     .../tests/treecopy_test_source.dir/test_no_match.dir/.hidden_test_no_match.file'),
     .../tests/treecopy_test_source.dir/test_no_match.dir/test_match.file'),
     .../tests/treecopy_test_source.dir/test_no_match.dir/test_no_match.file')]

    >>> import decorator_timeit
    >>> # timeit with test directory
    >>> result = decorator_timeit.TimeIt(repeat=100)(list_files_recursive)(path_base_dir=path_source_dir)
    >>> # timeit with /media/softdev/rotek-apps
    >>> path_base_dir = pathlib.Path('/media/softdev/rotek-apps')
    >>> result2 = decorator_timeit.TimeIt(repeat=100)(list_files_recursive)(path_base_dir=path_source_dir)

    """

    path_base_dir = path_base_dir.resolve()
    lib_path.log_and_raise_if_not_isdir(path_base_dir)
    l_path_result = list()

    # we use os.walk because it is 3 x faster then pathlib.Path('.').rglob(*)
    # and oddly pathlib.Path('.').rglob(*) fails on windows on samba share (sometimes)
    for root, dirs, files in os.walk(str(path_base_dir), topdown=False):
        for name in files:
            path_file = pathlib.Path(root) / name
            l_path_result.append(path_file)
    return l_path_result


def list_paths_recursive(path_base_dir: pathlib.Path) -> List[pathlib.Path]:
    """
    get all files and directories (including tha base directory) under the base directory, recursive. Includes also dotted files in dotted directories

    >>> # Setup
    >>> import timeit
    >>> from pprint import pp
    >>> path_test_dir = pathlib.Path(__file__).parent.parent / 'tests'
    >>> path_source_dir = path_test_dir / 'treecopy_test_source.dir'
    >>> pp(sorted(list_paths_recursive(path_source_dir))) # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    [.../tests/treecopy_test_source.dir'),
     .../tests/treecopy_test_source.dir/.hidden_match.dir'),
     .../tests/treecopy_test_source.dir/.hidden_match.dir/.hidden_test_match.file'),
     .../tests/treecopy_test_source.dir/.hidden_match.dir/.hidden_test_no_match.file'),
     .../tests/treecopy_test_source.dir/.hidden_match.dir/test_match.file'),
     .../tests/treecopy_test_source.dir/.hidden_match.dir/test_no_match.file'),
     .../tests/treecopy_test_source.dir/.hidden_match.file'),
     .../tests/treecopy_test_source.dir/.hidden_no_match.dir'),
     .../tests/treecopy_test_source.dir/.hidden_no_match.dir/.hidden_test_match.file'),
     .../tests/treecopy_test_source.dir/.hidden_no_match.dir/.hidden_test_no_match.file'),
     .../tests/treecopy_test_source.dir/.hidden_no_match.dir/test_match.file'),
     .../tests/treecopy_test_source.dir/.hidden_no_match.dir/test_no_match.file'),
     .../tests/treecopy_test_source.dir/.hidden_no_match.file'),
     .../tests/treecopy_test_source.dir/test_empty.dir'),
     .../tests/treecopy_test_source.dir/test_empty2.dir'),
     .../tests/treecopy_test_source.dir/test_empty2.dir/test_empty.dir'),
     .../tests/treecopy_test_source.dir/test_match.dir'),
     .../tests/treecopy_test_source.dir/test_match.dir/.hidden_test_match.file'),
     .../tests/treecopy_test_source.dir/test_match.dir/.hidden_test_no_match.file'),
     .../tests/treecopy_test_source.dir/test_match.dir/test_match.file'),
     .../tests/treecopy_test_source.dir/test_match.dir/test_match_file_noextension'),
     .../tests/treecopy_test_source.dir/test_match.dir/test_no_match.file'),
     .../tests/treecopy_test_source.dir/test_no_match.dir'),
     .../tests/treecopy_test_source.dir/test_no_match.dir/.hidden_test_match.file'),
     .../tests/treecopy_test_source.dir/test_no_match.dir/.hidden_test_no_match.file'),
     .../tests/treecopy_test_source.dir/test_no_match.dir/test_match.file'),
     .../tests/treecopy_test_source.dir/test_no_match.dir/test_no_match.file')]

    """

    path_base_dir = path_base_dir.resolve()
    lib_path.log_and_raise_if_not_isdir(path_base_dir)
    l_path_result = list()

    # we use os.walk because it is 3 x faster then pathlib.Path('.').rglob(*)
    # and oddly pathlib.Path('.').rglob(*) fails on windows on samba share (sometimes)

    l_path_result.append(path_base_dir)
    for root, dirs, files in os.walk(str(path_base_dir), topdown=False):
        for s_dir in dirs:
            path_dir = pathlib.Path(root) / s_dir
            l_path_result.append(path_dir)
        for name in files:
            path_file = pathlib.Path(root) / name
            l_path_result.append(path_file)
    return l_path_result


def list_paths_recursive_filtered(path_base_dir: pathlib.Path, l_patterns_match: List[str] = None, l_patterns_unmatch: List[str] = None) -> List[pathlib.Path]:
    """

    # TODO IGNORE FILES
    # l_path_ignore_files = lib_ignore_files.get_l_nomatch_from_ignore_files(path_source_dir, ignore_file_name='.rotekignore')
    # l_path_sources = lib_list.l_substract_unsorted_fast(l_path_sources, l_path_ignore_files)

    Directory aller Files und Verzeichnisse welche den Suchkriterien entsprechen rekursiv vom Basisverzeichnis
    Es dürfen auch Verzeichnisnamen und Wildcards in den Filtern  verwendet werden.

    ls_patterns_nomatch übersteuert ls_patterns_match

    Vorsicht : ls_files_match=['*.*'] matched nur Files mit einer Extension.
               für alle Files : ls_files_match=['*']


    Matches / Unmatches Patterns. Patterns for directories :
    >>> # Setup
    >>> from pprint import pp
    >>> path_test_dir = pathlib.Path(__file__).parent.parent / 'tests'
    >>> path_source_dir = path_test_dir / 'treecopy_test_source.dir'

    >>> pp(sorted(list_paths_recursive_filtered(path_source_dir,['*match*/*'],[]))) # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    [.../tests/treecopy_test_source.dir/.hidden_match.dir/.hidden_test_match.file'),
     .../tests/treecopy_test_source.dir/.hidden_match.dir/.hidden_test_no_match.file'),
     .../tests/treecopy_test_source.dir/.hidden_match.dir/test_match.file'),
     .../tests/treecopy_test_source.dir/.hidden_match.dir/test_no_match.file'),
     .../tests/treecopy_test_source.dir/.hidden_no_match.dir/.hidden_test_match.file'),
     .../tests/treecopy_test_source.dir/.hidden_no_match.dir/.hidden_test_no_match.file'),
     .../tests/treecopy_test_source.dir/.hidden_no_match.dir/test_match.file'),
     .../tests/treecopy_test_source.dir/.hidden_no_match.dir/test_no_match.file'),
     .../tests/treecopy_test_source.dir/test_match.dir/.hidden_test_match.file'),
     .../tests/treecopy_test_source.dir/test_match.dir/.hidden_test_no_match.file'),
     .../tests/treecopy_test_source.dir/test_match.dir/test_match.file'),
     .../tests/treecopy_test_source.dir/test_match.dir/test_match_file_noextension'),
     .../tests/treecopy_test_source.dir/test_match.dir/test_no_match.file'),
     .../tests/treecopy_test_source.dir/test_no_match.dir/.hidden_test_match.file'),
     .../tests/treecopy_test_source.dir/test_no_match.dir/.hidden_test_no_match.file'),
     .../tests/treecopy_test_source.dir/test_no_match.dir/test_match.file'),
     .../tests/treecopy_test_source.dir/test_no_match.dir/test_no_match.file')]

    >>> pp(sorted(list_paths_recursive_filtered(path_source_dir,['*_test_*'],['*no_match*']))) # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    [.../tests/treecopy_test_source.dir/.hidden_match.dir'),
     .../tests/treecopy_test_source.dir/.hidden_match.dir/.hidden_test_match.file'),
     .../tests/treecopy_test_source.dir/.hidden_match.dir/test_match.file'),
     .../tests/treecopy_test_source.dir/.hidden_match.file'),
     .../tests/treecopy_test_source.dir/test_empty.dir'),
     .../tests/treecopy_test_source.dir/test_empty2.dir'),
     .../tests/treecopy_test_source.dir/test_empty2.dir/test_empty.dir'),
     .../tests/treecopy_test_source.dir/test_match.dir'),
     .../tests/treecopy_test_source.dir/test_match.dir/.hidden_test_match.file'),
     .../tests/treecopy_test_source.dir/test_match.dir/test_match.file'),
     .../tests/treecopy_test_source.dir/test_match.dir/test_match_file_noextension')]

    >>> pp(sorted(list_paths_recursive_filtered(path_source_dir,['*/.hidden*/*'],['*_no_match*']))) # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    [.../tests/treecopy_test_source.dir/.hidden_match.dir/.hidden_test_match.file'),
     .../tests/treecopy_test_source.dir/.hidden_match.dir/test_match.file')]

    """

    path_base_dir = path_base_dir.resolve()
    lib_path.log_and_raise_if_path_does_not_exist(path_base_dir)
    lib_path.log_and_raise_if_not_isdir(path_base_dir)

    l_paths_all = list_paths_recursive(path_base_dir)
    l_paths_result = filter_path_objects(l_paths=l_paths_all, l_patterns_match=l_patterns_match, l_patterns_unmatch=l_patterns_unmatch)

    return l_paths_result


def filter_path_objects(l_paths: List[pathlib.Path], l_patterns_match: List[str] = None, l_patterns_unmatch: List[str] = None) -> List[pathlib.Path]:
    """
    # TODO IGNORE FILES
    # l_path_ignore_files = lib_ignore_files.get_l_nomatch_from_ignore_files(path_source_dir, ignore_file_name='.rotekignore')
    # l_path_sources = lib_list.l_substract_unsorted_fast(l_path_sources, l_path_ignore_files)

    """
    l_patterns_match = lib_parameter.get_default_if_none(l_patterns_match, default=['*'])
    l_patterns_unmatch = lib_parameter.get_default_if_none(l_patterns_unmatch, default=[])
    l_paths_match = list()
    l_paths_unmatch = list()

    for path_all in l_paths:
        for pattern_match in l_patterns_match:
            if fnmatch.fnmatch(path_all, pattern_match):
                l_paths_match.append(path_all)

    for path_match in l_paths_match:
        for pattern_unmatch in l_patterns_unmatch:
            if fnmatch.fnmatch(path_match, pattern_unmatch):
                l_paths_unmatch.append(path_match)

    # TODO IGNORE FILES
    # l_path_ignore_files = lib_ignore_files.get_l_nomatch_from_ignore_files(path_source_dir, ignore_file_name='.rotekignore')
    # l_path_sources = lib_list.l_substract_unsorted_fast(l_path_sources, l_path_ignore_files)

    l_paths_result = list(set(l_paths_match) - set(l_paths_unmatch))
    return l_paths_result


def copy_path_object_with_metadata(source: pathlib.Path, target: pathlib.Path, copy_empty_directories: bool = True):
    """
    copys a file object (directory of file), if possible with metadata

    >>> # Setup
    >>> path_test_dir = pathlib.Path(__file__).parent.parent / 'tests'
    >>> path_source_dir = path_test_dir / 'treecopy_test_source.dir'
    >>> path_target_dir = path_test_dir / 'treecopy_test_target.dir'
    >>> path_source_file = path_source_dir / 'test_match.dir/test_match.file'
    >>> path_target_file = path_target_dir / 'test_match.dir/test_match.file'
    >>> shutil.rmtree(str(path_target_dir), ignore_errors=True)

    >>> # do NOT copy empty directory
    >>> copy_path_object_with_metadata(path_source_dir, path_target_dir, copy_empty_directories = False)
    >>> assert not path_target_dir.exists()

    >>> # do copy empty directory
    >>> copy_path_object_with_metadata(path_source_dir, path_target_dir)
    >>> assert path_target_dir.is_dir()

    >>> # copy file
    >>> copy_path_object_with_metadata(path_source_file, path_target_file)
    >>> assert path_target_file.is_file()

    >>> # Teardown
    >>> shutil.rmtree(str(path_target_dir), ignore_errors=True)
    """

    # if it is a file:
    if source.is_file():
        lib_path.create_directory_if_not_exists(target.parent)
        shutil.copyfile(str(source), str(target))
        copy_metadata_of_path_object(source, target)

    # crate the directory if it is not there
    elif source.is_dir() and copy_empty_directories:
        lib_path.create_directory_if_not_exists(target)
        copy_metadata_of_path_object(source, target)


def expand_paths_subdirs_recursive(l_paths: List[pathlib.Path], expand_subdirs: bool = True) -> List[pathlib.Path]:
    """
    takes a mixed list of directories and files, and returns a list of files expanding the subdirectories
    >>> # Setup
    >>> from pprint import pp
    >>> test_dir = pathlib.Path(__file__).parent.parent / 'tests'
    >>> path_test_dir1 = test_dir / 'test_a/test_a_a'
    >>> path_test_dir2 = test_dir / 'test_a/test_a_b'
    >>> path_test_file1 = test_dir / 'test_a/file_test_a_1.txt'

    >>> # Test with expand Subdirs
    >>> l_files = expand_paths_subdirs_recursive([path_test_dir1, path_test_dir2, path_test_dir2, path_test_file1])
    >>> pp(l_files)  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    [.../tests/test_a/test_a_a/file_test_a_a_1.txt'),
     .../tests/test_a/test_a_b/file_test_a_b_2.txt'),
     .../tests/test_a/test_a_a/file_test_a_a_2.txt'),
     .../tests/test_a/test_a_a/.file_test_a_a_1.txt'),
     .../tests/test_a/test_a_b/.file_test_a_b_2.txt'),
     .../tests/test_a/file_test_a_1.txt'),
     .../tests/test_a/test_a_b/file_test_a_b_1.txt'),
     .../tests/test_a/test_a_b/.file_test_a_b_1.txt'),
     .../tests/test_a/test_a_a/.file_test_a_a_2.txt')]

    >>> # Test without expand Subdirs
    >>> l_files = expand_paths_subdirs_recursive([path_test_dir1, path_test_dir2, path_test_dir2, path_test_file1], expand_subdirs=False)
    >>> pp(l_files)  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    [.../tests/test_a/file_test_a_1.txt')]

    """

    l_path_files = list()

    for path in l_paths:
        path = path.resolve()
        if os.path.isfile(str(path)):
            l_path_files.append(path)
        elif os.path.isdir(str(path)) and expand_subdirs:
            l_path_files = l_path_files + list_files_recursive(path)

    l_path_files = list(set(l_path_files))    # deduplicate
    return l_path_files


def copy_metadata_of_path_object(source: pathlib.Path, target: pathlib.Path) -> None:
    try:
        shutil.copystat(str(source), str(target))
    except Exception:
        pass


def remove_empty_folders_recursive(path_base_dir: pathlib.Path) -> None:
    """
    delete all empty folders - recursively, including the basedir if empty
    /folder/empty_folder1/empty_folder2 --> /folder

    >>> # Setup
    >>> path_test_dir = pathlib.Path(__file__).parent.parent / 'tests'
    >>> path_empty_folder_test_source = path_test_dir / 'empty_folder_test_source'
    >>> path_empty_folder_test_target = path_test_dir / 'empty_folder_test_target'
    >>> copy_files_recursive_filtered(path_empty_folder_test_source, path_empty_folder_test_target)

    >>> # TEST
    >>> remove_empty_folders_recursive(path_empty_folder_test_target)
    >>> assert len(list(path_empty_folder_test_target.glob('**/'))) == 2

    >>> # Teardown
    >>> shutil.rmtree(str(path_empty_folder_test_target), ignore_errors=True)

    """
    path_base_dir = path_base_dir.resolve()
    lib_path.log_and_raise_if_path_does_not_exist(path_base_dir)
    lib_path.log_and_raise_if_not_isdir(path_base_dir)

    lib_path.log_and_raise_if_not_isdir(pathlib.Path(path_base_dir))
    l_path_folders = sorted(list_dirs_recursive(path_base_dir), reverse=True)
    for path_folder in l_path_folders:
        if lib_path.is_directory_empty(path_folder):
            path_folder.rmdir()


def remove_folders_recursive(path_base_dir: pathlib.Path, l_patterns_match: List[str] = None, l_patterns_nomatch: List[str] = None):
    """
    Löscht alle Verzeichnisse welche den Suchkriterien entsprechen rekursiv vom Basisverzeichnis aus, auch wenn diese nicht leer sind.
    Es dürfen auch Verzeichnisnamen und Wildcards in den Filtern verwendet werden. ls_patterns_nomatch übersteuert ls_patterns_match

    the patterns matches directory names, not files !

    z.Bsp. alle Unterverzeichnisse löschen bis auf das */doc/* (alle Unterverzeichnisse unter */doc werden nicht gelöscht):
    rnlib.remove_folders_recursive('c:/test2',ls_patterns_match=['*'], ls_patterns_nomatch=['*/doc/*'])

    ls_patterns_match:   eine Liste an Matchstrings, z.Bsp. ['*.py'] - alle Verzeichnisse die Matchen werden gelöscht
    ls_patterns_nomatch: eine Liste an Matchstrings, z.Bsp. ['*.doc'] - alle Verzeichnisse die Matchen werden NICHT gelöscht

    >>> # Setup
    >>> import unittest
    >>> import pprint
    >>> path_test_dir = pathlib.Path(__file__).parent.parent / 'tests'
    >>> path_source_dir = path_test_dir / 'treecopy_test_source.dir'
    >>> path_target_dir = path_test_dir / 'treecopy_test_target.dir'
    >>> shutil.rmtree(str(path_target_dir),ignore_errors=True)

    >>> # Delete all
    >>> copy_files_recursive_filtered(path_source_dir, path_target_dir)
    >>> assert len(list(path_target_dir.rglob('*'))) == 26
    >>> remove_folders_recursive(path_target_dir)
    >>> assert len(list(path_target_dir.rglob('*'))) == 0
    >>> assert not path_target_dir.exists()

    >>> # Delete "*/.hidden*" exclusive *_test_match.file
    >>> copy_files_recursive_filtered(path_source_dir, path_target_dir)
    >>> pprint.pp(sorted(list(path_target_dir.glob('**/'))))  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    [.../tests/treecopy_test_target.dir'),
     .../tests/treecopy_test_target.dir/.hidden_match.dir'),
     .../tests/treecopy_test_target.dir/.hidden_no_match.dir'),
     .../tests/treecopy_test_target.dir/test_empty.dir'),
     .../tests/treecopy_test_target.dir/test_empty2.dir'),
     .../tests/treecopy_test_target.dir/test_empty2.dir/test_empty.dir'),
     .../tests/treecopy_test_target.dir/test_match.dir'),
     .../tests/treecopy_test_target.dir/test_no_match.dir')]

    >>> remove_folders_recursive(path_target_dir, ['*'], ['*/.hidden*'])
    >>> pprint.pp(sorted(list(path_target_dir.glob('**/'))))  # doctest: +ELLIPSIS +NORMALIZE_WHITESPACE
    [.../tests/treecopy_test_target.dir'),
     .../tests/treecopy_test_target.dir/.hidden_match.dir'),
     .../tests/treecopy_test_target.dir/.hidden_no_match.dir')]

    >>> # Teardown
    >>> shutil.rmtree(str(path_target_dir),ignore_errors=True)

    """

    base_dir = path_base_dir.resolve()
    lib_path.log_and_raise_if_path_does_not_exist(pathlib.Path(base_dir))
    lib_path.log_and_raise_if_not_isdir(pathlib.Path(base_dir))

    if len(base_dir.parts) < 2:
        raise RuntimeError('Sie wollen von "{}" alle Unterverzeichnisse löschen - zu gefährlich, Notbremse'.format(base_dir))

    # alle Folder die matchen dem Ergebnis hinzufügen
    l_path_dirs = list_dirs_recursive_filtered(path_base_dir=base_dir, l_patterns_match=l_patterns_match, l_patterns_unmatch=l_patterns_nomatch)
    l_path_dirs = sorted(l_path_dirs, reverse=True)
    for path_dir in l_path_dirs:
        if not lib_path.has_subdirs(path_dir):
            shutil.rmtree(path_dir, ignore_errors=True)
