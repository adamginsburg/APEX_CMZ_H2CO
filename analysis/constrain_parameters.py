"""
Functions for fitting temperature (and density and column) from the line ratio
plus whatever other constraints are available
"""
import inspect

import numpy as np
from scipy.ndimage.interpolation import map_coordinates
from astropy import units as u

from h2co_modeling import grid_fitter

class paraH2COmodel(object):

    def __init__(self, tbackground=2.73, gridsize=250):
        from pyspeckit_fitting import (texgrid303, taugrid303, texgrid321, taugrid321,
                                       texgrid322, taugrid322, hdr)

        self.texgrid303 = texgrid303
        self.taugrid303 = taugrid303
        self.texgrid321 = texgrid321
        self.taugrid321 = taugrid321
        self.texgrid322 = texgrid322
        self.taugrid322 = taugrid322
        self.hdr = hdr

        self.Tbackground = tbackground
        self.tline303a = ((1.0-np.exp(-np.array(self.taugrid303))) *
                          (self.texgrid303-self.Tbackground))
        self.tline321a = ((1.0-np.exp(-np.array(self.taugrid321))) *
                          (self.texgrid321-self.Tbackground))
        self.tline322a = ((1.0-np.exp(-np.array(self.taugrid322))) *
                          (self.texgrid322-self.Tbackground))

        zinds,yinds,xinds = np.indices(self.tline303a.shape)
        upsample_factor = np.array([250./self.tline303a.shape[0],
                                    250./self.tline303a.shape[1],
                                    250./self.tline303a.shape[2]], dtype='float')
        uzinds,uyinds,uxinds = upsinds = np.indices([x*us
                                                     for x,us in zip(self.tline303a.shape,
                                                                     upsample_factor)],
                                                   dtype='float')
        self.tline303 = map_coordinates(self.tline303a,
                                   upsinds/upsample_factor[:,None,None,None],
                                   mode='nearest')
        self.tline321 = map_coordinates(self.tline321a,
                                   upsinds/upsample_factor[:,None,None,None],
                                   mode='nearest')
        self.tline322 = map_coordinates(self.tline322a,
                                   upsinds/upsample_factor[:,None,None,None],
                                   mode='nearest')
    
        self.tline = {303: self.tline303,
                      321: self.tline321,
                      322: self.tline322}

        self.densityarr = ((uxinds + self.hdr['CRPIX1']-1)*self.hdr['CDELT1'] /
                      float(upsample_factor[2])+self.hdr['CRVAL1']) # log density
        self.columnarr  = ((uyinds + self.hdr['CRPIX2']-1)*self.hdr['CDELT2'] /
                      float(upsample_factor[1])+self.hdr['CRVAL2']) # log column
        self.temparr    = ((uzinds + self.hdr['CRPIX3']-1)*self.hdr['CDELT3'] /
                      float(upsample_factor[0])+self.hdr['CRVAL3']) # lin temperature
        self.drange = [self.densityarr.min(), self.densityarr.max()]
        self.crange = [self.columnarr.min(),  self.columnarr.max()]
        self.trange = [self.temparr.min(),    self.temparr.max()]
        self.darr = self.densityarr[0,0,:]
        self.carr = self.columnarr[0,:,0]
        self.tarr = self.temparr[:,0,0]

        # While the individual lines are subject to filling factor uncertainties, the
        # ratio is not.
        self.modelratio1 = self.tline321/self.tline303
        self.modelratio2 = self.tline322/self.tline321

        self.model_logabundance = np.log10(10**self.columnarr / u.pc.to(u.cm) /
                                           10**self.densityarr)

    def grid_getmatch_321to303(self, ratio, eratio):
            match,indbest,chi2r = grid_fitter.grid_getmatch(ratio, eratio,
                                                            self.modelratio1)
            return chi2r

    def grid_getmatch_322to321(self, ratio, eratio):
            match,indbest,chi2r = grid_fitter.grid_getmatch(ratio, eratio,
                                                            self.modelratio2)
            return chi2r

    def chi2_fillingfactor(self, tline, etline, lineid):
        """
        Return a chi^2 value for each model parameter treating the specified
        line brightness as a lower limit

        Parameters
        ----------
        tline : float
            The line brightness temperature
        lineid : int
            The line id, one of 303,321,322
        """
        chi2 = ((self.tline[lineid] - tline)/etline)**2 * (self.tline[lineid] < tline)
        return chi2

    def chi2_column(self, logh2column, elogh2column, h2coabundance, linewidth):

        h2fromh2co = np.log10(10**self.columnarr * (np.sqrt(np.pi) * linewidth)
                              / 10**h2coabundance)
        chi2_h2 = ((h2fromh2co-logh2column)/elogh2column)**2

        return chi2_h2

    def chi2_abundance(self, logabundance, elogabundance):
        model_logabundance = np.log10(10**self.columnarr / u.pc.to(u.cm) /
                                      10**self.densityarr)
        chi2X = ((model_logabundance-logabundance)/elogabundance)**2
        return chi2X

    def set_constraints(self,
                        taline303=None, etaline303=None,
                        taline321=None, etaline321=None,
                        taline322=None, etaline322=None,
                        logabundance=None, elogabundance=None,
                        logh2column=None, elogh2column=None,
                        ratio303321=None, eratio303321=None,
                        ratio321322=None, eratio321322=None,
                        linewidth=None):

        argspec=inspect.getargvalues(inspect.currentframe())
        for arg in argspec.args:
            if argspec.locals[arg] is not None:
                setattr(self, arg, argspec.locals[arg])

        self.chi2_X = (self.chi2_abundance(logabundance, elogabundance) 
                       if not any(arg is None for arg in (logabundance,
                                                          elogabundance))
                       else 0)

        self.chi2_h2 = (self.chi2_column(logh2column, elogh2column,
                                         logabundance, linewidth) 
                        if not
                        any(arg is None for arg in (logabundance, logh2column,
                                                      elogh2column, linewidth))
                        else 0)

        self.chi2_ff1 = (self.chi2_fillingfactor(taline303, etaline303, 303)
                         if not any(arg is None for arg in (taline303,
                                                            etaline303))
                         else 0)


        self.chi2_ff2 = (self.chi2_fillingfactor(taline321, etaline321, 321)
                         if not any(arg is None for arg in (taline321,
                                                            etaline321))
                         else 0)

        self.chi2_r303321 = (self.grid_getmatch_321to303(ratio303321,
                                                         eratio303321)
                             if not any(arg is None for arg in (ratio303321,
                                                                eratio303321))
                             else 0)

        self.chi2_r321322 = (self.grid_getmatch_321to303(ratio321322,
                                                         eratio321322)
                             if not any(arg is None for arg in (ratio321322,
                                                                eratio321322))
                             else 0)

        self.chi2 = (self.chi2_X + self.chi2_h2 + self.chi2_ff1 + self.chi2_ff2
                     + self.chi2_r321322 + self.chi2_r303321)

    def get_parconstraints(self):
        """
        """
        if not hasattr(self, 'chi2'):
            raise AttributeError("Run set_constraints first")

        row = {}

        indbest = np.argmin(self.chi2)
        deltachi2b = (self.chi2-self.chi2.min())
        for parname,pararr in zip(('temperature','column','density'),
                                  (self.temparr,self.columnarr,self.densityarr)):
            row['{0}_chi2'.format(parname)] = pararr.flat[indbest]
            OK = deltachi2b<1
            if np.count_nonzero(OK) > 0:
                row['{0:1.1s}min1sig_chi2'.format(parname)] = pararr[OK].min()
                row['{0:1.1s}max1sig_chi2'.format(parname)] = pararr[OK].max()
            else:
                row['{0:1.1s}min1sig_chi2'.format(parname)] = np.nan
                row['{0:1.1s}max1sig_chi2'.format(parname)] = np.nan

        return row
