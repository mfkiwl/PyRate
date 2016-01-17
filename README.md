# PyRate - a Python tool for RAte and Time-series Estimation

PyRate is a Python tool for estimating the average rate (velocity) and incremental time-series of surface movement for every pixel in a stack of images generated by interferometric processing of Synthetic Aperture Radar (InSAR) data. PyRate is a partial Python translation of [Pirate](http://homepages.see.leeds.ac.uk/~earhw/software/pirate/), a MATLAB tool developed at the University of Leeds.


## Dependencies:

- [SciPy](www.scipy.org)
- [GDAL](www.gdal.org) a compiled version is included in the codebase
- [NetworkX](https://pypi.python.org/pypi/networkx)
- [pyproj](https://pypi.python.org/pypi/pyproj)
- [nose](https://pypi.python.org/pypi/nose/)
- [pytest](https://pypi.python.org/pypi/pytest)
- [sphinx](http://sphinx-doc.org/) for building the docs.
- [luigi](https://pypi.python.org/pypi/luigi) for controlling batch jobs.
- [parmap](https://pypi.python.org/pypi/parmap/1.2.0) a python multiprocessing wrapper, also included in the code

For the viewer you will also need

- [Flask](http://flask.pocoo.org/)
- [Pillow](https://pypi.python.org/pypi/Pillow)
- [netCDF4](https://pypi.python.org/pypi/netCDF4)
- a web browser.

## Clone the repo:

Clone the repo:    

    git clone https://github.com/GeoscienceAustralia/PyRate.git
    
This will prompt for your github username and password. Once you have entered them and you have access to this repo, `PyRate` will clone in your current directory. 

## Virtualenv setup for `PyRate`
(This is broken at the moment due to GDAL. Please use anaconda instructions below)

It is recommended that you create a `virtualenv` to run the `tlda` code. 

These instructions are for `ubuntu 14.04` and is expected to work for most newer versions of `ubuntu`. The `virtualenv` and the requirements can be installed using the following steps.

    sudo pip install virtualenv
    sudo apt-get -y build-dep matplotlib  # then enter your root password
    virtualenv -p python2.7 ~/pyrate_venv
    source ~/pyrate_venv/bin/activate   

Note, in the above, the first command `sudo apt-get -y build-dep matplotlib` installs all the build dependencies for `matplotlib`.

Once inside the `virtualenv`, navigate to the `PyRate` code:
    
    cd PyRate # This is where the requirements.txt exists
    pip install -r requirements.txt

## Anaconda setup for `PyRate`

####  Install anaconda:

On 64bit linux:
    
    bash Anaconda2-2.4.1-Linux-x86_64.sh

Please accept all defaults. This will install anaconda in the `~/anaconda2` directory.
 
You will need to download and install the appropriate version for your OS. The following instructions are for ubuntu 14.04 and are exptect to work for most versions of ubuntu.

#### Create the `pyrate` environment
    
    ~/anaconda2/bin/conda create --name pyrate --file /path/to/PyRate/requirements_conda.txt

#### Activate the `pyrate` environment

    source ~/anaconda2/bin/activate pyrate
    
#### Install `luigi`
    pip install luigi==1.3.0
    
The last step is necessary because conda does not contain `luigi`.

### Deactivate
Once you are done using `PyRate` you could deactivate from the conda env using: 

    source deactivate

#### Back to main anaconda if you need to:
    
    source activate /home/user/anaconda2
    
## Setting up the 'PYRATEPATH' environment variable

You need to add the directory containing the `pyrate` folder to the *PYTHONPATH* environment variable.

The environment variable *PYRATEPATH* needs to point to the folder where you put the test data. This is how I set up my environment variable:

	export PYRATEPATH="/home/sudipta/GA/PyRate"
	export PYTHONPATH=$PYRATEPATH/:$PYTHONPATH

	
## Documentation

The [Sphinx](http://sphinx-doc.org/) documenation of the scripts can be found under the main documentation tree for the project, which is found in the top level folder *doc*. To build the documentation do

	apidoc
	make html

The documentation will be generated in *doc/build*. The main entry point is *index.html*.


## Tests

Tests use [unittest](http://pythontesting.net/framework/unittest/unittest-introduction/) and can be found in *pyrate/tests*.

To run the tests, use the following command inside the `PyRate` directory:
		
	cd PyRate
	nosetests --nologcapture
	
Or you can use `unittest discover`:

	cd PyRate
	python -m unittest discover pyrate/

## Basic Usage Instructions

The runnable programs can be found in *pyrate/scripts*.

The steps are:

1. Edit the config file
1. Data formatting
1. Image transformations
1. PyRate workflow

### Config file:

TODO

### Data formatting:

The utility script *converttogtif.py* is provided to convert geocoded unwrapped interferograms in ROI_PAC or GAMMA format into a GeoTIFF format usable by PyRate.

	python <full_path>/converttogtif.py <CONFIG_FILE>

The script will determine the input format from the value specified at the *processor:* keyword in the config file (0: ROI\_PAC; 1: GAMMA)

A GAMMA translation requires a geographic DEM header file (\*.dem.par) and SLC parameter files (\*.slc.par) for both master and slave images to extract metadata required for the formatting. Therefore three header files are needed to format each geocoded unwrapped GAMMA interferogram <GAMMA_FILE>. The path and name of the DEM header file are specified in the config file under the *demHeaderFile:* keyword. The SLC parameter files should be in the same location as the interferogram file and are found automatically by date string pattern matching.

A ROI\_PAC translation requires a header/resource file (*.rsc* extension) for the geocoded unwrapped ROI_PAC interferogram (in the same directory) and either the geographic projection (e.g. 'WGS84') specified as an option or a header/resource file for the geographic DEM containing the geographic projection in the parameter DATUM:


### Image transformations:

This separate step of multi-looking (resampling) and cropping the images is handled with *run_prepifg.py*.

For command line options/help:

	python <full_path>/run_prepifg.py -h

The *run_prepifg.py* script requires the PyRate runtime configuration file. If a config file is not provided as an arg, the script will look for 'pyrate.conf' in the current directory.  


### PyRate workflow:

This is the core of the processing tools, handled with run_pyrate.py.

For command line options/help:


	python <full_path>/run_pyrate.py -h


The *run_pyrate.py* script also requires the PyRate runtime configuration file. As with the previous step, if a config file is not provided as an arg, the script will look for *pyrate.conf* by default.


### Running the viewer

You run the viewer from *pyrate/viewer/web.py" and passing the directory containing the (geotif) files you want to look at as the first command line parameter. For example:

	python pyrate/viewer/web.py /path/to/tifs

The program looks for a file *test.ncdf* (specified by `pyrate.viewer.datamanager.IMAGE_STACK_FILE_NAME`) in */path/to/tifs* and if it cannot find it, it will create it from all the files with the tif extension in that directory. It will create (or overwrite) the file *na_frequency.png* at the same time.

These two files will remain once the program exits and **WILL NOT BE AUTOMATICALLY RECREATED IF THE TIFF FILES CHANGE**. That is, one must manually remove *test.ncdf* to cause recreation of it.

## Todos

- NCI/GA contact details
- description of what the software does
- Licensing information
