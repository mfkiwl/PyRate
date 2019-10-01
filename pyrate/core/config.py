#   This Python module is part of the PyRate software package.
#
#   Copyright 2017 Geoscience Australia
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
"""
This Python module contains utilities to parse PyRate configuration
files. It also includes numerous general constants relating to options
in configuration files. Examples of PyRate configuration files are
provided in the configs/ directory
"""
# coding: utf-8
# pylint: disable=invalid-name
# pylint: disable=W1203
# pylint: disable=too-many-locals
# pylint: disable=trailing-whitespace
from typing import List, Tuple, Dict, Optional
import os
from os.path import splitext, split
import re
import itertools
import logging

from pyrate.core.ifgconstants import YEARS_PER_DAY

_logger = logging.getLogger(__name__)

# general constants
NO_MULTILOOKING = 1
ROIPAC = 0
GAMMA = 1
LOG_LEVEL = 'INFO'
SIXTEEN_DIGIT_EPOCH_PAIR = r'\d{8}-\d{8}'
TWELVE_DIGIT_EPOCH_PAIR = r'\d{6}-\d{6}'
EIGHT_DIGIT_EPOCH = r'\d{8}'
MINIMUM_NUMBER_EPOCHS = 3

# constants for lookups
#: STR; Name of input interferogram list file
IFG_FILE_LIST = 'ifgfilelist'
#: BOOL (0/1); The interferogram processor used (0==ROIPAC, 1==GAMMA)
PROCESSOR = 'processor'
#: STR; Name of directory containing input interferograms.
OBS_DIR = 'obsdir'
#: STR; Name of directory for saving output products
OUT_DIR = 'outdir'
#: STR; Name of Digital Elevation Model file
DEM_FILE = 'demfile'
#: STR; Name of the header for the DEM
DEM_HEADER_FILE = 'demHeaderFile'
#: STR; Name of directory containing GAMMA SLC parameter files
SLC_DIR = 'slcFileDir'
# STR; Name of the file list containing the pool of available SLC headers
SLC_FILE_LIST = 'slcfilelist'


#: STR; The projection of the input interferograms.
INPUT_IFG_PROJECTION = 'projection'
#: FLOAT; The no data value in the interferogram files.
NO_DATA_VALUE = 'noDataValue'
#: FLOAT; No data averaging threshold for prepifg
NO_DATA_AVERAGING_THRESHOLD = 'noDataAveragingThreshold'
#: BOOL (1/2/3); Re-project data from Line of sight, 1 = vertical,
# 2 = horizontal, 3 = no conversion
#REPROJECTION = 'prjflag' # NOT CURRENTLY USED
#: BOOL (0/1): Convert no data values to Nan
NAN_CONVERSION = 'nan_conversion'

# Prepifg parameters
#: BOOL (1/2/3/4); Method for cropping interferograms, 1 = minimum overlapping area (intersection), 2 = maximum area (union), 3 = customised area, 4 = all ifgs already same size
IFG_CROP_OPT = 'ifgcropopt'
#: INT; Multi look factor for interferogram preparation in x dimension
IFG_LKSX = 'ifglksx'
#: INT; Multi look factor for interferogram preparation in y dimension
IFG_LKSY = 'ifglksy'
#: REAL; Minimum longitude for cropping with method 3
IFG_XFIRST = 'ifgxfirst'
#: REAL; Maximum longitude for cropping with method 3
IFG_XLAST = 'ifgxlast'
#: REAL; Minimum latitude for cropping with method 3
IFG_YFIRST = 'ifgyfirst'
#: REAL; Maximum latitude for cropping with method 3
IFG_YLAST = 'ifgylast'

# reference pixel parameters
#: INT; Coordinate in x of reference pixel OR -1 = perform search
REFX = 'refx'
#: INT; Coordinate in y of reference pixel OR -1 = perform search
REFY = 'refy'
#: INT; Number of reference pixel grid search nodes in x dimension
REFNX = "refnx"
#: INT; Number of reference pixel grid search nodes in y dimension
REFNY = "refny"
#: INT; Dimension of reference pixel search window
REF_CHIP_SIZE = 'refchipsize'
#: REAL; Minimum fraction of observations required in search window for pixel to be a viable reference pixel
REF_MIN_FRAC = 'refminfrac'
#: BOOL (1/2); Reference phase estimation method
REF_EST_METHOD = 'refest'

# coherence masking parameters
COH_MASK = 'cohmask'
"""int: perform coherence masking, 1 = yes, 0 = no"""
COH_THRESH = 'cohthresh'
"""float: coherence treshold"""
COH_FILE_DIR = 'cohfiledir'
"""str: Directory containing coherence .cc files. Defaults to OBS_DIR if not provided."""
COH_FILE_LIST = 'cohfilelist'
"""str: Name of the file list containing the pool of available coherence files"""

#atmospheric error correction parameters NOT CURRENTLY USED
APS_CORRECTION = 'apscorrect'
APS_METHOD = 'apsmethod'
APS_INCIDENCE_MAP = 'incidencemap'
APS_INCIDENCE_EXT = 'APS_INCIDENCE_EXT'
APS_ELEVATION_MAP = 'elevationmap'
APS_ELEVATION_EXT = 'APS_ELEVATION_EXT'

# orbital error correction/parameters
#: BOOL (1/0); Flag controlling whether to apply orbital error correction
ORBITAL_FIT = 'orbfit'
#: BOOL (1/2); Method for orbital error correction, 1: independent, 2: network
ORBITAL_FIT_METHOD = 'orbfitmethod'
#: BOOL (1/2/3) Order of orbital error model, 1 = planar in x and y (2 parameter model, 2 = quadratic in x and y (5 parameter model), 3 = quadratic in x and cubic in y (part-cubic 6 parameter model)
ORBITAL_FIT_DEGREE = 'orbfitdegrees'
#: INT; Multi look factor for orbital error calculation in x dimension
ORBITAL_FIT_LOOKS_X = 'orbfitlksx'
#: INT; Multi look factor for orbital error calculation in y dimension
ORBITAL_FIT_LOOKS_Y = 'orbfitlksy'

# Linear rate/stacking parameters
#: REAL; Threshold ratio between 'model minus observation' residuals and a-priori observation standard deviations for linear rate estimate acceptance (otherwise remove furthest outlier and re-iterate)
LR_NSIG = 'nsig'
#: INT; Number of required observations per pixel for the linear rate inversion
LR_PTHRESH = 'pthr'
#: REAL; Maximum allowable standard error for pixels in linear rate inversion.
LR_MAXSIG = 'maxsig'

