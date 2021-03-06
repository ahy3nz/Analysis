import pdb
import numpy as np
from collections import OrderedDict
from scipy.optimize import curve_fit
import MDAnalysis as mda
import MDAnalysis.analysis.waterdynamics
import pandas as pd
import time
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt

######################
## Use mdanalysis to study rotational relaxation of water molecules
## Close to the interface
## Note the use of a mol2 to remember accurate resnames (pdb bad)
## and to remember bonds (gro bad)
#####################

def stretched_exponential(x_data, a, tau, beta):
    """ Function used to get decay times for water relaxation

    Parameters
    ----------
    x_data : times 
    a : exponential prefactor 
    tau : rotational relaxation time
    beta : exponent in the exponential term


    References
    ----------
    Sciortino, P., Gallo, P., Tartaglia, P., Chen, S-H. 1996. Supercooled water
        and the kinetic glass transition
    Castrillon, S., Giovambattista, N., Aksay, I.A., Debenedetti, P. 2009. Effect
        of Surface Polarity on the Structure and Dynamics of WAter in Nanoscale
        Confinement
        """
    return a * np.exp(-((x_data/tau)**beta))

def main(mol2='extra.mol2', traj='npt_80-100ns.xtc'):
    uni = mda.Universe(mol2, traj, in_memory=True)
    #uni = mda.Universe('extra.mol2', 'last5ns.xtc', in_memory=True)
    midplane = uni.dimensions[2]/2
    top_phosphates = [a for a in uni.atoms if 'P' in a.name[0] 
                        and a.position[2] > midplane]
    bot_phosphates = [a for a in uni.atoms if 'P' in a.name[0] 
                        and a.position[2] < midplane]
    bot_interface = np.mean([a.position[2] for a in bot_phosphates])
    top_interface = np.mean([a.position[2] for a in top_phosphates])

    frame_to_time = 10 # ps
    corr_length = 500 # frames
    selection = '(resname HOH or resname SOL) and prop z <= {0} and prop z >= {1}'.format(top_interface+10, bot_interface-10)
    #selection = '(resname HOH or resname SOL)'
    # Water orientational relaxation
    wor_analysis = mda.analysis.waterdynamics.WaterOrientationalRelaxation(uni, 
                    selection, 0, uni.trajectory.n_frames, corr_length)
    wor_analysis.run()

    #now we print the data ready to plot. The first two columns are WOR_OH vs t plot,
    #the second two columns are WOR_HH vs t graph and the third two columns are WOR_dip vs t graph
    #for WOR_OH, WOR_HH, WOR_dip in wor_analysis.timeseries:
        #print("{time} {WOR_OH} {time} {WOR_HH} {time} {WOR_dip}".format(time=time, WOR_OH=WOR_OH, WOR_HH=WOR_HH,WOR_dip=WOR_dip))


    frames = np.arange(0, corr_length, dtype=int) 
    times = frames * frame_to_time
    oh_timeseries =[column[0] for column in wor_analysis.timeseries]
    hh_timeseries =[column[1] for column in wor_analysis.timeseries]
    dip_timeseries =[column[2] for column in wor_analysis.timeseries]

    popt, pcov = curve_fit(stretched_exponential, times, dip_timeseries)
    stretched_exp_params = OrderedDict()
    stretched_exp_params['A'] = popt[0]
    stretched_exp_params['tau'] = popt[1]
    stretched_exp_params['beta'] = popt[2]
    computed_corr = stretched_exponential(times, *popt)

    np.savetxt('oh_corr.dat',np.column_stack((frames, times, oh_timeseries)), 
            header="frames, times, oh_corr")

    np.savetxt('hh_corr.dat',np.column_stack((frames, times, hh_timeseries)), 
            header="frames, times, hh_corr")

    np.savetxt('dip_corr.dat',np.column_stack((frames, times, dip_timeseries)), 
            header="frames, times, dip_corr")



    plt.figure(1,figsize=(18, 6))

    #WOR OH
    plt.subplot(131)
    plt.xlabel('time')
    plt.ylabel('WOR')
    plt.title('WOR OH')
    plt.plot(times,[column[0] for column in wor_analysis.timeseries])

    #WOR HH
    plt.subplot(132)
    plt.xlabel('time')
    plt.ylabel('WOR')
    plt.title('WOR HH')
    plt.plot(times,[column[1] for column in wor_analysis.timeseries])

    #WOR dip
    plt.subplot(133)
    plt.xlabel('time')
    plt.ylabel('WOR')
    plt.title('WOR dip')
    plt.plot(times,[column[2] for column in wor_analysis.timeseries], label='Computed')
    plt.plot(times, computed_corr, linestyle ='--', color='red', label='fit')
    plt.legend()

    plt.savefig('wor.png')
    
    return stretched_exp_params

