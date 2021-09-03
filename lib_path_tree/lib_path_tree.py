# STDLIB
from concurrent.futures import ThreadPoolExecutor
import fnmatch
import os
import pathlib
import shutil
from typing import Any, Callable, Iterator, List, Optional, Set, Union

# OWN
import igittigitt
import lib_parameter
import lib_path
import pathlib3x


def copy_tree_fnmatch_new(path_source_dir: pathlib.Path,
                          path_target_dir: pathlib.Path,
                          patterns_fn_match: Optional[List[str]] = None,
                          patterns_fn_unmatch: Optional[List[str]] = None,
                          gitignore_filenames: Optional[List[str]] = None,
                          create_empty_directories: bool = True,
                          threaded: bool = True):

    """
    copy files and directories recursively, using match/unmatch patterns


    Parameter
    ---------
    path_source_dir
        the source directory
    path_target_dir
        the target directory
    patterns_fn_match
        patterns to match, default = ['*']
    patterns_fn_unmatch
        patterns to unmatch, default = [] - this wins over the 'match' pattern
    gitignore_filenames
        a list of ignorefile names, which will be parsed recursively from the source directory
        ignorefiles in already ignored directories will not be considered
        default = '.gitignore'
    create_empty_directories
        create empty directories in target

    Exceptions
    ----------
    NotADirectoryError
        when the source directory does not exist
    RunTimeError
       if the target directory is within the source directory

    Examples
    ----------

    >>> # Setup
    >>> import unittest
    >>> import pprint
    >>> path_test_dir = pathlib.Path(__file__).parent.parent / 'tests'
    >>> p_bad_source_dir = pathlib.Path('./does/not/exist')
    >>> p_source_dir = path_test_dir / 'treecopy_test_source.dir'
    >>> p_target_dir = path_test_dir / 'treecopy_test_target.dir'
    >>> targets_match=['*/.hidden*/*']
    >>> targets_unmatch=['*_no_match*']
    >>> shutil.rmtree(str(p_target_dir),ignore_errors=True)

    >>> # test source does not exist
    >>> unittest.TestCase().assertRaises(NotADirectoryError, copy_tree_fnmatch, path_source_dir=p_bad_source_dir, path_target_dir=p_target_dir)

    >>> # test target dir within source dir
    >>> unittest.TestCase().assertRaises(NotADirectoryError, copy_tree_fnmatch, path_source_dir=p_target_dir, path_target_dir=path_test_dir)

    >>> # test copy all
    >>> shutil.rmtree(str(p_target_dir),ignore_errors=True)
    >>> copy_tree_fnmatch(p_source_dir, p_target_dir)
    >>> assert len(list(p_target_dir.rglob('*'))) == 26

    >>> # test copy some with match / unmatch
    >>> shutil.rmtree(str(p_target_dir),ignore_errors=True)
    >>> copy_tree_fnmatch(p_source_dir, p_target_dir, targets_match, targets_unmatch)
    >>> pprint.pp(sorted(list(p_target_dir.rglob('*'))))
    [.../tests/treecopy_test_target.dir/.hidden_match.dir'),
     .../tests/treecopy_test_target.dir/.hidden_match.dir/.hidden_test_match.file'),
     .../tests/treecopy_test_target.dir/.hidden_match.dir/test_match.file')]

    >>> assert len(list(p_target_dir.rglob('*'))) == 3

    >>> # Teardown
    >>> shutil.rmtree(str(p_target_dir),ignore_errors=True)


    >>> import decorator_timeit
    >>> # timeit with test directory
    >>> result = decorator_timeit.TimeIt(repeat=100)(copy_tree_fnmatch)(p_source_dir, p_target_dir, targets_match, targets_unmatch, threaded=False)
    >>> result2 = decorator_timeit.TimeIt(repeat=100)(copy_tree_fnmatch)(p_source_dir, p_target_dir, targets_match, targets_unmatch, threaded=True)


    """

    patterns_fn_match = lib_parameter.get_default_if_none(patterns_fn_match, default=['*'])
    patterns_fn_unmatch = lib_parameter.get_default_if_none(patterns_fn_unmatch, default=[])
    gitignore_filenames = lib_parameter.get_default_if_none(gitignore_filenames, default=['.gitignore'])
    path_source_dir = path_source_dir.resolve()
    path_target_dir = path_target_dir.resolve()
    lib_path.log_and_raise_if_not_isdir(path_source_dir)
    lib_path.log_and_raise_if_target_directory_within_source_directory(path_source_dir, path_target_dir)

    gitignore_parser = igittigitt.IgnoreParser()












    path_sources = get_tree_path_fnmatch(path_source_dir, patterns_fn_match, patterns_fn_unmatch)

    if threaded:
        with ThreadPoolExecutor(max_workers=2) as tp:
            for path_source in path_sources:
                path_target = pathlib.Path(str(path_source).replace(str(path_source_dir), str(path_target_dir), 1))
                tp.submit(copy_path_object_with_metadata, path_source, path_target, create_empty_directories)
    else:
        for path_source in path_sources:
            path_target = pathlib.Path(str(path_source).replace(str(path_source_dir), str(path_target_dir), 1))
            copy_path_object_with_metadata(path_source, path_target, create_empty_directories)


