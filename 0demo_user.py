"""
This script is intended to help with debugging problems and solvers.
It create problem-solver groups (using the directory) and runs multiple
macroreplications of each problem-solver pair.
"""

import sys
import os.path as o
import os
sys.path.append(o.abspath(o.join(o.dirname(sys.modules[__name__].__file__), "..")))

# Import the ProblemsSolvers class and other useful functions
from simopt.experiment_base import ProblemsSolvers, plot_solvability_profiles
from simopt.models.san_2 import SANLongestPath
from simopt.models.smf import SMF_Max
from simopt.models.rmitd import RMITDMaxRevenue
from simopt.models.openjackson import OpenJacksonMinQueue
from simopt.models.mm1queue import MM1MinMeanSojournTime
from rng.mrg32k3a import MRG32k3a
from simopt.solvers import randomsearch, astrodf, neldmd
from simopt.base import Solution


# !! When testing a new solver/problem, first go to directory.py.
# There you should add the import statement and an entry in the respective
# dictionary (or dictionaries).
# See directory.py for more details.

# Specify the names of the solver and problem to test.
# These names are strings and should match those input to directory.py.
# Ex:
solver_names = ["RNDSRCH", "ASTRODF", "NELDMD"]
solvers = [randomsearch, astrodf, neldmd]

# solver_names = ["RNDSRCH"]
problem_set = [SANLongestPath, SMF_Max, RMITDMaxRevenue, OpenJacksonMinQueue, MM1MinMeanSojournTime]
rands = [True for i in range(len(problem_set))]

solver_names = [i.upper() for i in input('Please enter the names of solvers you want to use and separate by white space: ').split()]

problem_index = [int(i) for i in input('Please enter the indices of problems you want to generate and separate by white space (start from 0): ').split()]
L_num = [int(i) for i in input("Please enter the number of random instances for each problem you want to generate (enter 0 for deterministic case): ").split()]

while len(L_num) != len(problem_index):
    print('Invalid input. The input number of random instances does not match with the number of problems you want.')
    print('Please re-input the number of instance you want for the ', len(problem_index), ' problems.')
    L_num = [int(i) for i in input("Please enter the number of random instances for each problem you want to generate (enter 0 for deterministic case): ").split()]

def rebase(random_rng, n):
    new_rngs = []
    for rng in random_rng:
        stream_index = rng.s_ss_sss_index[0]
        substream_index = rng.s_ss_sss_index[1]
        subsubstream_index = rng.s_ss_sss_index[2]
        new_rngs.append(MRG32k3a(s_ss_sss_index=[stream_index, substream_index + n, subsubstream_index]))
    random_rng = new_rngs
    return random_rng

myproblems = [problem_set[i] for i in problem_index]

for i in range(len(problem_index)):
    if L_num[i] == 0:
        L_num[i] = 1
        rands[i] = False
    else:
        rands[i] = True

problems = []
problem_names = []
        
def generate_problem(i, myproblems, rands, problems, L_num):    
    print('For problem ', myproblems[i]().model.name, ':')  
    model_fixed_factors = eval(input("Please enter the parameters you want to override in terms of dictionary, otherwise please input a null dictionary: "))
    
    name = myproblems[i]
    myproblem = name(model_fixed_factors=model_fixed_factors, random=rands[i])
    # random_rng = [MRG32k3a(s_ss_sss_index=[2, 4 , ss]) for ss in range(myproblem.model.n_random, myproblem.model.n_random + myproblem.n_rngs)]
    random_rng = [MRG32k3a(s_ss_sss_index=[2, 4 + L_num[i], ss]) for ss in range(myproblem.n_rngs)]
    rng_list2 = [MRG32k3a(s_ss_sss_index=[2, 4, ss]) for ss in range(myproblem.model.n_random)]
    
    if rands[i] == False:
        problems.append(myproblem)
        myproblem.name = str(myproblem.model.name) + str(0)
        problem_names.append(myproblem.name)
    
    else:
        for j in range(L_num[i]):
            random_rng = rebase(random_rng, j)
            rng_list2 = rebase(rng_list2, j)
            name = myproblems[i]
            myproblem = name(model_fixed_factors=model_fixed_factors, random=rands[i], random_rng=rng_list2)
            myproblem.attach_rngs(random_rng)
            myproblem.name = str(myproblem.model.name) + str(j)
            print('budget: ', myproblem.factors["budget"])
            problems.append(myproblem)
            problem_names.append(myproblem.name)
    
    return problems, problem_names
        
for i in range(len(L_num)):
        problems, problem_names = generate_problem(i, myproblems, rands, problems, L_num)


# Initialize an instance of the experiment class.
mymetaexperiment = ProblemsSolvers(solver_names=solver_names, problems = problems)
# mymetaexperiment = ProblemsSolvers(solver_names=solver_names, problem_names = problem_names)


# Run a fixed number of macroreplications of each solver on each problem.
mymetaexperiment.run(n_macroreps=20)


print("Post-processing results.")
# Run a fixed number of postreplications at all recommended solutions.
mymetaexperiment.post_replicate(n_postreps=20)
# Find an optimal solution x* for normalization.
mymetaexperiment.post_normalize(n_postreps_init_opt=20)

print("Plotting results.")
# print("Optimal solution: ",mymetaexperiment.xstar)
# Produce basic plots of the solvers on the problems.
plot_solvability_profiles(experiments=mymetaexperiment.experiments, plot_type="cdf_solvability")

# Plots will be saved in the folder experiments/plots.
print("Finished. Plots can be found in experiments/plots folder.")




# print('initial: ', initials)
# for i in range(len(problems)):
#     mysolution = Solution(initials[i], problems[i])
#     mysolution.attach_rngs(rng_lists[i], copy=False)
#     n_reps = 1
#     problems[i].simulate(mysolution, m=n_reps)
    
#     # print('arcs: ', problems[i].model.factors["arcs"])
#     print(mysolution.objectives_mean[0])
#     print(type(mysolution))

#     # print("Objective coefficients: ", myproblem.factors["c"])  # For SAN

#     print(f"Ran {n_reps} replications of the {problems[i].name} problem at solution x = {x}.\n")
        
#     print("The individual observations of the objective were:")
#     for idx in range(n_reps):
#         print(f"\t {round(mysolution.objectives[idx][0], 4)}")
#     if problems[i].gradient_available:
#         print("\nThe individual observations of the gradients of the objective were:")
#         for idx in range(n_reps):
#             print(f"\t {[round(g, 4) for g in mysolution.objectives_gradients[idx][0]]}")
#     else:
#         print("\nThis problem has no known gradients.")
#     if problems[i].n_stochastic_constraints > 0:
#         print(f"\nThis problem has {problems[i].n_stochastic_constraints} stochastic constraints of the form E[LHS] <= 0.")
#         for stc_idx in range(problems[i].n_stochastic_constraints):
#             print(f"\tFor stochastic constraint #{stc_idx + 1}, the mean of the LHS was {round(mysolution.stoch_constraints_mean[stc_idx], 4)} with standard error {round(mysolution.stoch_constraints_stderr[stc_idx], 4)}.")
#             print("\tThe observations of the LHSs were:")
#             for idx in range(n_reps):
#                 print(f"\t\t {round(mysolution.stoch_constraints[idx][stc_idx], 4)}")
#     else:
#         print("\nThis problem has no stochastic constraints.")

