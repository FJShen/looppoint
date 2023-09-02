#!/usr/bin/python3

from pathlib import Path
import glob
import re

def _find_eligible_global_pinpoints_csv_file(path: Path):
    files = glob.glob(path.as_posix() + "/*.Data/*global.pinpoints.csv")
    return files

def _read_global_csv_file(file_path: Path):
    with open(file_path, "r") as f:
        contents = f.read()
    return contents


def _extract_single_region_from_global_s(s: str):
    """
    If `s` still contains a region, extract the region, and return a tuple of three
    strings:
    1. `s` minus the extracted region
    2. The extract region
    3. The region id
    Else if `s` is depleted of regions, return the tuple:
    1. `s` without change
    2. None
    3. None
    """    
    # first, get an region id still in the file
    regex_pattern_1 = re.compile(
        "(# Regions based on.*\n\n)"\
        "(# comment,.*\n\n)"\
        "(# RegionId = (?P<region_id>\d+) .*\n.*\n.*\n.*\n)"
        , re.M
    )
    match = regex_pattern_1.match(s)
    if not match: 
        return (s, None, None)
    region_id = match.group("region_id")
    
    # Then, dynamically generate a regex pattern to cast onto the entire string.
    # This will be a fullmatch, hence we need to specify start-of-line (^) and
    # end-of-line ($) in each line.
    # This stupid repitition of doing two regex matches per invocation is due to
    # group referencing not correctly working on the multi-line string
    regex_pattern_2 = re.compile(
        "(?P<header_1>^# Regions based on.*$\n\n)"\
        "(?P<header_2>^# comment,.*$\n\n)"\
        f"(?P<region_roi>^# RegionId = {region_id} .*$\n^.*$\n^.*$\n^.*$\n(^$\n)*)"\
        "(?P<middle_text>(^.*$\n)*)"\
        f"(?P<region_warmup>(^.*$\n^.*$\n^.*$\n^Warmup for regionid {region_id},.*$\n(^$\n)*)|(^# No warmup possible for regionid {region_id}.*$\n(^$\n)*))"\
        "(?P<trailing_text>(^.*$\n)*)"
        ,re.M
    )
    match2 = regex_pattern_2.fullmatch(s)
    if not match2:
        return (s, None, None)
    else:
        # perform the extraction
        region_str = match2.group("region_roi") + match2.group("region_warmup") 
        remaining_str = match2.group("header_1") + match2.group("header_2") + match2.group("middle_text") + match2.group("trailing_text")
        return (remaining_str, region_str, region_id)

def _generate_region_csv_file(global_file: str, region_id: str, region_str: str):
    # inject the region id into the target file name, based on global_file
    filename_regex = re.compile("(?P<anyname>.*)\.global\.pinpoints\.csv")
    match = filename_regex.fullmatch(global_file)
    if not match:
        raise Exception(f"Cannot fully match filename {global_file}")
    region_filename = match.group("anyname") + f".global.pinpoints.{region_id}.csv"
    
    # open file and dump!
    with open(region_filename, "w") as ofile:
        ofile.write(region_str)

def run(path: Path):
    """
    This script aims to break down a single csv file contaning all ROIs and their
    warmup regions into separate csv files, each containing one ROI (and its
    associated warmup region, if existent).

    INPUT: The routine needs to know the full path of the looppoint run's output_base_dir,
    which could look like "custom-matrix-omp-0-test-passive-1-20230901172326".
    That's it. From here the script will hunt for the pinpoint.csv file using
    glob(*.Data/*global.pinpoints.csv).

    OUTPUT (SIDE EFFECTS): 

    EXCEPTION: If glob(*.Data/*.csv) returns zero or more than one file, the script
    raises an exception. 
    """
    files = _find_eligible_global_pinpoints_csv_file(path)
    if len(files) != 1:
        raise Exception(f"Result of glob is not one single file. We got {files}")
    # print(files)
    
    global_csv_file = files[0]
    s = _read_global_csv_file(global_csv_file)
    # print(fc)

    [s, single_region_s, region_id] = _extract_single_region_from_global_s(s)
    while single_region_s is not None:
        _generate_region_csv_file(global_csv_file, region_id, single_region_s)
        [s, single_region_s, region_id] = _extract_single_region_from_global_s(s)

def main() :
    path = Path("/home/shen449/runahead_project/looppoint/apps/demo/matrix-omp/test/custom-matrix-omp-0-test-passive-1-20230901172326")
    run(path)

if __name__ == "__main__":
    main()