def copy_tree_fnmatch(path_source_dir: pathlib.Path,
                      path_target_dir: pathlib.Path,
                      patterns_fn_match: List[str] = None,
                      patterns_fn_unmatch: List[str] = None,
                      create_empty_directories: bool = True,
                      threaded: bool = True):
    """
    copy files and directories recursively, using match/unmatch patterns


    Parameter
    ---------
    path_source_dir
        the source directory
    path_target_dir
        the target directory
    patterns_fn_match
        patterns to match, default = ['*']
    patterns_fn_unmatch
        patterns to unmatch, default = [] - this wins over the 'match' pattern
    create_empty_directories
        create empty directories in target

    Exceptions
    ----------
    NotADirectoryError
        when the source directory does not exist
    RunTimeError
       if the target directory is within the source directory

    Examples
    ----------

    >>> # Setup
    >>> import unittest
    >>> import pprint
    >>> path_test_dir = pathlib.Path(__file__).parent.parent / 'tests'
    >>> p_bad_source_dir = pathlib.Path('./does/not/exist')
    >>> p_source_dir = path_test_dir / 'treecopy_test_source.dir'
    >>> p_target_dir = path_test_dir / 'treecopy_test_target.dir'
    >>> targets_match=['*/.hidden*/*']
    >>> targets_unmatch=['*_no_match*']
    >>> shutil.rmtree(str(p_target_dir),ignore_errors=True)

    >>> # test source does not exist
    >>> unittest.TestCase().assertRaises(NotADirectoryError, copy_tree_fnmatch, path_source_dir=p_bad_source_dir, path_target_dir=p_target_dir)

    >>> # test target dir within source dir
    >>> unittest.TestCase().assertRaises(NotADirectoryError, copy_tree_fnmatch, path_source_dir=p_target_dir, path_target_dir=path_test_dir)

    >>> # test copy all
    >>> shutil.rmtree(str(p_target_dir),ignore_errors=True)
    >>> copy_tree_fnmatch(p_source_dir, p_target_dir)
    >>> assert len(list(p_target_dir.rglob('*'))) == 26

    >>> # test copy some with match / unmatch
    >>> shutil.rmtree(str(p_target_dir),ignore_errors=True)
    >>> copy_tree_fnmatch(p_source_dir, p_target_dir, targets_match, targets_unmatch)
    >>> pprint.pp(sorted(list(p_target_dir.rglob('*'))))
    [.../tests/treecopy_test_target.dir/.hidden_match.dir'),
     .../tests/treecopy_test_target.dir/.hidden_match.dir/.hidden_test_match.file'),
     .../tests/treecopy_test_target.dir/.hidden_match.dir/test_match.file')]

    >>> assert len(list(p_target_dir.rglob('*'))) == 3

    >>> # Teardown
    >>> shutil.rmtree(str(p_target_dir),ignore_errors=True)


    >>> import decorator_timeit
    >>> # timeit with test directory
    >>> result = decorator_timeit.TimeIt(repeat=100)(copy_tree_fnmatch)(p_source_dir, p_target_dir, targets_match, targets_unmatch, threaded=False)
    >>> result2 = decorator_timeit.TimeIt(repeat=100)(copy_tree_fnmatch)(p_source_dir, p_target_dir, targets_match, targets_unmatch, threaded=True)


    """

    patterns_fn_match = lib_parameter.get_default_if_none(patterns_fn_match, default=['*'])
    patterns_fn_unmatch = lib_parameter.get_default_if_none(patterns_fn_unmatch, default=[])
    path_source_dir = path_source_dir.resolve()
    path_target_dir = path_target_dir.resolve()
    lib_path.log_and_raise_if_not_isdir(path_source_dir)
    lib_path.log_and_raise_if_target_directory_within_source_directory(path_source_dir, path_target_dir)
    path_sources = get_tree_path_fnmatch(path_source_dir, patterns_fn_match, patterns_fn_unmatch)

    if threaded:
        with ThreadPoolExecutor(max_workers=2) as tp:
            for path_source in path_sources:
                path_target = pathlib.Path(str(path_source).replace(str(path_source_dir), str(path_target_dir), 1))
                tp.submit(copy_path_object_with_metadata, path_source, path_target, create_empty_directories)
    else:
        for path_source in path_sources:
            path_target = pathlib.Path(str(path_source).replace(str(path_source_dir), str(path_target_dir), 1))
            copy_path_object_with_metadata(path_source, path_target, create_empty_directories)


