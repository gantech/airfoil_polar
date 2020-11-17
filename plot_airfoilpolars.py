import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import glob, pathlib
import airfoil_polar
import pandas as pd
from mpl_toolkits.mplot3d import Axes3D

def plot_all_airfoil_polar(af_polar_yaml, filename):

    afp = airfoil_polar.AirfoilTableDB(af_polar_yaml)
    afnames = sorted(list(afp.get_airfoils()))

    plt.style.use('subplot13')
    with PdfPages(filename) as pfpgs:
        for af in afnames:
            fig,axs = plt.subplots(1,3)
            af_data = afp.get_airfoil_data(af)
            axs[0].plot(af_data['aoa'], af_data['cl'])
            stall_angle = afp.lift_stall_angle(af)
            axs[0].plot(stall_angle, afp.get_aftable(af)(stall_angle,'cl'), '+', color='r')
            axs[1].plot(af_data['aoa'], af_data['cd'])
            #axs[1,0].plot(af_data['aoa'], af_data['cm'])
            axs[2].plot(af_data['aoa'], af_data['cl']/af_data['cd'])
            axs[0].set_title( af )
            axs[0].set_xlabel(r'$\alpha$')
            axs[1].set_xlabel(r'$\alpha$')
            axs[2].set_xlabel(r'$\alpha$')
            axs[0].set_ylabel(r'$C_l$')
            axs[1].set_ylabel(r'$C_d$')
            axs[2].set_ylabel(r'$C_l/C_d$')
            plt.tight_layout()
            pfpgs.savefig()
            plt.close(fig)

if __name__=="__main__":
  plot_all_airfoil_polar('iea15mw/ham2d/re03000000.yaml','iea15mw/ham2d/re03000000.pdf')