# atmospheric delay errors fitting parameters NOT CURRENTLY USED
# atmfitmethod = 1: interferogram by interferogram; atmfitmethod = 2, epoch by epoch
#ATM_FIT = 'atmfit'
#ATM_FIT_METHOD = 'atmfitmethod'

#: BOOL (0/1) Do spatio-temporal filter
APSEST = 'apsest'

# temporal low-pass filter parameters
TLPF_METHOD = 'tlpfmethod'
TLPF_CUTOFF = 'tlpfcutoff'
TLPF_PTHR = 'tlpfpthr'

# spatially correlated noise low-pass filter parameters
SLPF_METHOD = 'slpfmethod'
SLPF_CUTOFF = 'slpfcutoff'
SLPF_ORDER = 'slpforder'
SLPF_NANFILL = 'slpnanfill'
SLPF_NANFILL_METHOD = 'slpnanfill_method'

# Time series parameters
#: BOOL (1/0); Do Time series calculation
TIME_SERIES_CAL = 'tscal'
#: INT (1/2); Method for time series inversion (1: Laplacian Smoothing; 2: SVD)
TIME_SERIES_METHOD = 'tsmethod'
#: INT; Number of required input observations per pixel for time series inversion
TIME_SERIES_PTHRESH = 'ts_pthr'
#: INT (1/2); Order of Laplacian smoothing operator, first or # second order
TIME_SERIES_SM_ORDER = 'smorder'
#: REAL; Laplacian smoothing factor (values used is 10**smfactor)
TIME_SERIES_SM_FACTOR = 'smfactor'
# tsinterp is automatically assigned in the code; not needed in conf file
#TIME_SERIES_INTERP = 'tsinterp'

#: BOOL (0/1/2); Use parallelisation/Multi-threading
PARALLEL = 'parallel'
#: INT; Number of processes for multi-threading
PROCESSES = 'processes'

# Orbital error correction constants for conversion to readable flags
INDEPENDENT_METHOD = 1
NETWORK_METHOD = 2
PLANAR = 1
QUADRATIC = 2
PART_CUBIC = 3

# dir for temp files
TMPDIR = 'tmpdir'

# Lookup to help convert args to correct type/defaults
# format is	key : (conversion, default value)
# None = no conversion
PARAM_CONVERSION = {
#    REPROJECTION : (int, 3), # Default no conversion, CONVERSION NOT IMPLEMENTED
    IFG_CROP_OPT : (int, 1), # default to area 'intersection' option
    IFG_LKSX : (int, NO_MULTILOOKING),
    IFG_LKSY : (int, NO_MULTILOOKING),
    IFG_XFIRST : (float, None),
    IFG_XLAST : (float, None),
    IFG_YFIRST : (float, None),
    IFG_YLAST : (float, None),
    NO_DATA_VALUE: (float, 0.0),

    COH_MASK: (int, 0),
    COH_THRESH: (float, 0.1),

    REFX: (float, 181),
    REFY: (float, 91),
    REFNX: (int, 10),
    REFNY: (int, 10),
    REF_CHIP_SIZE: (int, 21),
    REF_MIN_FRAC: (float, 0.5),
    REF_EST_METHOD: (int, 1),  # default to average of whole image

    ORBITAL_FIT: (int, 0),
    ORBITAL_FIT_METHOD: (int, NETWORK_METHOD),
    ORBITAL_FIT_DEGREE: (int, PLANAR),
    ORBITAL_FIT_LOOKS_X: (int, 10),
    ORBITAL_FIT_LOOKS_Y: (int, 10),

    LR_NSIG: (int, 2),
    # pixel thresh based on nepochs? not every project may have 20 epochs
    LR_PTHRESH: (int, 3),
    LR_MAXSIG: (int, 10),

    #ATM_FIT: (int, 0), NOT CURRENTLY USED
    #ATM_FIT_METHOD: (int, 2),

    APSEST: (int, 0),
    TLPF_METHOD: (int, 1),
    TLPF_CUTOFF: (float, 1.0),
    TLPF_PTHR: (int, 1),

    SLPF_METHOD: (int, 1),
    SLPF_CUTOFF: (float, 1.0),
    SLPF_ORDER: (int, 1),
    SLPF_NANFILL: (int, 0),

    TIME_SERIES_CAL: (int, 0),
    # pixel thresh based on nepochs? not every project may have 20 epochs
    TIME_SERIES_PTHRESH: (int, 3),
    TIME_SERIES_SM_FACTOR: (float, None),
    TIME_SERIES_SM_ORDER: (int, None),
    TIME_SERIES_METHOD: (int, 2),  # Default to SVD method

    PARALLEL: (int, 0),
    PROCESSES: (int, 8),
    PROCESSOR: (int, None),
    NAN_CONVERSION: (int, 0),
    NO_DATA_AVERAGING_THRESHOLD: (float, 0.0),
    }

PATHS = [OBS_DIR, IFG_FILE_LIST, DEM_FILE,
         DEM_HEADER_FILE, OUT_DIR,
         SLC_DIR, SLC_FILE_LIST, COH_FILE_DIR, COH_FILE_LIST,
         APS_INCIDENCE_MAP,
         APS_ELEVATION_MAP]

DEFAULT_TO_OBS_DIR = [SLC_DIR, COH_FILE_DIR]

INT_KEYS = [APS_CORRECTION, APS_METHOD]

def get_config_params(path: str, validate: bool=True, requires_tif: bool=False) -> Dict:
    """
    Reads the parameters file provided by the user and converts it into
    a dictionary.
    
    Args:
        path: Absolute path to the parameters file.
        validate: Validate the parameters if True, otherwise skip validation.
        requires_tif: True if the calling process requires interferograms
            in geotiff format (performs additional validation).
    Returns:
       A dictionary of parameters. 
    """
    txt = ''
    with open(path, 'r') as inputFile:
        for line in inputFile:
            if any(x in line for x in PATHS):
                pos = line.find('~')
                if pos != -1:
                    # create expanded line
                    line = line[:pos] + os.environ['HOME'] + line[(pos+1):]
            txt += line
    params = _parse_conf_file(txt, validate, requires_tif)
    params[TMPDIR] = os.path.join(os.path.abspath(params[OUT_DIR]), 'tmpdir')

    return params

