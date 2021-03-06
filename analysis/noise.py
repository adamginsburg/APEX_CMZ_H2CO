from masked_cubes import (cube303, cube303sm, cube303m, cube321m, cube303msm,
                          cube321msm, cube321, cube321sm)
from spectral_cube import SpectralCube,BooleanArrayMask
from astropy.io import fits
from numpy.lib.stride_tricks import as_strided
from paths import mpath
import numpy as np
import time
from astropy import log

t0 = time.time()

noise_fn = mpath('APEX_H2CO_merge_high_plait_all_noise.fits')

noise = fits.getdata(noise_fn)
nhits = fits.getdata(mpath('APEX_H2CO_merge_high_nhits.fits'))
noise[nhits<20] = np.nan
noise_cube = as_strided(noise, shape=cube303m.shape, strides=(0,)+noise.strides)
noisehdr = fits.getheader(noise_fn)

sm_noise = fits.getdata(mpath('APEX_H2CO_merge_high_plait_all_smooth_noise.fits'))
sm_noise[nhits<20] = np.nan
sm_noise_cube = as_strided(sm_noise, shape=cube303msm.shape,
                           strides=(0,)+sm_noise.strides)

# Cubes masked with noise cube == OK
# (can I make this lazier?)
noisefinite = np.isfinite(noise) # stride length changes for bools?
sm_noisefinite = np.isfinite(sm_noise)
cube303nm = cube303.with_mask(BooleanArrayMask(as_strided(noisefinite,
                                                          shape=cube303.shape,
                                                          strides=(0,)+noisefinite.strides),
                                               cube303.wcs))
cube303nmsm = cube303sm.with_mask(BooleanArrayMask(as_strided(sm_noisefinite,
                                                          shape=cube303sm.shape,
                                                          strides=(0,)+sm_noisefinite.strides),
                                                   cube303sm.wcs))

cube321nm = cube321.with_mask(BooleanArrayMask(as_strided(noisefinite,
                                                          shape=cube321.shape,
                                                          strides=(0,)+noisefinite.strides),
                                               cube321.wcs))
cube321nmsm = cube321sm.with_mask(BooleanArrayMask(as_strided(sm_noisefinite,
                                                          shape=cube321sm.shape,
                                                          strides=(0,)+sm_noisefinite.strides),
                                                   cube321sm.wcs))

log.debug("Noise creation took {0:0.1f} seconds".format(time.time()-t0))