if __name__ == "__main__":
    main()

def bulk_main(mol2='extra.mol2', traj='npt_80-100ns.xtc'):
    uni = mda.Universe(mol2, traj, in_memory=True)
    #uni = mda.Universe('extra.mol2', 'last5ns.xtc', in_memory=True)
    midplane = uni.dimensions[2]/2
    top_phosphates = [a for a in uni.atoms if 'P' in a.name[0] 
                        and a.position[2] > midplane]
    bot_phosphates = [a for a in uni.atoms if 'P' in a.name[0] 
                        and a.position[2] < midplane]
    bot_interface = np.mean([a.position[2] for a in bot_phosphates])
    top_interface = np.mean([a.position[2] for a in top_phosphates])

    frame_to_time = 10 # ps
    corr_length = 500 # frames
    #selection = '(resname HOH or resname SOL) and prop z <= {0} and prop z >= {1}'.format(top_interface+10, bot_interface-10)
    selection = '(resname HOH or resname SOL)'
    # Water orientational relaxation
    wor_analysis = mda.analysis.waterdynamics.WaterOrientationalRelaxation(uni, 
                    selection, 0, uni.trajectory.n_frames, corr_length)
    wor_analysis.run()

    #now we print the data ready to plot. The first two columns are WOR_OH vs t plot,
    #the second two columns are WOR_HH vs t graph and the third two columns are WOR_dip vs t graph
    #for WOR_OH, WOR_HH, WOR_dip in wor_analysis.timeseries:
        #print("{time} {WOR_OH} {time} {WOR_HH} {time} {WOR_dip}".format(time=time, WOR_OH=WOR_OH, WOR_HH=WOR_HH,WOR_dip=WOR_dip))


    frames = np.arange(0, corr_length, dtype=int) 
    times = frames * frame_to_time
    oh_timeseries =[column[0] for column in wor_analysis.timeseries]
    hh_timeseries =[column[1] for column in wor_analysis.timeseries]
    dip_timeseries =[column[2] for column in wor_analysis.timeseries]

    popt, pcov = curve_fit(stretched_exponential, times, dip_timeseries)
    stretched_exp_params = OrderedDict()
    stretched_exp_params['A'] = popt[0]
    stretched_exp_params['tau'] = popt[1]
    stretched_exp_params['beta'] = popt[2]
    computed_corr = stretched_exponential(times, *popt)

    np.savetxt('oh_corr_bulk.dat',np.column_stack((frames, times, oh_timeseries)), 
            header="frames, times, oh_corr")

    np.savetxt('hh_corr_bulk.dat',np.column_stack((frames, times, hh_timeseries)), 
            header="frames, times, hh_corr")

    np.savetxt('dip_corr_bulk.dat',np.column_stack((frames, times, dip_timeseries)), 
            header="frames, times, dip_corr")



    plt.figure(1,figsize=(18, 6))

    #WOR OH
    plt.subplot(131)
    plt.xlabel('time')
    plt.ylabel('WOR')
    plt.title('WOR OH')
    plt.plot(times,[column[0] for column in wor_analysis.timeseries])

    #WOR HH
    plt.subplot(132)
    plt.xlabel('time')
    plt.ylabel('WOR')
    plt.title('WOR HH')
    plt.plot(times,[column[1] for column in wor_analysis.timeseries])

    #WOR dip
    plt.subplot(133)
    plt.xlabel('time')
    plt.ylabel('WOR')
    plt.title('WOR dip')
    plt.plot(times,[column[2] for column in wor_analysis.timeseries], label='Computed')
    plt.plot(times, computed_corr, linestyle ='--', color='red', label='fit')
    plt.legend()

    plt.savefig('wor_bulk.png')
    
    return stretched_exp_params