def _parse_conf_file(content, validate: bool=True, requires_tif: bool=False) -> Dict:
    """
    Converts the parameters from their text form into a dictionary.
    
    Args:
        content: Parameters as text.
        
    Returns:
        A dictionary of parameters.
    """
    def _is_valid(line):
        """
        Check if line is not empty or has % or #
        """
        return line != "" and line[0] not in "%#"

    lines = [ln.split() for ln in content.split('\n') if _is_valid(ln)]

    # convert "field:   value" lines to [field, value]
    kvpair = [(e[0].rstrip(":"), e[1]) for e in lines if len(e) == 2] \
        + [(e[0].rstrip(":"), None) for e in lines if len(e) == 1]
    parameters = dict(kvpair)
    for p in PATHS:
        if p not in parameters:
            parameters[p] = None

    for p in INT_KEYS:
        if p not in parameters:
            parameters[p] = '0'  # insert dummies

    parameters = _handle_extra_parameters(parameters)

    if not parameters:
        raise ConfigException('Cannot parse any parameters from config file')

    return _parse_pars(parameters, validate, requires_tif)

def _handle_extra_parameters(params):
    """
    Function to check if requirements for weather model correction are given.
    """
    params[APS_INCIDENCE_EXT] = None
    params[APS_ELEVATION_EXT] = None

    if params[APS_INCIDENCE_MAP] is not None:
        params[APS_INCIDENCE_EXT] = \
            os.path.basename(params[APS_INCIDENCE_MAP]).split('.')[-1]
        params[APS_ELEVATION_MAP] = None
        params[APS_ELEVATION_EXT] = None
        return params

    # define APS_ELEVATON_EXT for gamma prepifg
    if params[APS_ELEVATION_MAP] is not None:
        params[APS_ELEVATION_EXT] = os.path.basename(
            params[APS_ELEVATION_MAP]).split('.')[-1]

    return params

def _parse_pars(pars, validate: bool=True, requires_tif: bool=False) -> Dict:
    """
    Takes dictionary of parameters, converting values to required type
    and providing defaults for missing values.

    Args:
        pars: Parameters dictionary.

    Returns:
        Dictionary of converted (and optionally validated) parameters.
    """
    # Fallback to default for missing values and perform conversion.
    for k in PARAM_CONVERSION:
        if pars.get(k) is None:
            pars[k] = PARAM_CONVERSION[k][1]
            _logger.warning(f"No value found for parameter '{k}'. Providing "
                            f"default value {pars[k]}.")
        else:
            conversion_func = PARAM_CONVERSION[k][0]
            if conversion_func:
                try:
                    pars[k] = conversion_func(pars[k])
                except ValueError as e:
                    _logger.error(f"Unable to convert '{k}': {pars[k]} to "
                                  f"expected type {conversion_func.__name__}.")
                    raise e

    # Fallback to default for missing paths.
    for p in DEFAULT_TO_OBS_DIR:
        if pars.get(p) is None:
            pars[p] = pars[OBS_DIR]

    if validate:
        validate_parameters(pars, requires_tif)
    return pars



# CONFIG UTILS - TO BE MOVED?

def parse_namelist(nml):
    """
    Parses name list file into array of paths

    :param str nml: interferogram file list

    :return: list of interferogram file names
    :rtype: list
    """
    with open(nml) as f_in:
        lines = [line.rstrip() for line in f_in]
    return filter(None, lines)

def write_config_file(params, output_conf_file):
    """
    Takes a param object and writes the config file. Reverse of get_conf_params.

    :param dict params: parameter dictionary
    :param str output_conf_file: output file name

    :return: config file
    :rtype: list
    """
    with open(output_conf_file, 'w') as f:
        for k, v in params.items():
            if v is not None:
                f.write(''.join([k, ':\t', str(v), '\n']))
            else:
                f.write(''.join([k, ':\t', '', '\n']))

def transform_params(params):
    """
    Returns subset of all parameters for cropping and multilooking.

    :param dict params: Parameter dictionary

    :return: xlooks, ylooks, crop
    :rtype: int
    """

    t_params = [IFG_LKSX, IFG_LKSY, IFG_CROP_OPT]
    xlooks, ylooks, crop = [params[k] for k in t_params]
    return xlooks, ylooks, crop

def original_ifg_paths(ifglist_path, obs_dir):
    """
    Returns sequence of paths to files in given ifglist file.

    Args:
        ifglist_path: Absolute path to interferogram file list.
        obs_dir: Absolute path to observations directory.

    Returns:
        list: List of full paths to interferogram files.
    """
    ifglist = parse_namelist(ifglist_path)
    return [os.path.join(obs_dir, p) for p in ifglist]

def coherence_paths_for(path, params, tif=False) -> str:
    """
    Returns path to coherence file for given interferogram. Pattern matches
    based on epoch in filename.

    Example:
        '20151025-20160501_eqa_filt.cc'
        Datepair is the epoch.

    Args:
        path: Path to intergerogram to find coherence file for.
        params: Parameter dictionary.
        tif: Find converted tif if True (_cc.tif), else find .cc file.

    Returns:
        Path to coherence file.
    """
    _, filename = split(path)
    pattern = re.compile(r'\d{8}-\d{8}')
    epoch = re.match(pattern, filename).group(0)
    coherence_dir = params[COH_FILE_DIR]
    matches = [name for name in parse_namelist(params[COH_FILE_LIST])
               if epoch in name]
    if tif:
        names_exts = [os.path.splitext(m) for m in matches]
        matches = [ne[0] + ne[1].replace('.', '_') + '.tif'
                   for ne in names_exts]

    return [os.path.join(coherence_dir, m) for m in matches]

def coherence_paths(params) -> List[str]:
    """
    Returns paths to corresponding coherence files for given IFGs. Assumes
    that each IFG has a corresponding coherence file in the coherence file
    directory and they share epoch prefixes.

    Args:
        ifg_paths: List of paths to intergerogram files.

    Returns:
        A list of full paths to coherence files.
    """
    ifg_file_list = params.get(IFG_FILE_LIST)
    ifgs = parse_namelist(ifg_file_list)
    paths = [coherence_paths_for(ifg, params) for ifg in ifgs]
    return list(itertools.chain.from_iterable(paths))

