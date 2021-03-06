import numpy as np
from astropy import units as u
from paths import h2copath,figurepath,hpath
import copy
import os
import aplpy
import pylab as pl
import matplotlib
from astropy.io import fits
from masked_cubes import cube303m, cube321m, cube303msm, cube321msm, sncube, sncubesm
from ratio_cubes import ratiocube_303321, ratiocubesm_303321
from piecewise_rtotem import pwtem
from astropy import log
import paths
matplotlib.rc_file(paths.pcpath('pubfiguresrc'))

pl.ioff()
pl.close(1)
pl.close(2)

cm = matplotlib.cm.RdYlBu_r
cm.set_bad('#888888')
figsize = (20,10)

small_recen = dict(x=0.3, y=-0.03,width=1.05,height=0.27)
big_recen = dict(x=0.55, y=-0.075,width=2.3,height=0.40)

max_ratio = 0.51

# Old version: integrated ratio maps (this is still used in publication)
for weighted in ("","_weighted","_masked_weighted"):
    for bl in ("_bl",""):
        for smooth in ("","_smooth",):#"_vsmooth"):
            ratio1 = 'H2CO_321220_to_303202{0}{1}_integ{2}.fits'.format(smooth,bl,weighted)
            ratio2 = 'H2CO_322221_to_303202{0}{1}_integ{2}.fits'.format(smooth,bl,weighted)


            for ii,ratio in enumerate((ratio1, ratio2)):
                log.info(ratio)
                fig = pl.figure(ii+1, figsize=figsize)
                fig.clf()
                F = aplpy.FITSFigure(os.path.join(h2copath, ratio),
                                     convention='calabretta', figure=fig)
                F.show_colorscale(cmap=cm, vmin=0, vmax=max_ratio)
                F.add_colorbar()
                F.tick_labels.set_xformat('d.dd')
                F.tick_labels.set_yformat('d.dd')
                F.recenter(**small_recen)
                F.save(os.path.join(figurepath,
                                    'big_maps',
                                    ratio.replace(".fits",".pdf")))
                F.recenter(**big_recen)
                F.save(os.path.join(figurepath,
                                    'big_maps',
                                    "big_"+ratio.replace(".fits",".pdf")))

                dustcolumn = '/Users/adam/work/gc/gcmosaic_column_conv36.fits'
                F.show_contour(dustcolumn,
                               levels=[5], colors=[(0,0,0,0.5)], zorder=15,
                               alpha=0.5,
                               linewidths=[0.5],
                               layer='dustcontour')

                F.save(os.path.join(figurepath,
                                    'big_maps',
                                    "big_"+ratio.replace(".fits","_withcontours.pdf")))

# Dendrogram mean ratios
for weighted in ("","weighted"):
    for smooth in ("","_smooth",):#"_vsmooth"):
        ratio = 'RatioCube_DendrogramObjects{0}_Piecewise_{1}mean.fits'.format(smooth,weighted)
        log.info(ratio)

        fig = pl.figure(1, figsize=figsize)
        fig.clf()
        F = aplpy.FITSFigure(os.path.join(h2copath, ratio),
                             convention='calabretta', figure=fig)
        F.show_colorscale(cmap=cm, vmin=0, vmax=max_ratio)
        F.add_colorbar()
        F.tick_labels.set_xformat('d.dd')
        F.tick_labels.set_yformat('d.dd')
        F.recenter(**small_recen)
        F.save(os.path.join(figurepath,
                            'big_maps',
                            ratio.replace(".fits",".pdf")))
        F.recenter(**big_recen)
        F.save(os.path.join(figurepath,
                            'big_maps',
                            "big_"+ratio.replace(".fits",".pdf")))



# "new" version: 20 km/s slices
# (used for analysis, not for publication)

vcuts = np.arange(-60,141,20)