def get_tree_dirs(path_base_dir: pathlib.Path) -> Iterator[pathlib.Path]:
    """
    get all directories under the base directory, recursive. Includes also dotted directories

    Parameter
    ---------
    path_base_dir
        the base directory

    Examples
    --------

    >>> # Setup
    >>> from pprint import pp
    >>> path_test_dir = pathlib.Path(__file__).parent.parent / 'tests'
    >>> path_source_dir = path_test_dir / 'treecopy_test_source.dir'

    >>> # test
    >>> pp(sorted(get_tree_dirs(path_source_dir)))
    [.../tests/treecopy_test_source.dir'),
     .../tests/treecopy_test_source.dir/.hidden_match.dir'),
     ...
     .../tests/treecopy_test_source.dir/test_match.dir'),
     .../tests/treecopy_test_source.dir/test_no_match.dir')]

    """

    path_base_dir = path_base_dir.resolve()
    lib_path.log_and_raise_if_not_isdir(path_base_dir)

    # we use os.walk because it is 3 x faster then pathlib.Path('.').rglob(*)
    # and oddly pathlib.Path('.').rglob(*) fails on windows on samba share (sometimes)
    yield pathlib.Path(path_base_dir)
    for root, dirs, files in os.walk(str(path_base_dir), topdown=False):
        for s_dir in dirs:
            path_dir = pathlib.Path(root) / s_dir
            yield path_dir