def mlooked_path(path, looks, crop_out):
    """
    Adds suffix to ifg path, for creating a new path for multilooked files.

    :param str path: original interferogram path
    :param int looks: number of range looks applied
    :param int crop_out: crop option applied

    :return: multilooked file name
    :rtype: str
    """
    base, ext = splitext(path)
    return "{base}_{looks}rlks_{crop_out}cr{ext}".format(
        base=base, looks=looks, crop_out=crop_out, ext=ext)

def get_dest_paths(base_paths, crop, params, looks):
    """
    Determines the full path names for the destination multilooked files

    :param list base_paths: original interferogram paths
    :param int crop: Crop option applied
    :param dict params: Parameters dictionary
    :param int looks: number of range looks applied

    :return: full path names for destination files
    :rtype: list
    """

    dest_mlooked_ifgs = [mlooked_path(os.path.basename(q).split('.')[0] + '_'
                                      + os.path.basename(q).split('.')[1] +
                                      '.tif', looks=looks, crop_out=crop)
                         for q in base_paths]

    return [os.path.join(params[OUT_DIR], p) for p in dest_mlooked_ifgs]

def get_ifg_paths(config_file, requires_tif=False):
    """
    Read the configuration file, extract interferogram file list and determine
    input and output interferogram path names.

    :param str config_file: Configuration file path

    :return: base_unw_paths: List of unwrapped inteferograms
    :return: dest_paths: List of multi-looked and cropped geotifs
    :return: params: Dictionary corresponding to the config file
    :rtype: list
    :rtype: list
    :rtype: dict
    """
    params = get_config_params(config_file, requires_tif)
    ifg_file_list = params.get(IFG_FILE_LIST)

    xlks, _, crop = transform_params(params)

    # base_unw_paths need to be geotiffed by converttogeotiff
    #   and multilooked by run_prepifg
    base_unw_paths = original_ifg_paths(ifg_file_list, params[OBS_DIR])

    # dest_paths are tifs that have been coherence masked (if enabled),
    #  cropped and multilooked
    dest_paths = get_dest_paths(base_unw_paths, crop, params, xlks)

    return base_unw_paths, dest_paths, params

# ==== PARAMETER VALIDATION ==== #

_PARAM_VALIDATION = {
    OBS_DIR: (
        lambda a: a is not None and os.path.exists(a),
        f"'{OBS_DIR}': directory must be provided and must exist."
    ),
    IFG_FILE_LIST: (
        lambda a: a is not None and os.path.exists(a),
        f"'{IFG_FILE_LIST}': file must be provided and must exist."
    ),
    DEM_FILE: (
        lambda a: a is not None and os.path.exists(a),
        f"'{DEM_FILE}': file must be provided and must exist."
    ),
    DEM_HEADER_FILE: (
        lambda a: a is not None and os.path.exists(a),
        f"'{DEM_HEADER_FILE}': file must be provided and must exist."
    ),
    OUT_DIR: (
        lambda a: a is not None,
        f"'{OBS_DIR}': directory must be provided."
    ),
    APS_INCIDENCE_MAP: (
        lambda a: os.path.exists(a) if a is not None else True,
        f"'{APS_INCIDENCE_MAP}': file must exist."
    ),
    APS_ELEVATION_MAP: (
        lambda a: os.path.exists(a) if a is not None else True,
        f"'{APS_ELEVATION_MAP}': file must exists."
    ),
    IFG_CROP_OPT: (
        lambda a: a in (1, 2, 3, 4),
        f"'{IFG_CROP_OPT}': must select option 1, 2, 3, or 4."
    ),
    IFG_LKSX: (
        lambda a: a >= 1,
        f"'{IFG_LKSX}': must be >= 1."
    ),
    IFG_LKSY: (
        lambda a: a >= 1,
        f"'{IFG_LKSY}': must be >= 1."
    ),
    NO_DATA_VALUE: (
        lambda a: True,
        "Any float value valid."
    ),
    COH_MASK: (
        lambda a: a in (0, 1),
        f"'{COH_MASK}': must select option 0 or 1."
    ),
    REFX: (
        lambda a: True,
        "Any int value valid."
    ),
    REFY: (
        lambda a: True,
        "Any int value valid."
    ),
    ORBITAL_FIT: (
        lambda a: a in (0, 1),
        f"'{ORBITAL_FIT}': must select option 0 or 1."
    ),
    LR_NSIG: (
        lambda a: 1 <= a <= 10,
        f"'{LR_NSIG}': must be between 1 and 10 (inclusive)."
    ),
    LR_PTHRESH: (
        lambda a: a >= 1,
        f"'{LR_PTHRESH}': must be >= 1"
    ),
    LR_MAXSIG: (
        lambda a: 0 <= a <= 1000,
        f"'{LR_MAXSIG}': must be between 0 and 1000 (inclusive)."
    ),
    APSEST: (
        lambda a: a in (0, 1),
        f"'{APSEST}': must select option 0 or 1."
    ),
    TIME_SERIES_CAL: (
        lambda a: a in (0, 1),
        f"'{TIME_SERIES_CAL}': must select option 0 or 1."
    ),
    PARALLEL: (
        lambda a: a in (0, 1, 2),
        f"'{PARALLEL}': must select option 0 or 1 or 2."
    ),
    PROCESSES: (
        lambda a: a >= 1,
        f"'{PROCESSES}': must be >= 1."
    ),
    PROCESSOR: (
        lambda a: a in (0, 1),
        f"'{PROCESSOR}': must select option 0 or 1."
    ),
    NAN_CONVERSION: (
        lambda a: a in (0, 1),
        f"'{NAN_CONVERSION}': must select option 0 or 1."
    ),
    NO_DATA_AVERAGING_THRESHOLD: (
        lambda a: True,
        "Any float value valid."),
}
"""dict: basic validation functions for compulsory parameters."""

_CUSTOM_CROP_VALIDATION = {
    IFG_XFIRST: (
        lambda a: a is not None,
        f"'{IFG_XFIRST}': must be provided."
    ),
    IFG_XLAST: (
        lambda a: a is not None,
        f"'{IFG_XLAST}': must be provided."
    ),
    IFG_YFIRST: (
        lambda a: a is not None,
        f"'{IFG_YFIRST}': must be provided."
    ),
    IFG_YLAST: (
        lambda a: a is not None,
        f"'{IFG_YLAST}': must be provided.."
    ),
}
"""dict: basic validation functions for custom cropping parameters."""

