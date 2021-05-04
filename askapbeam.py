#! /usr/bin/env python
from __future__ import print_function, division

import argparse

from astropy.coordinates import SkyCoord
from astropy.io import fits
import astropy.units as units
import numpy as np

from astrobits.coordinates import fits_to_radec


parser = argparse.ArgumentParser()
parser.add_argument('--template', required=True)
parser.add_argument('--output', default=None)
args = parser.parse_args()

template = fits.open(args.template)[0]
lmbda = 299792458 / template.header['CRVAL4'] # might need to change to CRVAL3 depending on where central frequency is stored in image header
print("Lambda:", lmbda)

ras, decs = fits_to_radec(template)
ra0, dec0 = np.radians(template.header['CRVAL1']), np.radians(template.header['CRVAL2'])
coords = SkyCoord(ras.flatten(), decs.flatten(), unit=(units.radian, units.radian))
center = SkyCoord(ra0, dec0, unit=(units.radian, units.radian))
dists = np.reshape(coords.separation(center).radian, template.data.shape)

fwhm = (1.09 * lmbda) / 12
sigma = fwhm / (2 * np.sqrt(2 * np.log(2)))
beam = np.exp(-dists**2 / (2 * sigma**2))

# Special ASKAP fix for stokes I calculation
beam /= 2

template.data[:] = beam
template.writeto(args.output, overwrite=True)