def get_tree_dirs_fnmatch(path_base_dir: pathlib.Path,
                          patterns_fn_match: List[str] = None,
                          patterns_fn_unmatch: List[str] = None) -> Iterator[pathlib.Path]:
    """
    all directories recursive from the base directory (including the base directory itself)
    which matches / unmatches the given patterns

    Parameter
    ---------
    path_base_dir
        the base directory
    patterns_fn_match
        patterns to match, default = ['*']
    patterns_fn_unmatch
        patterns to unmatch, default = [] - this wins over the 'match' pattern


    Examples
    --------

    >>> # Setup
    >>> from pprint import pp
    >>> path_test_dir = pathlib.Path(__file__).parent.parent / 'tests'
    >>> path_source_dir = path_test_dir / 'treecopy_test_source.dir'

    >>> pp(sorted(get_tree_dirs_fnmatch(path_source_dir,['*/test*'],[])))
    [.../tests/treecopy_test_source.dir'),
     .../tests/treecopy_test_source.dir/.hidden_match.dir'),
     ...
     .../tests/treecopy_test_source.dir/test_match.dir'),
     .../tests/treecopy_test_source.dir/test_no_match.dir')]

    >>> pp(sorted(get_tree_dirs_fnmatch(path_source_dir,['*/test*'],['*no_match*'])))
    [.../tests/treecopy_test_source.dir'),
     .../tests/treecopy_test_source.dir/.hidden_match.dir'),
     ...
     .../tests/treecopy_test_source.dir/test_empty2.dir/test_empty.dir'),
     .../tests/treecopy_test_source.dir/test_match.dir')]

    >>> pp(sorted(get_tree_dirs_fnmatch(path_source_dir,['*/test*'],['*/.hidden*'])))
    [.../tests/treecopy_test_source.dir'),
     .../tests/treecopy_test_source.dir/test_empty.dir'),
     ...
     .../tests/treecopy_test_source.dir/test_match.dir'),
     .../tests/treecopy_test_source.dir/test_no_match.dir')]

    """
    path_base_dir = path_base_dir.resolve()
    lib_path.log_and_raise_if_path_does_not_exist(path_base_dir)
    lib_path.log_and_raise_if_not_isdir(path_base_dir)

    l_paths_all = get_tree_dirs(path_base_dir)
    l_paths_result = filter_path_objects_fnmatch(paths=l_paths_all, patterns_fn_match=patterns_fn_match, patterns_fn_unmatch=patterns_fn_unmatch)

    return l_paths_result


def get_tree_files(path_base_dir: pathlib.Path) -> Iterator[pathlib.Path]:
    """
    get all files (not directories) under the base directory, recursive. Includes also dotted files in dotted directories


    Parameter
    ---------
    path_base_dir
        the base directory


    Examples
    --------

    >>> # Setup
    >>> import timeit
    >>> from pprint import pp
    >>> path_test_dir = pathlib.Path(__file__).parent.parent / 'tests'
    >>> path_source_dir = path_test_dir / 'treecopy_test_source.dir'
    >>> pp(sorted(get_tree_files(path_source_dir)))
    [.../tests/treecopy_test_source.dir/.hidden_match.dir/.hidden_test_match.file'),
     .../tests/treecopy_test_source.dir/.hidden_match.dir/.hidden_test_no_match.file'),
     ...
     .../tests/treecopy_test_source.dir/test_no_match.dir/test_match.file'),
     .../tests/treecopy_test_source.dir/test_no_match.dir/test_no_match.file')]

    """

    path_base_dir = path_base_dir.resolve()
    lib_path.log_and_raise_if_not_isdir(path_base_dir)

    # we use os.walk because it is 3 x faster then pathlib.Path('.').rglob(*)
    # and oddly pathlib.Path('.').rglob(*) fails on windows on samba share (sometimes)
    for root, dirs, files in os.walk(str(path_base_dir), topdown=False):
        for name in files:
            path_file = pathlib.Path(root) / name
            yield path_file