_GAMMA_VALIDATION = {
    SLC_DIR: (
        lambda a: os.path.exists(a) if a is not None else True,
        f"'{SLC_DIR}': directory must must exist."
    ),
    SLC_FILE_LIST: (
        lambda a: a is not None and os.path.exists(a),
        f"'{SLC_FILE_LIST}': file must be provided and must exist."
    ),
}
"""dict: basic validation functions for gamma parameters."""

_COHERENCE_VALIDATION = {
    COH_THRESH: (
        lambda a: 0.0 <= a <= 1.0,
        f"'{COH_THRESH}': must be between 0.0 and 1.0 (inclusive)."
    ),
    COH_FILE_DIR: (
        lambda a: os.path.exists(a) if a is not None else True,
        f"'{COH_FILE_DIR}': directory must exist."
    ),
    COH_FILE_LIST: (
        lambda a: a is not None and os.path.exists(a),
        f"'{COH_FILE_LIST}': file must be provided and must exist."
    ),
}
"""dict: basic validation functions for coherence parameters."""

_ORBITAL_FIT_VALIDATION = {
    ORBITAL_FIT_METHOD: (
        lambda a: a in (1, 2),
        f"'{ORBITAL_FIT_METHOD}': must select option 1 or 2."
    ),
    ORBITAL_FIT_DEGREE: (
        lambda a: a in (1, 2, 3),
        f"'{ORBITAL_FIT_DEGREE}': must select option 1, 2 or 3."
    ),
    ORBITAL_FIT_LOOKS_X: (
        lambda a: a >= 1,
        f"'{ORBITAL_FIT_LOOKS_X}': must be >= 1."
    ),
    ORBITAL_FIT_LOOKS_Y: (
        lambda a: a >= 1,
        f"'{ORBITAL_FIT_LOOKS_Y}': must be >= 1."
    ),
}
"""dict: basic validation fucntions for orbital error correction parameters."""

_APSEST_VALIDATION = {
    TLPF_METHOD: (
        lambda a: a in (1, 2, 3),
        f"'{TLPF_METHOD}': must select option 1, 2 or 3."
    ),
    TLPF_CUTOFF: (
        lambda a: a >= YEARS_PER_DAY, # 1 day in years
        f"'{TLPF_CUTOFF}': must be >= {YEARS_PER_DAY}."
    ),
    TLPF_PTHR: (
        lambda a: a >= 1,
        f"'{TLPF_PTHR}': must be >= 1."
    ),
    SLPF_METHOD: (
        lambda a: a in (1, 2),
        f"'{SLPF_METHOD}': must select option 1 or 2."
    ),
    SLPF_CUTOFF: (
        lambda a: a >= 0.001,
        f"'{SLPF_CUTOFF}': must be >= 0.001."
    ),
    SLPF_ORDER: (
        lambda a: 1 <= a <= 3,
        f"'{SLPF_ORDER}': must be between 1 and 3 (inclusive)."
    ),
    SLPF_NANFILL: (
        lambda a: a in (0, 1),
        f"'{SLPF_NANFILL}': must select option 0 or 1."
    ),
}
"""dict: basic validation functions for atmospheric correction parameters."""

_TIME_SERIES_VALIDATION = {
    TIME_SERIES_PTHRESH: (
        lambda a: a >= 1,
        f"'{TIME_SERIES_PTHRESH}': must be >= 1"
    ),
    #TODO: Matt to investigate smoothing factor values.
    TIME_SERIES_SM_FACTOR: (
        lambda a: True,
        f"'{TIME_SERIES_SM_FACTOR}':"
    ),
    TIME_SERIES_SM_ORDER: (
        lambda a: a in (1, 2),
        f"'{TIME_SERIES_SM_ORDER}': must select option 1 or 2."
    ),
    TIME_SERIES_METHOD: (
        lambda a: a in (1, 2),
        f"'{TIME_SERIES_METHOD}': must select option 1 or 2."
    ),
}
"""dict: basic vaidation functions for time series parameters."""

_REFERENCE_PIXEL_VALIDATION = {
    REFNX: (
        lambda a: 1 <= a <= 50,
        f"'{REFNX}': must be between 1 and 50 (inclusive)."
    ),
    REFNY: (
        lambda a: 1 <= a <= 50,
        f"'{REFNY}': must be between 1 and 50 (inclusive)."
    ),
    REF_CHIP_SIZE: (
        lambda a: 1 <= a <= 101 and a % 2 == 1,
        f"'{REF_CHIP_SIZE}': must be between 1 and 101 (inclusive) and be odd."
    ),
    REF_MIN_FRAC: (
        lambda a: 0.0 <= a <= 1.0,
        f"'{REF_MIN_FRAC}': must be between 0.0 and 1.0 "
        "(inclusive)."
    ),
    REF_EST_METHOD: (
        lambda a: a in (1, 2),
        f"'{REF_EST_METHOD}': must select option 1 or 2."
    ),
}
"""dict: basic validation functions for reference pixel search parameters."""

def validate_parameters(pars: Dict, requires_tif: bool=False):
    """
    Main validation function. Calls validation subfunctions and gathers
    some required variables for performing validation.

    Args:
        pars: The parameters dictionary.
        requires_tif: Whether the currently used workflow requires
            interferograms in tif format.

    Raises:
        ConfigException: If errors occur during parameter validation.
    """
    is_GAMMA = pars[PROCESSOR] == GAMMA
    ifl = pars[IFG_FILE_LIST]

    validate_compulsory_parameters(pars)
    validate_optional_parameters(pars)

    if is_GAMMA:
        validate_epochs(ifl, SIXTEEN_DIGIT_EPOCH_PAIR)
    else:
        validate_epochs(ifl, TWELVE_DIGIT_EPOCH_PAIR)

    validate_ifgs(ifl, pars[OBS_DIR])

    extents, n_cols, n_rows, n_epochs, max_span = None, None, None, None, None
    if requires_tif:
        validate_tifs_exist(pars[IFG_FILE_LIST], pars[OBS_DIR])
        # Get info regarding epochs and dimensions needed for validation.
        crop_opts = _crop_opts(pars)
        extents, n_cols, n_rows, n_epochs, max_span = \
           _get_ifg_information(pars[IFG_FILE_LIST], pars[OBS_DIR], crop_opts)

        validate_pixel_parameters(n_cols, n_rows, pars)
        validate_reference_pixel_search_windows(n_cols, n_rows, pars)
        validate_extent_parameters(extents, pars)
        validate_minimum_epochs(n_epochs, MINIMUM_NUMBER_EPOCHS)
        validate_epoch_thresholds(n_epochs, pars)
        validate_epoch_cutoff(max_span, TLPF_CUTOFF, pars)

    validate_obs_thresholds(ifl, pars)

    if is_GAMMA:
        validate_epochs(pars[SLC_FILE_LIST], EIGHT_DIGIT_EPOCH)
        validate_gamma_headers(ifl, pars[SLC_FILE_LIST], pars[SLC_DIR])

    if pars[COH_MASK]:
        validate_epochs(pars[COH_FILE_LIST], SIXTEEN_DIGIT_EPOCH_PAIR)
        validate_coherence_files(ifl, pars)

