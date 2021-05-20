#! /usr/bin/env python
from __future__ import division, print_function

import argparse
import os.path

from astropy.io import fits


parser = argparse.ArgumentParser()
parser.add_argument('--image', required=True)
parser.add_argument('--beam', required=True)
args = parser.parse_args()

image = fits.open(args.image)[0]
beam = fits.open(args.beam)[0]

image.data /= beam.data

prefix = os.path.splitext(args.image)[0]
image.writeto(prefix + '-pb.fits', overwrite=True)