fig = pl.figure(1, figsize=figsize)
for cube,sn,smooth in zip((ratiocube_303321, ratiocubesm_303321),
                          (sncube, sncubesm),
                          ("","_smooth",)):#"_vsmooth"):
    for vrange in zip(vcuts[:-1], vcuts[1:]):
        proj = cube.spectral_slab(*(vrange*u.km/u.s)).mean(axis=0)
        fig.clf()
        F = aplpy.FITSFigure(proj.hdu, convention='calabretta', figure=fig)
        F.show_colorscale(cmap=cm, vmin=0.1, vmax=0.65)
        F.add_colorbar()
        F.tick_labels.set_xformat('d.dd')
        F.tick_labels.set_yformat('d.dd')
        #F.recenter(**small_recen)
        #F.save(os.path.join(figurepath, ratio.replace(".fits",".pdf")))
        F.recenter(**big_recen)
        F.add_label(1.60, -0.22,
                    "$v=[{0}, {1}]$ km s$^{{-1}}$".format(vrange[0],vrange[1]),
                    color='w', size=14, zorder=20,
                    horizontalalignment='left')
        F.save(os.path.join(figurepath,
                            'big_maps',
                            "big_H2CO_321220_to_303202{0}_bl_{1}to{2}.pdf"
                            .format(smooth,int(vrange[0]),int(vrange[1]))
                           )
              )

fig = pl.figure(1, figsize=figsize)
for (cubehi,cubelo),sn,smooth in zip(((cube303m,cube321m),
                                      (cube303msm,cube321msm)),
                                     (sncube, sncubesm),
                                     ("","_smooth",)):#"_vsmooth"):
    for vrange in zip(vcuts[:-1], vcuts[1:]):
        projhi = cubehi.spectral_slab(*(vrange*u.km/u.s)).mean(axis=0)
        projlo = cubelo.spectral_slab(*(vrange*u.km/u.s)).mean(axis=0)
        proj = projlo/projhi
        hdu = fits.PrimaryHDU(data=proj.decompose().value,
                              header=projlo.hdu.header)
        fig.clf()
        F = aplpy.FITSFigure(hdu, convention='calabretta', figure=fig)
        cm = matplotlib.cm.RdYlBu_r
        cm.set_bad('#888888')
        F.show_colorscale(cmap=cm, vmin=0.1, vmax=0.65)
        F.add_colorbar()
        F.tick_labels.set_xformat('d.dd')
        F.tick_labels.set_yformat('d.dd')
        #F.recenter(**small_recen)
        #F.save(os.path.join(figurepath, ratio.replace(".fits",".pdf")))
        F.recenter(**big_recen)
        F.add_label(1.60, -0.22,
                    "$v=[{0}, {1}]$ km s$^{{-1}}$".format(vrange[0],vrange[1]),
                    color='w', size=14, zorder=20,
                    horizontalalignment='left')
        F.save(os.path.join(figurepath,
                            'big_maps',
                            "big_H2CO_321220_to_303202{0}_bl_{1}to{2}_slabratio.pdf"
                            .format(smooth,int(vrange[0]),int(vrange[1]))
                           )
              )

        tproj = np.copy(proj)
        tproj[np.isfinite(proj)] = pwtem(proj[np.isfinite(proj)].value)
        hdu = fits.PrimaryHDU(tproj, projhi.hdu.header)
        fig.clf()
        F = aplpy.FITSFigure(hdu,
                             convention='calabretta',
                             figure=fig)

        #cm = copy.copy(pl.cm.rainbow)
        cm = copy.copy(pl.cm.RdYlBu_r)
        cm.set_bad('#888888')
        #cm.set_bad((0.5,0.5,0.5,0.5))
        F.show_colorscale(cmap=cm,vmin=15,vmax=200)
        F.set_tick_labels_format('d.dd','d.dd')
        peaksn = sn.spectral_slab(*(vrange*u.km/u.s)).max(axis=0)
        peaksn[(peaksn<0) | np.isnan(peaksn)] = 0
        color = (0.5,)*3 # should be same as background #888
        nlevs = 50
        F.show_contour(peaksn.hdu,
                       levels=[0]+np.logspace(0.20,1,nlevs).tolist(),
                       colors=[(0.5,0.5,0.5,1)] + [color + (alpha,)
                                                   for alpha in
                                                   np.exp(-(np.logspace(0.20,1,nlevs)-10**0.2)**2/(1.0**2*2.))],
                       filled=True,
                       zorder=10, convention='calabretta')
        F.add_colorbar()
        F.add_label(1.60, -0.22,
                    "$v=[{0}, {1}]$ km s$^{{-1}}$".format(vrange[0],vrange[1]),
                    color='w', size=14,
                    horizontalalignment='left',
                    zorder=20)
        F.colorbar.set_axis_label_text('T (K)')
        F.recenter(**big_recen)
        F.save(os.path.join(figurepath,
                            'big_maps',
                            'big_lores{0}_tmap_greyed_{1}to{2}_slabratio.png'.format(smooth,
                                                                           int(vrange[0]),
                                                                           int(vrange[1]))))
        log.info(os.path.join(figurepath,
                              'big_maps',
                              'big_lores{0}_tmap_greyed_{1}to{2}_slabratio.png'.format(smooth,
                                                                             int(vrange[0]),
                                                                             int(vrange[1]))))