def _raise_errors(errors: List[str]):
    """
    Convenience function for raising an exception with errors.
    """
    if errors:
        errors.insert(0, "invalid parameters")
        raise ConfigException('\n'.join(errors))
    return True

def validate_compulsory_parameters(pars: Dict) -> Optional[bool]:
    """
    Calls the validators for compulsory (always used) parameters.
    
    Args:
        pars: The parameters dictionary.

    Returns:
        True if validation is successful.
        
    Raises:
        ConfigException: If validation fails.
    """
    errors = []
    for k in pars.keys():
        validator = _PARAM_VALIDATION.get(k)
        if validator is None:
            _logger.debug(f"No validator implemented for '{k}'.")
            continue
        if not validator[0](pars[k]):
            errors.append(validator[1])

    return _raise_errors(errors)

def validate_optional_parameters(pars: Dict):
    """ 
    Calls the validators for optional parameters.
    
    Args:
        pars: The parameters dictionary.
        
    Returns:
        True if validation successful.
        
    Raises:
        ConfigException: If validation fails.
    """
    def validate(on: bool, validators: Dict, pars: Dict) -> List[str]:
        """
        Convenience method for calling validators.
    
        Args:
            on: Determines whether to call the validators.
            validators: A dictionary of validator functions.
            pars: Parameters dictionary.

        Returns:
            A list of errors.           
        """
        errors = []
        if on:
            for k, validator in validators.items():
                if not validator[0](pars[k]):
                    errors.append(validator[1])
        return errors

    errors = []

    errors.extend(
        validate(pars[COH_MASK], _COHERENCE_VALIDATION, pars))
    errors.extend(
        validate(pars[APSEST], _APSEST_VALIDATION, pars))
    errors.extend(
        validate(pars[TIME_SERIES_CAL], _TIME_SERIES_VALIDATION, pars))
    errors.extend(
        validate(pars[ORBITAL_FIT], _ORBITAL_FIT_VALIDATION, pars))
    errors.extend(
        validate(pars[PROCESSOR] == GAMMA, _GAMMA_VALIDATION, pars))
    errors.extend(
        validate(pars[IFG_CROP_OPT] == 3, _CUSTOM_CROP_VALIDATION, pars))
    errors.extend(
        validate(pars[REFX] > 0 and pars[REFY] > 0, _REFERENCE_PIXEL_VALIDATION, pars))

    return _raise_errors(errors)

def validate_minimum_epochs(n_epochs: int, min_epochs: int) -> Optional[bool]:
    """
    Validates the minimum number of epochs required for PyRate to produce
    good results. 

    Args:
        n_epochs: The number of unique epochs in the collection of interferograms
            provided as input.
        min_epochs: The minimum number of epochs PyRate requires.

    Returns:
        True if there are enough epochs to satisfy minimum epochs.
    
    Raises:
        ConfigException: If there are not enough epochs to satisfy min epochs.
    """
    errors = []
    if n_epochs < min_epochs:
        errors.append(f"'{IFG_FILE_LIST}': total number of epochs is less "
                      "than {min_epochs}. {min_epochs} or "
                      "more unique epochs are required by PyRate.")
    _raise_errors(errors)

def validate_epochs(file_list: str, pattern: str) -> Optional[bool]:
    """
    Validate that user provided file names contain the correct pattern of
    epochs.

    Args:
        file_list: Path to the list of files to validate.
        pattern: Regex string for finding the epoch(s).

    Returns:
        True if all names in file list contain the epoch pattern *once*.

    Raises:
        ConfigException: If not all names in the file list don't contain
            the epoch pattern or contain it more than once.
    """
    errors = []
    PTN = re.compile(pattern)
    filenames = parse_namelist(file_list)
    for fn in filenames:
        epochs = PTN.findall(fn)
        if not epochs:
            errors.append(f"'{file_list}': {fn} does not contain an epoch of "
                          f"format {pattern}.")
        if len(epochs) > 1:
            errors.append(f"'{file_list}': {fn} does contains more than "
                          f"one epoch of {pattern}. There must be only one "
                          f"epoch in the filename.")

    return _raise_errors(errors)

def validate_epoch_cutoff(max_span: float, cutoff: str, pars: Dict) -> Optional[bool]:
    """
    Validate cutoff parameters that rely on the data timespan.
    
    Args:
        max_span: The maximum temporal span of the provided data in years.
        cutoff: The key of the cutoff parameter.
        pars: The parameters dictionary.
    
    Returns:
        True if the cutoff is less than the maximum data timespan.
    
    Raises:
        ConfigException: If the cutoff is greater than the max data timespan.
    """
    errors = []
    if pars[cutoff] > max_span:
        errors.append("'{cutoff}': must be less than max time span of "
                      "data in years ({max_span}).")
    return _raise_errors(errors)

def validate_tifs_exist(ifg_file_list: str, obs_dir: str) -> Optional[bool]:
    """
    Validates that provided interferograms exist in geotiff format.

    Args:
        ifg_file_list: Path to file containing interfergram file names.
        obs_dir: Path to observations directory.

    Returns:
        True if all interferograms exist in geotiff format.

    Raises:
        ConfigException: If not all intergerograms exist in geotiff format.
    """
    from pyrate.core.shared import output_tiff_filename

    errors = []
    ifgs = parse_namelist(ifg_file_list)
    ifg_paths = [os.path.join(obs_dir, ifg) for ifg in ifgs]
    gtiff_paths = [output_tiff_filename(f, obs_dir) for f in ifg_paths]
    for gtp in gtiff_paths:
        if not os.path.exists(gtp):
            fname = os.path.split(gtp)[1]
            errors.append(f"'{IFG_FILE_LIST}': interferogram '{fname}' is "
                          "required in geotiff format but no geotiff file "
                          "could be found.")

    return _raise_errors(errors)

