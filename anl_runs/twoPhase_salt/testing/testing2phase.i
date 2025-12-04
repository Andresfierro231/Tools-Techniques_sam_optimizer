### TEST INFORMATION ####
#### Category:

# Gas Transport Model

#### Requirement:

# SAM shall support modeling of a gas source term in the model using a spatially dependent function when
# the gas is transported by the drift velocity

#### Acceptance Criteria:

# The gas mass flow rate is checked at the inlet and outlet and ensured to be zero. It is checked at three
# points between the injection/removal points and ensured to be equal to the expected mass flow rate. The
# expected mass flow rate is calculated as S*L*A, where S is the volumetric mass source rate (or removal),
# A is the flow area, and L is the length over which it is injected (0.1 m).

#### Summary Description:

# This is a vertical pipe with a salt flowing upwards
# Gas is injected as a point source term in the bottom of the pipe and is removed at the top via
# a negative volumetric source term.
# The drift flux model is enabled.

#### END TEST INFORMATION ####


[GlobalParams]
global_init_P = 1.1e5 # Global initial fluid pressure
global_init_V = 0.2 # Global initial temperature for fluid and solid
global_init_T = 628.15 # Global initial fluid velocity
scaling_factor_var = '1e3 1e-2 1e-6' # Scaling factors for fluid variables (p, v, T)

[PBModelParams]
gas_scaling_factor = '1e4'
gas_model = true
gas_slip_model = 'drift_flux'
Courant_control = true
[]
[]

[EOS]
[eos] # EOS name
type = PTConstantEOS
T_0 = 628.15
p_0 = 1.1e5
cp = 1000.0
h_0 = 8e5
k = 72
rho_0 = 1000.0
mu = 1e-5
sigma = 0.26
[]
[eos_gas]
type = HeEquationOfState
#type = PTConstantEOS
#T_0 = 628.15
#p_0 = 1.1e5
#cp = 1000.0
#h_0 = 8e5
#k = 72
#rho_0 = 0.1
#mu = 1e-5
[]
[]

[Functions]
[injection]
type = PiecewiseConstant
x = '0.0 0.1 0.2 0.8 0.9 1.0'
y = '0.0 1e-3 0.0 -1e-3 0.0 0.0'
direction = left_inclusive
axis = x
[]
[]

[Components]
[pipe1]
type = PBOneDFluidComponent
eos = eos # The equation-of-state name
eos_gas = eos_gas
position = '0 0 0' # The origin position of this component
orientation = '0 0 1' # The orientation of the component
Dh = 2.972e-3 # Equivalent hydraulic diameter
length = 1.0 # Length of the component
n_elems = 100 # Number of elements used in discretization
A = 2.972e-3 # Area set to that of MSRE flow channel
gas_source = 'injection'
f=0.001
[]
[inlet]
type = PBTDJ
input = 'pipe1(in)' # Name of the connected components and the end type
eos = eos # The equation-of-state
eos_gas = eos_gas
v_bc = 0.2 # Velocity boundary condition
T_bc = 628.15 # Global initial fluid velocity
alphag_bc = '0.0'
[]

[outlet]
type = PBTDV
input = 'pipe1(out) ' # Name of the connected components and the end type
eos = eos # The equation-of-state
eos_gas = eos_gas
p_bc= 1.1e5 # Global initial fluid pressure
T_bc = 628.15 # Temperature boundary condition
[]
[]

[Postprocessors]
[gas_mdot_000]
type = ComponentNodalGasMassFlowRate
input = pipe1(0)
[]
[gas_mdot_010]
type = ComponentNodalGasMassFlowRate
input = pipe1(10)
[]
[gas_mdot_020]
type = ComponentNodalGasMassFlowRate
input = pipe1(20)
[]
[gas_mdot_030]
type = ComponentNodalGasMassFlowRate
input = pipe1(30)
[]
[gas_mdot_040]
type = ComponentNodalGasMassFlowRate
input = pipe1(40)
[]
[gas_mdot_050]
type = ComponentNodalGasMassFlowRate
input = pipe1(50)
[]
[gas_mdot_060]
type = ComponentNodalGasMassFlowRate
input = pipe1(60)
[]
[gas_mdot_070]
type = ComponentNodalGasMassFlowRate
input = pipe1(70)
[]
[gas_mdot_080]
type = ComponentNodalGasMassFlowRate
input = pipe1(80)
[]
[gas_mdot_090]
type = ComponentNodalGasMassFlowRate
input = pipe1(90)
[]
[gas_mdot_100]
type = ComponentNodalGasMassFlowRate
input = pipe1(100)
[]


###########################################################################
# Acceptance Test 1: Ensure gas mass flow rate axial profile is correct considering source term
###########################################################################
[check_mdot_000]
type = PostprocessorComparison
comparison_type = equals
value_a = 'gas_mdot_000'
value_b = 0.0
[]
[check_mdot_020]
type = PostprocessorComparison
comparison_type = equals
value_a = 'gas_mdot_020'
# Injection occurs at a rate of 1e-3 over 0.1 m, so total mass flux will be that times flow area
value_b = ${fparse 1e-3*0.1*2.972e-3}
[]
[check_mdot_050]
type = PostprocessorComparison
comparison_type = equals
value_a = 'gas_mdot_050'
value_b = ${fparse 1e-3*0.1*2.972e-3}
[]
[check_mdot_070]
type = PostprocessorComparison
comparison_type = equals
value_a = 'gas_mdot_070'
value_b = ${fparse 1e-3*0.1*2.972e-3}
[]
[check_mdot_100]
type = PostprocessorComparison
comparison_type = equals
value_a = 'gas_mdot_100'
value_b = 0.0
# Match to 6 digits
absolute_tolerance = 1e-6
[]
[]

[Preconditioning]
[SMP_PJFNK]
type = SMP # Single-Matrix Preconditioner
full = true # Using the full set of couplings among all variables
solve_type = 'PJFNK' # Using Preconditioned JFNK solution method
#petsc_options_iname = '-pc_type' # PETSc option, using preconditiong
#petsc_options_value = 'lu' # PETSc option, using ‘LU’ precondition type in Krylov solve
#petsc_options_iname = '-pc_type -ksp_gmres_restart'
#petsc_options_value = 'lu 101'
#petsc_options_iname = '-pc_type -pc_svd_monitor'
#petsc_options_value = 'svd true'
[]
[] # End preconditioning block

[Executioner]
type = Steady # This is a Steady simulation

petsc_options_iname = '-ksp_gmres_restart' # Additional PETSc settings, name list
petsc_options_value = '100' # Additional PETSc settings, value list

nl_rel_tol = 1e-8 # Relative nonlinear tolerance for each Newton solve
nl_abs_tol = 1e-8 # Relative nonlinear tolerance for each Newton solve
nl_max_its = 100 # Number of nonlinear iterations for each Newton solve

l_tol = 1e-8 # Relative linear tolerance for each Krylov solve
l_max_its = 100 # Number of linear iterations for each Krylov solve

[Quadrature]
type = TRAP # Using trapezoid integration rule
order = FIRST # Order of the quadrature
[]
[] # End Executioner block

[Outputs]
perf_graph = true
print_linear_residuals = false # Disable linear residual outputs
[console]
type = Console # Screen output
[]
[out_displace]
type = Exodus
use_displaced = true
[]
[csv]
type = CSV
[]
[]