fig = pl.figure(1, figsize=figsize)
for cube,sn,smooth in zip((ratiocube_303321, ratiocubesm_303321),
                          (sncube, sncubesm),
                          ("","_smooth",)):#"_vsmooth"):
    for vrange in zip(vcuts[:-1], vcuts[1:]):
        fig.clf()
        proj = cube.spectral_slab(*(vrange*u.km/u.s)).mean(axis=0)
        tproj = np.copy(proj)
        tproj[np.isfinite(proj)] = pwtem(proj[np.isfinite(proj)].value)
        hdu = fits.PrimaryHDU(tproj, proj.hdu.header)
        hdu.writeto(hpath("tmap{0}_{1}to{2}".format(smooth,
                                                    int(vrange[0]),
                                                    int(vrange[1]))),
                    clobber=True)
        F = aplpy.FITSFigure(hdu,
                             convention='calabretta',
                             figure=fig)

        #cm = copy.copy(pl.cm.rainbow)
        #cm.set_bad((0.5,0.5,0.5,0.5))
        cm = copy.copy(pl.cm.RdYlBu_r)
        cm.set_bad('#888888')
        F.show_colorscale(cmap=cm,vmin=15,vmax=200)
        F.set_tick_labels_format('d.dd','d.dd')
        peaksn = sn.spectral_slab(*(vrange*u.km/u.s)).max(axis=0)
        peaksn[(peaksn<0) | np.isnan(peaksn)] = 0
        color = (0.5,)*3 # should be same as background #888
        nlevs = 50
        F.show_contour(peaksn.hdu,
                       levels=[0]+np.logspace(0.20,1,nlevs).tolist(),
                       colors=[(0.5,0.5,0.5,1)] + [color + (alpha,)
                                                   for alpha in
                                                   np.exp(-(np.logspace(0.20,1,nlevs)-10**0.2)**2/(1.0**2*2.))],
                       filled=True,
                       zorder=10, convention='calabretta')
        F.add_colorbar()
        F.add_label(1.60, -0.22,
                    "$v=[{0}, {1}]$ km s$^{{-1}}$".format(vrange[0],vrange[1]),
                    color='w', size=14, zorder=20,
                    horizontalalignment='left')
        F.colorbar.set_axis_label_text('T (K)')
        F.recenter(**big_recen)
        F.save(os.path.join(figurepath,
                            'big_maps',
                            'big_lores{0}_tmap_greyed_{1}to{2}.png'.format(smooth,
                                                                           int(vrange[0]),
                                                                           int(vrange[1]))))
        log.info(os.path.join(figurepath,
                              'big_maps',
                              'big_lores{0}_tmap_greyed_{1}to{2}.png'.format(smooth,
                                                                             int(vrange[0]),
                                                                             int(vrange[1]))))



        