def validate_ifgs(ifg_file_list: str, obs_dir: str) -> Optional[bool]:
    """
    Validates that provided interferograms exist.

    Args:
        ifg_file_list: Path to file containing interferogram file names..
        obs_dir: Path to observations directory.

    Returns:
        True if all interferograms exist.

    Raises:
        ConfigException: If not all interferograms exist.
    """
    errors = []
    ifgs = parse_namelist(ifg_file_list)
    ifg_paths = [os.path.join(obs_dir, ifg) for ifg in ifgs]
    for path in ifg_paths:
        if not os.path.exists(path):
            fname = os.path.split(path)[1]
            errors.append(f"'{IFG_FILE_LIST}': interferogram '{fname}' does not exist.")

    return _raise_errors(errors)

def validate_obs_thresholds(ifg_file_list: str, pars: Dict) -> Optional[bool]:
    """
    Validates parameters that specify an observations threshold.

    Args:
        ifg_file_list: Path to the file containing interferogram file names.
        pars: Parameters dictionary.
    
    Returns:
        True if there are enough interferograms to satisfy all observation thresholds.

    Raises:
        ConfigException: If there not enough interferograms to satisfy all observation
            thresholds.
    """
    def validate(n, p, k):
        thresh = p[k]
        if thresh > n:
            return [f"'{k}': not enough interferograms have been specified "
                    f"({n}) to satisfy threshold ({thresh})."]
        return []

    errors = []
    n_ifgs = len(list(parse_namelist(ifg_file_list)))
    errors.extend(validate(n_ifgs, pars, TIME_SERIES_PTHRESH))
    if pars[APSEST]:
        errors.extend(validate(n_ifgs, pars, TLPF_PTHR))

    return _raise_errors(errors)

def validate_epoch_thresholds(n_epochs: int, pars: Dict) -> Optional[bool]:
    """
    Validates threshold paramters that rely on the number of epochs
    available.

    Args:
        n_epochs: The number of unique epochs in the collection of interferograms
            provided as input.
        pars: Parameters dictionary.
    
    Returns:
        True if there are enough epochs to satisfy all epoch thresholds.

    Raises:
        ConfigException: If there are not enough epochs to satisfy all epoch thresholds.
    """
    errors = []
    thresh = pars[LR_PTHRESH]
    if n_epochs < thresh:
        errors.append(f"'{LR_PTHRESH}': not enough epochs have been specified "
                      f"({n_epochs}) to satisfy threshold ({thresh}).")

    return _raise_errors(errors)

def validate_extent_parameters(extents: Tuple[float, float, float, float], 
                               pars: Dict) -> Optional[bool]:
    """
    Validate parameters that provide lat/long coordinates by checking they fit
    within the scene being processed.

    Args:
        extents : Tuple of (xmin, xmax, ymin, ymax) describing the extents
            of the scene being processed in degrees.
        pars: Parameters dictionary.

    Returns:
        True if validation is successful.

    Raises:
        ConfigException: If validation fails.
    """
    errors = []
    xmin, ymin, xmax, ymax = extents
    x_dim_string = f"(xmin: {xmin}, xmax: {xmax})"
    y_dim_string = f"(ymin: {ymin}, ymax: {ymax})"

    # Check crop coordinates within scene.
    def _validate_crop_coord(var_name, dim_min, dim_max, dim_string):
        if not dim_min < pars[var_name] < dim_max:
            return [f"'{var_name}': crop coordinate ({pars[var_name]}) "
                    f"is outside bounds of scene {dim_string}."]

        return []
    
    if pars[IFG_CROP_OPT] == 3:
        errors.extend(_validate_crop_coord(IFG_XFIRST, xmin, xmax, x_dim_string))
        errors.extend(_validate_crop_coord(IFG_YFIRST, ymin, ymax, y_dim_string))
        errors.extend(_validate_crop_coord(IFG_XLAST, xmin, xmax, x_dim_string))
        errors.extend(_validate_crop_coord(IFG_YLAST, ymin, ymax, y_dim_string))

    # Check SLPF_CUTOFF within scene *in kilometeres*.
    DEG_TO_KM = 111.32 # km per degree
    x_extent = abs(xmin - xmax)
    y_extent = abs(ymin - ymax)
    x_extent_km = x_extent *  DEG_TO_KM
    y_extent_km = y_extent *  DEG_TO_KM
    if pars[SLPF_CUTOFF] > max(x_extent_km, y_extent_km):
        errors.append(f"'{SLPF_CUTOFF}': cutoff is out of bounds, must be "
                      "less than max scene bound (in km) "
                      f"({max(x_extent_km, y_extent_km)}).")

    return _raise_errors(errors)

def validate_pixel_parameters(n_cols: int, n_rows: int, pars: Dict) -> Optional[bool]:
    """
    Validate parameters that provide pixel coordinates by verifying they
    are within the scene being processed.

    Args:
        extents: Tuple of (xmin, xmax, ymin, ymax) describing the extents
            of the scene being processed in degrees.
        n_cols: Number of pixel columns (X) in the raster.
        n_rows: Number of pixel rows (X) in the raster.
        pars: Parameters dictionary.

    Returns:
        True if validation is successful.

    Raises:
        ConfigException: If validation fails.
    """
    errors = []
    x_dim_string = f"(xmin: 0, xmax: {n_cols}"
    y_dim_string = f"(ymin: 0, ymax: {n_rows}"

    # Check reference pixel coordinates within scene.
    if pars[REFX] > 0 and pars[REFY] > 0:
        if not 0 < pars[REFX] <= n_cols:
            errors.append(f"'{REFX}': reference pixel coodinate is "
                          f"outside bounds of scene ({x_dim_string}).")

        if not 0 < pars[REFY] <= n_rows:
            errors.append(f"'{REFY}': reference pixel coodinate is "
                          f"outside bounds of scene ({y_dim_string}).")

    # Check multilooks (extent/val) >= 1.
    def _validate_multilook(var_name, dim_val, dim_string):
        if dim_val / pars[var_name] < 1:
            return [f"'{var_name}': the quantity ( {dim_string} pixel count: "
                    f"{dim_val} / multilook factor: {pars[var_name]} ) must "
                    f"be greater than or equal to 1."]
        return []

    errors.extend(_validate_multilook(IFG_LKSX, n_cols, 'x'))
    errors.extend(_validate_multilook(IFG_LKSY, n_rows, 'y'))
    if pars[ORBITAL_FIT]:
        errors.extend(_validate_multilook(ORBITAL_FIT_LOOKS_X, n_cols, 'x'))
        errors.extend(_validate_multilook(ORBITAL_FIT_LOOKS_Y, n_rows, 'y'))

    return _raise_errors(errors)