def get_tree_path_fnmatch(path_base_dir: pathlib.Path,
                          patterns_fn_match: List[str] = None,
                          patterns_fn_unmatch: List[str] = None) -> Iterator[pathlib.Path]:
    """
    all path objects (directories and files)from the base directory (including the base directory itself)
    which matches / unmatches the given patterns


    Parameter
    ---------
    path_base_dir
        the base directory
    patterns_fn_match
        patterns to match, default = ['*']
    patterns_fn_unmatch
        patterns to unmatch, default = [] - this wins over the 'match' pattern


    Examples
    --------

    >>> # Setup
    >>> from pprint import pp
    >>> path_test_dir = pathlib.Path(__file__).parent.parent / 'tests'
    >>> path_source_dir = path_test_dir / 'treecopy_test_source.dir'

    >>> pp(sorted(get_tree_path_fnmatch(path_source_dir,['*match*/*'],[])))
    [.../tests/treecopy_test_source.dir/.hidden_match.dir/.hidden_test_match.file'),
     .../tests/treecopy_test_source.dir/.hidden_match.dir/.hidden_test_no_match.file'),
     ...
     .../tests/treecopy_test_source.dir/test_no_match.dir/test_match.file'),
     .../tests/treecopy_test_source.dir/test_no_match.dir/test_no_match.file')]

    >>> pp(sorted(get_tree_path_fnmatch(path_source_dir,['*_test_*'],['*no_match*'])))
    [.../tests/treecopy_test_source.dir/.hidden_match.dir'),
     .../tests/treecopy_test_source.dir/.hidden_match.dir/.hidden_test_match.file'),
     ...
     .../tests/treecopy_test_source.dir/test_match.dir/test_match.file'),
     .../tests/treecopy_test_source.dir/test_match.dir/test_match_file_noextension')]

    >>> pp(sorted(get_tree_path_fnmatch(path_source_dir,['*/.hidden*/*'],['*_no_match*'])))
    [.../tests/treecopy_test_source.dir/.hidden_match.dir/.hidden_test_match.file'),
     .../tests/treecopy_test_source.dir/.hidden_match.dir/test_match.file')]

    """

    path_base_dir = path_base_dir.resolve()
    lib_path.log_and_raise_if_path_does_not_exist(path_base_dir)
    lib_path.log_and_raise_if_not_isdir(path_base_dir)

    l_paths_all = get_path_recursive(path_base_dir)
    l_paths_result = filter_path_objects_fnmatch(paths=l_paths_all, patterns_fn_match=patterns_fn_match, patterns_fn_unmatch=patterns_fn_unmatch)

    return l_paths_result


def filter_path_objects_fnmatch(paths: Union[List[pathlib.Path], Iterator[pathlib.Path]],
                                patterns_fn_match: List[str] = None,
                                patterns_fn_unmatch: List[str] = None) -> Iterator[pathlib.Path]:
    """
    filters the given paths which matches / unmatches the given patterns


    Parameter
    ---------
    paths
        the path objects to filter
    patterns_fn_match
        patterns to match, default = ['*']
    patterns_fn_unmatch
        patterns to unmatch, default = [] - this wins over the 'match' pattern

    Examples
    --------

    >>> test_paths = [pathlib.Path('test.txt'), pathlib.Path('test.hlp')]
    >>> list(filter_path_objects_fnmatch(test_paths, ['*'], ['*.hlp']))
    [...Path('test.txt')]

    """
    patterns_fn_match = lib_parameter.get_default_if_none(patterns_fn_match, default=['*'])
    patterns_fn_unmatch = lib_parameter.get_default_if_none(patterns_fn_unmatch, default=[])

    for path in paths:
        if does_path_fnmatch_patterns(path, patterns_fn_match):
            if does_path_fnmatch_patterns(path, patterns_fn_unmatch):
                continue
            yield path


def does_path_fnmatch_patterns(path: pathlib.Path, patterns_fn_match: List[str]) -> bool:
    """
    Return True if path matches the fn_match pattern


    Parameter
    ---------
    path
        the path objects to filter
    patterns_fn_match
        patterns to match, default = ['*']


    Examples
    --------

    >>> assert does_path_fnmatch_patterns(pathlib.Path('test.txt'), ['*'])
    >>> assert not does_path_fnmatch_patterns(pathlib.Path('test.txt'), ['*.hlp'])
    """
    for pattern in patterns_fn_match:
        if fnmatch.fnmatch(path, pattern):
            return True
    return False


