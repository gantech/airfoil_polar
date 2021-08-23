import os, glob, re, yaml, glob
import numpy as np
import pandas as pd
import pathlib
import shutil, os
import cst

#Ham2D inputs

def get_ref_af_y ( af_file ):
    """Get the y coordinates for the reference airfoil for 
       a cosine distribution in x"""
    af = cst.AirfoilShape.from_txt_file(af_file)
    mod_af = cst.AirfoilShape.from_cst_parameters(af.cst().cst_lower, af.te_lower, af.cst().cst_upper, af.te_upper)
    return mod_af.yco

def get_nearest_ref_af(x,y):
    """Get nearest reference airfoil for a given set of airfoil coordinates"""
    af = cst.AirfoilShape(x,y)
    mod_af = cst.AirfoilShape.from_cst_parameters(af.cst().cst_lower,
                                                  af.te_lower,
                                                  af.cst().cst_upper,
                                                  af.te_upper)
    ref_afs = glob.glob('ref_inputs/automesh/usr_inputs/afs/*')
    ref_afs_diff = [ np.linalg.norm(get_ref_af_y(af)-mod_af.yco) for af in ref_afs ]
    nearest_af = ref_afs[np.argmin(ref_afs_diff)]
    return nearest_af.split('/')[-1]

def get_ref_automesh_inputs(af_name):
    usr_inputs = pd.read_csv('ref_inputs/automesh/usr_inputs/usr_inputs_{}.txt'.format(af_name.lower()),header=None,index_col=0,sep='\s+')
    return usr_inputs

def write_ham2d_mesh_input(x,y,dirname,afname,reynolds_no):
    pathlib.Path(dirname).mkdir(exist_ok=True)

    nearest_af = get_nearest_ref_af(x, y)
    usr_inputs = get_ref_automesh_inputs(nearest_af)
    usr_inputs.loc['inputfile'] = '{}.dat'.format(afname)
    usr_inputs.to_csv(dirname+'/usr_inputs.txt',sep=' ',header=None)

    with pathlib.Path(dirname+'/user_spacing_override.txt').open('w') as f:
        f.write('mode 1 \n')
        f.write('Re {:e} \n'.format(reynolds_no))
        f.write('charlen 1 \n')
        f.write('yPlus 2.0 \n')
        f.write('OBdelta 3.0 \n')

    af = cst.AirfoilShape(x,y)
    mod_af = cst.AirfoilShape.from_cst_parameters(af.cst().cst_lower,
                                                  af.te_lower,
                                                  af.cst().cst_upper,
                                                  af.te_upper)
    
    interp_x = mod_af.xco
    interp_y = mod_af.yco
    with pathlib.Path(dirname+'/{}.dat'.format(afname)).open('w') as f:
        npts = np.size(interp_x)
        for i in range(npts):
            f.write('{}    {}\n'.format(interp_x[i], interp_y[i]))

    shutil.copy(pathlib.Path('ref_inputs/automesh/user_smoothing.txt'),pathlib.Path(dirname+'/user_smoothing.txt'))
    shutil.copy(pathlib.Path('ref_inputs/automesh/user_stretch.txt'),pathlib.Path(dirname+'/user_stretch.txt'))


def write_ham2d_solver_input(dirname,alpha,reynolds_no,mach=0.1):
    hinp = pd.read_csv('ref_inputs/ham2d/input.hamstr',sep='=',header=None,index_col=0)
    hinp.loc['Mach'] = mach
    hinp.loc['alpha'] = alpha
    hinp.loc['rey'] = reynolds_no
    hinp.to_csv(dirname+'/input.hamstr',sep='=',header=None)

    shutil.copy(pathlib.Path('ref_inputs/ham2d/input.grv'),pathlib.Path(dirname+'/input.grv'))

def create_ham2d_input_files(dir_name, af_files, re=[3e6,6e6,9e6,12e6], aoa=np.linspace(-4,20,25)):
    pathlib.Path(dir_name).mkdir(exist_ok=True)
    pathlib.Path(dir_name+'/ham2d').mkdir(exist_ok=True)

    for i,af in enumerate(af_files):
        af_name = af.split('/')[-1]
        af_shape = np.loadtxt(af)
        pathlib.Path(dir_name+'/ham2d/{}'.format(af_name)).mkdir(exist_ok=True)
        for c_re in re:
            re_dir = dir_name+'/ham2d/{}/re_{:08d}'.format(af_name,int(c_re))
            pathlib.Path(re_dir).mkdir(exist_ok=True)
            pathlib.Path(re_dir+'/mesh/').mkdir(exist_ok=True)
            write_ham2d_mesh_input(af_shape[:,0],af_shape[:,1],re_dir+'/mesh',af_name, c_re)
            pathlib.Path(re_dir+'/mesh/meshgen_test/autorun/QuadData').mkdir(parents=True,exist_ok=True)
            for alpha in aoa:
                if (alpha < 0):
                    alpha_dir = re_dir+'/aoa_m{:02d}'.format(int(-alpha))
                else:
                    alpha_dir = re_dir+'/aoa_{:02d}'.format(int(alpha))
                pathlib.Path(alpha_dir).mkdir(exist_ok=True)
                pathlib.Path(alpha_dir+'/output').mkdir(exist_ok=True)
                write_ham2d_solver_input(alpha_dir,alpha,c_re)
                try:
                    pathlib.Path(alpha_dir+'/QuadData').unlink()
                except:
                    pass
                os.symlink('../mesh/meshgen_test/autorun/QuadData', alpha_dir+'/QuadData')

if __name__=="__main__":
    create_ham2d_input_files('iea15mw',glob.glob('coordinates/*'))
