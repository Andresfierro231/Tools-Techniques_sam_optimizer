SAM - Lite
===

SAM is a MOOSE-application code designed for system level analysis of advanced reactors.
The SAM lite-version executable contained in this package was built from release 2024-12-08.

# Installation

## Prerequisites

### Conda

The SAM executable relies on Conda for distribution.
Please refer to the MOOSE website for information on setting up your system to utilize the Conda
MOOSE environment: https://mooseframework.inl.gov/getting_started/installation/conda.html

## Install

Please download the tar file alongside this README file and complete the following commands:

```bash
#Create the conda SAM environment
conda config --set ssl_verify False
conda create -n SAM -q -y
#Activate the SAM environment
conda activate SAM
#Install SAM
conda install --use-local sam-2025_01_29_lite-build_0.conda
conda install moose-dev=2024.12.23=mpich -y
```

## Testing

To test the installation of SAM, run:

```bash
#Activate the SAM environment
conda activate SAM
#Test the executable
sam-opt --help
```
W10: Warning: Changing a readonly file                        