def get_path_recursive(path_base_dir: pathlib.Path) -> Iterator[pathlib.Path]:
    """
    get all files and directories (including tha base directory) under the base directory, recursive.
    Includes also dotted files in dotted directories


    Parameter
    ---------
    path_base_dir
        the base directory


    Examples
    --------

    >>> # Setup
    >>> import timeit
    >>> from pprint import pp
    >>> path_test_dir = pathlib.Path(__file__).parent.parent / 'tests'
    >>> path_source_dir = path_test_dir / 'treecopy_test_source.dir'
    >>> pp(sorted(get_path_recursive(path_source_dir)))
    [.../tests/treecopy_test_source.dir'),
     .../tests/treecopy_test_source.dir/.hidden_match.dir'),
     ...
     .../tests/treecopy_test_source.dir/test_no_match.dir/test_match.file'),
     .../tests/treecopy_test_source.dir/test_no_match.dir/test_no_match.file')]

    """

    path_base_dir = path_base_dir.resolve()
    lib_path.log_and_raise_if_not_isdir(path_base_dir)

    # we use os.walk because it is 3 x faster then pathlib.Path('.').rglob(*)
    # and oddly pathlib.Path('.').rglob(*) fails on windows on samba share (sometimes)

    yield path_base_dir
    for root, dirs, files in os.walk(str(path_base_dir), topdown=False):
        for s_dir in dirs:
            path_dir = pathlib.Path(root) / s_dir
            yield path_dir
        for name in files:
            path_file = pathlib.Path(root) / name
            yield path_file


