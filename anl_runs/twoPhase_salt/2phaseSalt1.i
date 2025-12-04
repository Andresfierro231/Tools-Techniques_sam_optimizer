!include twosalt3.i

## 20 Oct 25: I am not sure I am using this... I think the real scripts are twosalt*.i

# # Quadrature Settings
# p_order_quadPnts :=   1     #  2      #
# quad_type :=          TRAP  #  GAUSS  #
# quad_order :=         FIRST #  SECOND #
# scheme :=  implicit-euler # BDF2 #    # # crank-nicolson #

### Settings if doing Restart

# [Problem] # Problem restart
#   restart_file_base = 2phaseSalt1_SteadyState/LATEST
# []


[GlobalParams]

  [PBModelParams]
    gas_scaling_factor := '1e6' # '1e2' # Scales residual
    gas_model := true
    gas_slip_model := 'drift_flux'
    Courant_control := true
  []
[]



[MaterialProperties]

  [Argon_fluid_props] # Available here for your convenience; to change parameters around
    type := IdealGasFluidProperties
    gamma := 1.667 # Noble gas # fixed in theory
    molar_mass := 39.948E-3 # Kg / mol
    mu := 3.28E-5 # Viscosity Pa-s at 200*C # #
    k  := 0.0172 # W/m*K
  []

[]

[Functions]
    [injection_loc] # Spatial domains of bubble injection
        type = PiecewiseConstant
        x = '0.0  0.1   0.8    0.81'
        y =  '0.25  0     0.0       0' # '0.0 gas_injection_rate 0.0   gas_remove_rate 0' #
        direction = left_inclusive
        axis = x
    []
    [time_dependance] # Where are there bubbles
      type = PiecewiseLinear # PiecewiseConstant # Zero bubbles from -5000 to -2000 s; at -2000 sec, tries to slowly fill area with bubbles.
      x = '-5000 -2000 0'
      y = '0      0    1'
    []
    [scaling_density]
      type = ConstantFunction
      value = ${fparse 1.5e-7 * 1.29 / (pi* (0.87*0.0254)^2 / 4 * 0.1)} #0.00504 #504# 5.04
        # 1.5e-5 gas injected  # rho ~= 1.29 kg/m3 (ideal gas) # h = 0.01 m # A =  0.0003835 # m^2# ${fparse pi* (0.87^2 / 4 * 0.0254}
        #  1.5e-5 * 1.29/(.01* 0.0003835) =  5.045632333767927
        #  1.5e-5 * 1.29/(.1* 0.0003835) =   0.5045632333767927
    []
    [injection]
      type = CompositeFunction
      functions = 'injection_loc time_dependance scaling_density'
    []
  [time_stepper] # Determines max timestep in domain, bc timestepper uses min timestep available
    type = PiecewiseConstant
    x = '-5000  -2010 -2000   -1990'
    y = ' 200    0.1   0.1   3600'
    direction = left_inclusive
  []
[]

[Components]
  [up1]
    gas_source :=   'injection' # 3.0 # 0#
  []
[]



### =======================================================================================================
### ==================================     Bubbles Below    ===============================================
### =======================================================================================================


[Executioner] # Creating timestepper
  # type :=  Transient #  SAMSegregatedTransient #
  # solve_type = 'PJFNK'  # PJFNK JFNK NEWTON FD LINEAR # no n
  start_time = -5000
  end_time :=  1e6 # used by Travis


  dtmin := 1e-7 # after this point starts diverging
  automatic_scaling := false

  scheme := implicit-euler

  # dt = ${const_TS}

  # dtmax := 15 # ${dt_max}
  [TimeSteppers]
    [IterationAdaptiveDT]
      type := IterationAdaptiveDT
      growth_factor := 1.1
      optimal_iterations := 8
      linear_iteration_ratio := 150
      dt := 0.01
      cutback_factor := 0.8
      cutback_factor_at_failure := 0.5
    []
    [FunctionDT]
      type = FunctionDT
      function = time_stepper
      min_dt = 1e-6
    []

  []

  nl_rel_tol := 1e-7 # -6
  nl_abs_tol := 1e-6 # -7 # e-6 could be too high, want abs to be couple order magn below rel, charlie suggests e-8
  nl_max_its := 12 # Consider increasing to 20
  l_tol      := 1e-5
  l_max_its  := 100
[]


### =======================================================================================================
# ### ==============================   Get to Steady State    ===============================================
# ### =======================================================================================================

# [Executioner] # Creating timestepper
#   # type :=  Transient #  SAMSegregatedTransient #
#   # solve_type = 'PJFNK'  # PJFNK JFNK NEWTON FD LINEAR # no n
#   start_time = -5e4
#   end_time := 0 # 1e3 used by Travis


#   dtmin := 1e-7 # after this point starts diverging
#   automatic_scaling := false

#   scheme := implicit-euler

#   # dt = ${const_TS}

#   [TimeStepper]
#     type := IterationAdaptiveDT
#     optimal_iterations := 10
#     iteration_window := 4
#     dt := 0.01 # 100
#     growth_factor := 1.15     # Step size multiplier if solve is good
#     cutback_factor := 0.8     # Step size divisor if solve is poor

#   []
# []
