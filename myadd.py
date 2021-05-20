#! /usr/bin/env python
from __future__ import print_function, division

import argparse
import os.path

from astropy.io import fits
from numba import njit, float64, prange
import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('fitsfile', nargs='+')
    parser.add_argument('--weight-suffix')
    parser.add_argument('--output', default='myadd.fits')
    parser.add_argument('--noclipfield', action='store_true')
    parser.add_argument('--beam-threshold', type=float, default=0)
    args = parser.parse_args()

    header = None
    imagesum = None
    weightsum = None

    for i, fitsfile in enumerate(args.fitsfile):
        print("Adding file %d/%d..." % (i+1, len(args.fitsfile)))

        try:
            image = fits.open(fitsfile)[0]
            if args.weight_suffix:
                path, ext = os.path.splitext(fitsfile)
                weights = fits.open(path + args.weight_suffix + ext)[0].data
            else:
                weights = image.data.copy()
                weights[:] = 1

            weights[~np.isfinite(weights)] = 0
            weights[~np.isfinite(image.data)] = 0

            idx = weights < args.beam_threshold
            weights[idx] = 0
            # weights[idx] *= np.exp(-(weights[idx] - args.beam_threshold)**2 / (2 * 0.04**2))

            # Square the weights
            weights *= weights

            image.data[~np.isfinite(image.data)] = 0
            image.data *= weights

            if imagesum is not None:
                imagesum += image.data
            else:
                imagesum = image.data

            if weightsum is not None:
                weightsum += weights
            else:
                weightsum = weights

            if header is None:
                header = image.header

        except IOError:
            print("Could not open %s (or its associated rms file)" % fitsfile)

    if not args.noclipfield:
        imagesum[weightsum < args.beam_threshold] = np.nan

    # Normalise
    imagesum /= weightsum
    hdu = fits.PrimaryHDU(imagesum, header=header)
    hdu.writeto(args.output, overwrite=True)

    # PB corrected image and weights file
    hdu = fits.PrimaryHDU(weightsum, header=header)
    path, ext = os.path.splitext(args.output)
    hdu.writeto(path + '-weights' + ext, overwrite=True)

if __name__ == '__main__':
    main()