def copy_path_object_with_metadata(path_source: pathlib.Path, path_target: pathlib.Path, copy_empty_directories: bool = True):
    """
    copys a file object (directory of file), if possible with metadata

    when copy from samba share to windows machine, some files appeared on the windows machine as directories.
    in that case see https://askubuntu.com/questions/1288678/some-files-on-samba-shares-are-displayed-as-folders
    delete the DOSATTRIB on the Samba Server, and probably disable them on the server :

    - show samba file attributes   : sudo getfattr <filename>
    - remove samba file attributes : sudo setfattr -x user.DOSATTRIB <filename>
    - remove samba file attributes recursively:
        cd <directory on the samba server>
        find . -type f -exec setfattr -x user.DOSATTRIB "{}" \;

    Parameter
    ---------
    path_source
        the source path object
    path_target
        the target path object
    copy_empty_directories
        if to copy empty directories

    Examples
    --------

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

    # if it is a directory:
    if path_source.is_dir():
        if copy_empty_directories:
            pathlib3x.Path(path_target).mkdir(parents=True, exist_ok=True)
            copy_metadata_of_path_object(path_source, path_target)

    else:  # it is a file
        pathlib3x.Path(path_target).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path_source, path_target)


def expand_paths_subdirs_recursive(paths: List[pathlib.Path], expand_subdirs: bool = True) -> List[pathlib.Path]:
    """
    takes a mixed list of directories and files, and returns a list of files expanding the subdirectories
    this is used to expand path objects dropped onto an icon

    Parameter
    ---------
    paths
        mixed list of path objects (files and directories)
    expand_subdirs
        by default directories will be expanded

    Examples
    --------


    >>> # Setup
    >>> from pprint import pp
    >>> test_dir = pathlib.Path(__file__).parent.parent / 'tests'
    >>> path_test_dir1 = test_dir / 'test_a/test_a_a'
    >>> path_test_dir2 = test_dir / 'test_a/test_a_b'
    >>> path_test_file1 = test_dir / 'test_a/file_test_a_1.txt'

    >>> # Test with expand Subdirs
    >>> l_files = expand_paths_subdirs_recursive([path_test_dir1, path_test_dir2, path_test_dir2, path_test_file1])
    >>> pp(sorted(l_files))
    [.../tests/test_a/file_test_a_1.txt'),
     .../tests/test_a/test_a_a/.file_test_a_a_1.txt'),
     ...
     .../tests/test_a/test_a_b/file_test_a_b_1.txt'),
     .../tests/test_a/test_a_b/file_test_a_b_2.txt')]

    >>> # Test without expand Subdirs
    >>> l_files = expand_paths_subdirs_recursive([path_test_dir1, path_test_dir2, path_test_dir2, path_test_file1], expand_subdirs=False)
    >>> pp(l_files)
    [.../tests/test_a/file_test_a_1.txt')]

    """

    l_path_files = list()

    for path in paths:
        path = path.resolve()
        if os.path.isfile(str(path)):
            l_path_files.append(path)
        elif os.path.isdir(str(path)) and expand_subdirs:
            l_path_files = l_path_files + list(get_tree_files(path))

    l_path_files = list(set(l_path_files))    # deduplicate
    return l_path_files


def copy_metadata_of_path_object(source: pathlib.Path, target: pathlib.Path) -> None:
    """
    copy the metadata - used for directories

    Parameter
    ---------
    source
        the source object
    target
        the target object

    """
    try:
        shutil.copystat(str(source), str(target))
    except Exception:       # noqa
        pass


def remove_empty_folders_recursive(path_base_dir: pathlib.Path) -> None:
    """
    delete all empty folders - recursively, including the basedir if empty


    Parameter
    ---------
    path_base_dir
        the base directory

    Examples
    --------

    >>> # Setup
    >>> path_test_dir = pathlib.Path(__file__).parent.parent / 'tests'
    >>> path_empty_folder_test_source = path_test_dir / 'empty_folder_test_source'
    >>> path_empty_folder_test_target = path_test_dir / 'empty_folder_test_target'
    >>> copy_tree_fnmatch(path_empty_folder_test_source, path_empty_folder_test_target)

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
    l_path_folders = sorted(get_tree_dirs(path_base_dir), reverse=True)
    for path_folder in l_path_folders:
        if lib_path.is_directory_empty(path_folder):
            path_folder.rmdir()


def remove_folders_recursive_fnmatch(path_base_dir: pathlib.Path,
                                     patterns_fn_match: List[str] = None,
                                     patterns_fn_unmatch: List[str] = None,
                                     minimal_depth: int = 1):
    """
    delete directoriers from base directory, even if they are not empty.
    match and nomatch filters apply, that means a directory will not be removed if a subdirectory matches the nomatch rule

    Parameter
    ---------
    path_base_dir
        the base directory
    patterns_fn_match
        the patterns to match, default = ['*'], the patterns matches directory names, not files
    patterns_fn_unmatch
        the patterns to unmatch, default = [], the patterns matches directory names, not files
    minimal_depth
        the minimal depth from the base dir relative to root.
        if minimal_depth == 0, You can delete subfolders of the root folder
        id minimal_depth == 1, You can delete subfolders of /<folder>/... etc.
        this might prevent accidential deleting of folders

    Examples
    --------

    >>> # Setup
    >>> import unittest
    >>> import pprint
    >>> path_test_dir = pathlib.Path(__file__).parent.parent / 'tests'
    >>> path_source_dir = path_test_dir / 'treecopy_test_source.dir'
    >>> path_target_dir = path_test_dir / 'treecopy_test_target.dir'
    >>> shutil.rmtree(str(path_target_dir),ignore_errors=True)

    >>> # Delete all
    >>> copy_tree_fnmatch(path_source_dir, path_target_dir)
    >>> assert len(list(path_target_dir.rglob('*'))) == 26
    >>> remove_folders_recursive_fnmatch(path_target_dir)
    >>> assert len(list(path_target_dir.rglob('*'))) == 0
    >>> assert not path_target_dir.exists()

    >>> # Delete "*/.hidden*" exclusive *_test_match.file
    >>> copy_tree_fnmatch(path_source_dir, path_target_dir)
    >>> pprint.pp(sorted(list(path_target_dir.glob('**/'))))
    [.../tests/treecopy_test_target.dir'),
     .../tests/treecopy_test_target.dir/.hidden_match.dir'),
     .../tests/treecopy_test_target.dir/.hidden_no_match.dir'),
     .../tests/treecopy_test_target.dir/test_empty.dir'),
     .../tests/treecopy_test_target.dir/test_empty2.dir'),
     .../tests/treecopy_test_target.dir/test_empty2.dir/test_empty.dir'),
     .../tests/treecopy_test_target.dir/test_match.dir'),
     .../tests/treecopy_test_target.dir/test_no_match.dir')]

    >>> remove_folders_recursive_fnmatch(path_target_dir, ['*'], ['*/.hidden*'])
    >>> pprint.pp(sorted(list(path_target_dir.glob('**/'))))
    [.../tests/treecopy_test_target.dir'),
     .../tests/treecopy_test_target.dir/.hidden_match.dir'),
     .../tests/treecopy_test_target.dir/.hidden_no_match.dir')]

    >>> # provoke too shallow
    >>> remove_folders_recursive_fnmatch(path_target_dir, ['*'], ['*/.hidden*'], minimal_depth=42)
    Traceback (most recent call last):
        ...
    RuntimeError: you want to delete subfolders from "...tests/treecopy_test_target.dir" - minimal depth setting "42" prevents that

    >>> # Teardown
    >>> shutil.rmtree(str(path_target_dir),ignore_errors=True)

    """

    base_dir = path_base_dir.resolve()
    lib_path.log_and_raise_if_path_does_not_exist(pathlib.Path(base_dir))
    lib_path.log_and_raise_if_not_isdir(pathlib.Path(base_dir))

    if len(base_dir.parts) < minimal_depth + 1 :
        raise RuntimeError('you want to delete subfolders from "{}" - minimal depth setting "{}" prevents that'.format(base_dir, minimal_depth))

    # alle Folder die matchen dem Ergebnis hinzufügen
    l_path_dirs = get_tree_dirs_fnmatch(path_base_dir=base_dir, patterns_fn_match=patterns_fn_match, patterns_fn_unmatch=patterns_fn_unmatch)
    l_path_dirs = sorted(l_path_dirs, reverse=True)
    for path_dir in l_path_dirs:
        if not lib_path.has_subdirs(path_dir):
            shutil.rmtree(path_dir, ignore_errors=True)


def get_paths_gitignore_files(path_base_dir: pathlib.Path, ignore_file_names: Optional[List[str]] = None) -> List[pathlib.Path]:
    """
    find and return all ignore filenames recursive under the base directory


    Parameter
    ---------
    path_base_dir
        the base directory
    ignore_file_namess
        the filenames of the ignore files as string


    Examples
    --------


    >>> # Setup
    >>> path_test_dir = pathlib.Path(__file__).parent.parent.resolve() / 'tests/test_ignores'
    >>> test_path_base_dir = path_test_dir
    >>> test_ignore_file_names = ['.rotekignore']

    >>> # Test
    >>> list(get_paths_gitignore_files(path_base_dir=test_path_base_dir, ignore_file_names=test_ignore_file_names))
    [.../dir_test2/.rotekignore'), .../test_ignores/.rotekignore')]


    """
    ignore_file_names = lib_parameter.get_default_if_none(ignore_file_names, ['.gitignore'])

    gitignore_files: List[pathlib.Path] = list()
    for ignore_file_name in ignore_file_names:
        gitignore_files = gitignore_files + list(get_tree_path_fnmatch(path_base_dir, ['*/' + ignore_file_name]))
    return gitignore_files
