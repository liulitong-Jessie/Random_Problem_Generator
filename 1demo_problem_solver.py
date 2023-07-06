"""
This script is intended to help with debugging problems and solvers.
It create a problem-solver pairing (using the directory) and runs multiple
macroreplications of the solver on the problem.
"""

import sys
import os.path as o
import os
sys.path.append(o.abspath(o.join(o.dirname(sys.modules[__name__].__file__), "..")))

# Import the ProblemSolver class and other useful functions
from simopt.experiment_base import ProblemSolver, read_experiment_results, post_normalize, plot_progress_curves, plot_solvability_cdfs
from rng.mrg32k3a import MRG32k3a

# !! When testing a new solver/problem, first go to directory.py.
# See directory.py for more details.
# Specify the names of the solver and problem to test.

# -----------------------------------------------
solver_name = "RNDSRCH"  # Random search solver
problem_name = "SMF-1"   #"SAN-1"
# -----------------------------------------------

from simopt.models.san_2 import SANLongestPath
from simopt.models.smf import SMF_Max

def rebase(random_rng, n):
    new_rngs = []
    for rng in random_rng:
        stream_index = rng.s_ss_sss_index[0]
        substream_index = rng.s_ss_sss_index[1]
        subsubstream_index = rng.s_ss_sss_index[2]
        new_rngs.append(MRG32k3a(s_ss_sss_index=[stream_index, substream_index, subsubstream_index + n]))
    random_rng = new_rngs
    return random_rng

# n_inst = 5

n_inst = int(input('Please enter the number of instance you want to generate: '))
rand = bool(input('Please decide whether you want to generate random instances or determinent instances (True/False): '))

myproblem = SANLongestPath(random=True)
# myproblem = SMF_Max(random=True)

random_rng = [MRG32k3a(s_ss_sss_index=[2, ss + 4, 0]) for ss in range(myproblem.model.n_random, myproblem.model.n_random + myproblem.n_rngs)]
rng_list = [MRG32k3a(s_ss_sss_index=[0, ss, 0]) for ss in range(myproblem.model.n_rngs)]
rng_list2 = [MRG32k3a(s_ss_sss_index=[2, 4 + ss, 0]) for ss in range(myproblem.model.n_random)]
# rng_list = [* rng_list, * rng_list2]


# Generate 5 random problem instances
for i in range(n_inst):
    random_rng = rebase(random_rng, i)
    rng_list2 = rebase(rng_list2, i)
    # myproblem = SMF_Max(random=rand, random_rng=rng_list2)
    myproblem = SANLongestPath(random=rand, random_rng=rng_list2)
    myproblem.attach_rngs(random_rng)
    problem_name = 'SAN_' + str(i)
    print('-------------------------------------------------------')

    print(f"Testing solver {solver_name} on problem {problem_name}.")
    
    print("The arcs of the graph: ", myproblem.model.factors["arcs"])
    print('  ')

    # Specify file path name for storing experiment outputs in .pickle file.
    file_name_path = "experiments/outputs/" + solver_name + "_on_" + problem_name + ".pickle"
    print(f"Results will be stored as {file_name_path}.")

    # Initialize an instance of the experiment class.
    myexperiment = ProblemSolver(solver_name=solver_name, problem=myproblem)

    # Run a fixed number of macroreplications of the solver on the problem.
    myexperiment.run(n_macroreps=1) #20, 5

    # If the solver runs have already been performed, uncomment the
    # following pair of lines (and uncommmen the myexperiment.run(...)
    # line above) to read in results from a .pickle file.
    # myexperiment = read_experiment_results(file_name_path)

    print("Post-processing results.")
    # Run a fixed number of postreplications at all recommended solutions.
    myexperiment.post_replicate(n_postreps=5) #200, 10
    # Find an optimal solution x* for normalization.
    post_normalize([myexperiment], n_postreps_init_opt=1) #200, 5

    # Log results.
    myexperiment.log_experiment_results()

    #####
    # for itm in myexperiment.all_recommended_xs:
    #     res = itm.

    print("Optimal solution: ",myexperiment.xstar)
        

    print("Plotting results.")
    # Produce basic plots of the solver on the problem.
    plot_progress_curves(experiments=[myexperiment], plot_type="all", normalize=False)
    plot_progress_curves(experiments=[myexperiment], plot_type="mean", normalize=False)
    plot_progress_curves(experiments=[myexperiment], plot_type="quantile", beta=0.90, normalize=False)
    plot_solvability_cdfs(experiments=[myexperiment], solve_tol=0.1)

    # Plots will be saved in the folder experiments/plots.
    print("Finished. Plots can be found in experiments/plots folder.")