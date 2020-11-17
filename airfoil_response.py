import yaml, pathlib
import pandas as pd
import numpy as np
import glob

def process_ham2d_results(dir_name, af_names, re=[3e6,6e6,9e6,12e6], aoa=np.linspace(-4,20,25)):
    for rey in re:
        create_ham2d_polar(dir_name, af_names, rey, aoa)

def create_ham2d_polar(dir_name, af_names, reynolds, aoa=np.linspace(-4,20,25)):
    af_polar_db = {}
    for af in af_names:
      re_dir = dir_name+'/ham2d/{}/re_{:08d}'.format(af, int(reynolds))
      case_polar = pd.DataFrame(columns=['aoa','cl','cd','cm'])
      for alpha in aoa:
        if (alpha < 0):
            alpha_dir = re_dir+'/aoa_m{:02d}'.format(int(-alpha))
        else:
            alpha_dir = re_dir+'/aoa_{:02d}'.format(int(alpha))
        try:
            tmp = pd.read_csv(pathlib.Path(alpha_dir+'/output/alpha_clcd.dat'),sep='\s+',header=None,names=['aoa','cl','cd','cm'],usecols=[0,2,3,4])
            case_polar = case_polar.append(tmp.iloc[-1])
        except:
            print("Can't read file " + alpha_dir+'/output/alpha_clcd.dat')

      af_polar_db[af] = {
          'aoa': case_polar['aoa'].to_list(),
          'cl': case_polar['cl'].to_list(),
          'cd': case_polar['cd'].to_list(),
          'cm': case_polar['cm'].to_list()
      }

    yaml.dump(af_polar_db, open(dir_name+'/ham2d/re{:08d}.yaml'.format(int(reynolds)) ,'w'), default_flow_style=False)

if __name__=="__main__":
    afs = [i.split('/')[-1] for i in glob.glob('coordinates/*') ]
    process_ham2d_results('iea15mw', afs)