def validate_reference_pixel_search_windows(n_cols: int, n_rows: int, 
                                            pars: Dict) -> Optional[bool]:
    """
    Validates that the reference pixel search windows provided by user
    fit within the scene being processed.

    Args:
        n_cols: Number of pixel columns (X) in the scene.
        n_rows: Number of pixel rows (Y) in the scene.
    
    Returns:
        True if the scene can accomodate the search windows (no overlap).

    Raises:
        ConfigException: If the scene cannot accomodate the search windows.
    """
    from math import floor

    errors = []
    refnx = pars[REFNX]
    refny = pars[REFNY]
    chip_size = pars[REF_CHIP_SIZE]
    
    x_windows = floor(n_cols/chip_size)
    if refnx > x_windows:
        errors.append(f"'{REFNX}' & '{REF_CHIP_SIZE}': search windows do not "
                      f"fit in scene on X axis (number of columns: {n_cols}). "
                      f"Reduce {REF_CHIP_SIZE} or {REFNX} so that {REFNX} "
                      f"is less than or equal to (columns / {REF_CHIP_SIZE}).")
    y_windows = floor(n_rows/chip_size)
    if refny > y_windows:
        errors.append(f"'{REFNY}' & '{REF_CHIP_SIZE}': search windows do not "
                      f"fit in scene on Y axis (number of rows: {n_rows}). "
                      f"Reduce {REF_CHIP_SIZE} or {REFNY} so that {REFNY} "
                      f"is less than or equal to (rows / {REF_CHIP_SIZE}).")
    
    return _raise_errors(errors)

def validate_gamma_headers(ifg_file_list: str, slc_file_list: str, 
                           slc_dir: str) -> Optional[bool]:
    """
    Validates that a pair of GAMMA headers exist for each provided
    GAMMA interferogram.

    Args:
        ifg_file_list: Path to the file listing filenames of interferograms.
        slc_file_list: Path to the file listing filenames of GAMMA headers.
        slc_dir: Path to directory containing GAMMA headers.

    Returns:
        True if there are exactly 2 headers for each interogram (one for
        each epoch).

    Raises:
        ConfigException: If there are 0 or more than 2 matching headers
            for an interferogram.
    """
    from pyrate.core.gamma import get_header_paths
    errors = []

    for ifg in parse_namelist(ifg_file_list):
        headers = get_header_paths(ifg, slc_file_list, slc_dir)
        if len(headers) < 2:
            errors.append(f"'{SLC_DIR}': Headers not found for interferogram "
                          "'{ifg}'.")

    return _raise_errors(errors)

def validate_coherence_files(ifg_file_list: str, pars: Dict) -> Optional[bool]:
    """
    Validates that there is a matching coherence file for each provided
    interferogram.

    Args:
        ifg_file_list: Path to file listing interferogram names.
        pars: The parameters dictionary.

    Returns:
        True if there is exactly 1 coherence file for each interferogram.

    Raises:
        ConfigException: If there are 0 or more than 1 matching coherence
            files for an interferogram.
    """
    errors = []

    for ifg in parse_namelist(ifg_file_list):
        paths = coherence_paths_for(ifg, pars)
        if not paths:
            errors.append(f"'{COH_FILE_DIR}': no coherence files found for "
                          f"intergerogram '{ifg}'.")
        elif len(paths) > 2:
            errors.append(f"'{COH_FILE_DIR}': found more than one coherence "
                          f"file for '{ifg}'. There must be only one "
                          f"coherence file per interferogram. Found {paths}.")

    return _raise_errors(errors)

def _get_ifg_information(ifg_file_list: str, obs_dir: str, crop_opts: Tuple) -> Tuple:
    """
    Retrieves spatial and temporal information from the provided interferograms.
    Requires the interferograms to exist in geotiff format.

    Args:
        ifg_file_list: Path to file containing list of interferogram file names.
        obs_dir: Path to observations directory.
        crop_opts: Crop options from parameters.

    Returns:
        Tuple containing extents (xmin, ymin, xmax, ymax), number of pixel
        columns, number of pixel rows, number of unique epochs and maximum
        time span of the data.
    """
    from pyrate.core.shared import Ifg, output_tiff_filename
    from pyrate.core.prepifg_helper import _get_extents
    from pyrate.core.algorithm import get_epochs
    ifg_paths = [os.path.join(obs_dir, ifg) for ifg in parse_namelist(ifg_file_list)]
    rasters = [Ifg(output_tiff_filename(f, obs_dir)) for f in ifg_paths]

    for r in rasters:
        if not r.is_open:
            r.open()

    # extents = xmin, ymin, xmax, ymax
    extents = _get_extents(rasters, crop_opts[0], crop_opts[1])
    epoch_list = get_epochs(rasters)[0]
    n_epochs = len(epoch_list.dates)
    max_span = max(epoch_list.spans)
    # Assuming resolutions have been verified to be the same.
    x_step = rasters[0].x_step
    y_step = rasters[0].y_step

    # Get the pixel bounds. Ifg/Raster objects do have 'ncols'/'nrows' 
    #  properties, but we'll calculate it off the extents we got above
    #  because these take into account the chosen cropping option (until
    #  the stack of interferograms is cropped it's not known what the 
    #  pixel dimensions will be).
    n_cols = abs(int(abs(extents[0] - extents[2]) / x_step))
    n_rows = abs(int(abs(extents[1] - extents[3]) / y_step))

    return extents, n_cols, n_rows, n_epochs, max_span

def _crop_opts(params: Dict) -> Tuple:
    """
    Convenience function for getting crop options from parameters.
    """
    from pyrate.core.prepifg_helper import CustomExts

    crop_opt = params[IFG_CROP_OPT]
    if crop_opt == 3:
        xfirst = params[IFG_XFIRST]
        yfirst = params[IFG_YFIRST]
        xlast = params[IFG_XLAST]
        ylast = params[IFG_YLAST]
        return crop_opt, CustomExts(xfirst, yfirst, xlast, ylast)

    return crop_opt, None

class ConfigException(Exception):
    """
    Default exception class for configuration errors.
    """
