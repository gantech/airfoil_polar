from subprocess import Popen, PIPE
import glob, pprint, pathlib, os
import numpy as np
import pandas as pd

def submit_ham2d_jobs(dir_name, af_names, account, re=[3e6,6e6,9e6,12e6], aoa=np.linspace(-4,20,25), n_cases_per_job=36):

  #Submit mesh job first
  mesh_job_id = submit_mesh_job(dir_name, af_names, account, re, n_cases_per_job)
  if (mesh_job_id < 1):
    print("Mesh job submission didn't work. Please check")
    return -1

  #Now CFD jobs
  caseList = []
  for af_name in af_names:
    for c_re in re:
      re_dir = "../{}/re_{:08d}".format(af_name,int(c_re))
      for alpha in aoa:
        if (alpha < 0):
          alpha_dir = re_dir+'/aoa_m{:02d}'.format(int(-alpha))
        else:
          alpha_dir = re_dir+'/aoa_{:02d}'.format(int(alpha))
        caseList.append(alpha_dir)

  pathlib.Path(dir_name+"/ham2d/job_list").mkdir(exist_ok=True)
  n_jobs = int(len(caseList)/n_cases_per_job)
  for i in range(0, len(caseList), n_cases_per_job):
    with open(dir_name+"/ham2d/job_list/listOfCases_{:04d}".format(int(i/n_cases_per_job)),'w') as f:
       clist = caseList[i: i+n_cases_per_job]
       for c in clist:
          f.write(c+'\n')

  with open(dir_name+"/ham2d/job_list/polar_cases.slurm",'w') as f:
    f.write("#!/bin/bash"+"\n")
    f.write("#SBATCH --nodes=1"+"\n")
    f.write("#SBATCH --time=4:00:00"+"\n")
    f.write("#SBATCH --account={}".format(account)+"\n")
    f.write("#SBATCH --array=0-{}".format(n_jobs)+"\n")
    f.write("#SBATCH --job-name={}".format(dir_name)+"\n")
    f.write("#SBATCH --output=out.%x_%j"+"\n")
    f.write(""+"\n")
    f.write("source /projects/integrate/integrate_cfd/integrate_env.sh"+"\n")
    f.write(""+"\n")
    f.write("ranks_per_node=36"+"\n")
    f.write("mpi_ranks=$(expr $SLURM_JOB_NUM_NODES \* $ranks_per_node)"+"\n")
    f.write("export OMP_NUM_THREADS=1  # Max hardware threads = 4"+"\n")
    f.write("export OMP_PLACES=threads"+"\n")
    f.write("export OMP_PROC_BIND=spread"+"\n")
    f.write(""+"\n")
    f.write('echo "Job name       = $SLURM_JOB_NAME"'+"\n")
    f.write('echo "Num. nodes     = $SLURM_JOB_NUM_NODES"'+"\n")
    f.write('echo "Num. MPI Ranks = $mpi_ranks"'+"\n")
    f.write('echo "Num. threads   = $OMP_NUM_THREADS"'+"\n")
    f.write('echo "Working dir    = $PWD"'+"\n")
    f.write(""+"\n")
    f.write('caselist=$(printf "listOfCases_%04d" ${SLURM_ARRAY_TASK_ID}) \n')
    f.write(""+"\n")
    f.write("for i in `cat ${caselist}`"+"\n")
    f.write("do"+"\n")
    f.write("    cd $i"+"\n")
    f.write("    srun -n 1 -c 1 ${INTEGRATE_DIR}/install/integrate-cfd/bin/ham2d &> log &"+"\n")
    f.write("    cd -"+"\n")
    f.write("done"+"\n")
    f.write(""+"\n")
    f.write("wait"+"\n")
    f.write(""+"\n")

  os.chdir(dir_name+'/ham2d/job_list/')
  p = Popen(['sbatch', '-d', 'afterok:{}'.format(mesh_job_id), 'polar_cases.slurm'], stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True)
  output, err = p.communicate()
  print(output, err)

def submit_mesh_job(dir_name, af_names, account, re=[3e6,6e6,9e6,12e6], n_cases_per_job=36):
  caseList = []
  for af_name in af_names:
    for c_re in re:
      mesh_dir = "../{}/re_{:08d}/mesh".format(af_name,int(c_re))
      caseList.append(mesh_dir)

  pathlib.Path(dir_name+"/ham2d/job_list").mkdir(exist_ok=True)
  with open(dir_name+"/ham2d/job_list/meshCases",'w') as f:
    for c in caseList:
      f.write(c+'\n')

  with open(dir_name+"/ham2d/job_list/run_mesh.sh",'w') as f:
    f.write("cd $1 \n")
    f.write("srun -n 1 python ${INTEGRATE_DIR}/install/integrate-cfd/bin/automesh_run.py &> log.mesh \n")
    f.write("cd - \n")

  with open(dir_name+"/ham2d/job_list/mesh_cases.slurm",'w') as f:
    f.write("#!/bin/bash"+"\n")
    f.write("#SBATCH --nodes=1"+"\n")
    f.write("#SBATCH --time=4:00:00"+"\n")
    f.write("#SBATCH --account={}".format(account)+"\n")
    f.write("#SBATCH --job-name={}_mesh".format(dir_name)+"\n")
    f.write("#SBATCH --output=out.%x_%j"+"\n")
    f.write(""+"\n")
    f.write("source /projects/integrate/integrate_cfd/integrate_env.sh"+"\n")
    f.write(""+"\n")
    f.write("ranks_per_node=36"+"\n")
    f.write("mpi_ranks=$(expr $SLURM_JOB_NUM_NODES \* $ranks_per_node)"+"\n")
    f.write("export OMP_NUM_THREADS=1  # Max hardware threads = 4"+"\n")
    f.write("export OMP_PLACES=threads"+"\n")
    f.write("export OMP_PROC_BIND=spread"+"\n")
    f.write(""+"\n")
    f.write('echo "Job name       = $SLURM_JOB_NAME"'+"\n")
    f.write('echo "Num. nodes     = $SLURM_JOB_NUM_NODES"'+"\n")
    f.write('echo "Num. MPI Ranks = $mpi_ranks"'+"\n")
    f.write('echo "Num. threads   = $OMP_NUM_THREADS"'+"\n")
    f.write('echo "Working dir    = $PWD"'+"\n")
    f.write(""+"\n")
    f.write(""+"\n")
    f.write("cat meshCases | xargs -n 1 -P {} bash run_mesh.sh".format(n_cases_per_job)+"\n")
    f.write(""+"\n")

  os.chdir(dir_name+"/ham2d/job_list/")
  p = Popen(['sbatch', 'mesh_cases.slurm'], stdin=PIPE, stdout=PIPE, stderr=PIPE, text=True)
  output, err = p.communicate()
  os.chdir('../../../')
  if (p.returncode == 0):
    return int(output.split(' ')[-1])
  else:
    return -1

if __name__=="__main__":
  afs = [i.split('/')[-1] for i in glob.glob('coordinates/*') ]
  submit_ham2d_jobs('iea15mw', afs, 'integrate')
