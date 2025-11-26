################## MSFL Draft Script
### First Created: 30 Jul 25
# ⭐⭐ Today editing: 01 Aug 25
#
#
#                             Water Run Validation

# Continuing validation work from Salts, very similar to jsalt_base_case.i   
# 
## Overview questions
#
#
####
# Jadyn's Paper https://docs.google.com/document/d/1_5Ws5vh5xfU7X6hZ7Zhk28DTL38MUvc8Ca32jG6ZShs/edit?usp=sharing
#############################  Experimental Prameters  ######################################################
#


#### Control Panel ####
# Don't forget to change EOS for fluid type

## Commenting out unused in debugging
# airTempIn = 300 # Kelvin
# avg_air_vel_in = 0.4057 # 2.0612 # # m/s # Not used for now


fric_factor = 0.612
T_c = 441.37 # Pin the temperature you want the cooler to cool fluid to #${fparse 168.22 + 273.15} # Use measured temp at TP1  # 168.22 + 273.15 = 441.37
q_net = 189.26 # W # Note, I don't think she is using Q_heater


T_h = 445.7  # Turns out simulation stability is incredibly sensitive to value chosen here, but not numerical result for some strange reason # Maybe not highest temp, but avg temp of loop?
p_0 = 1.1e5 # 1.01e5 # try change to 1.5 or 2 # Initial pressure, and ambient
T_0 = 444 # T_0 = T_c # 441.37 # 430 # Kelvin # Initial System, start a bit warmer than T_c


v_0 = 0.02 # 0.0185
h_amb = 1e5  # Arbitrarily large, as specified in paper
p_out = 1.1e5

We_exp = 3.96
injection_vol_rate = 1.5e-7
ar_density = ${fparse 1.2e5 * 39.948e-3 / (8.3144598*319.6) } # Pressure at TS: 1.1973e5 Pa # P / (R * T) = M / V = 1.01e5 / (8.314/ 39.948e-3  * 319.6) = 1.518 

target_Pr = 47.50
target_vel = 0.028
target_deltaT = 11.94

target_bubble_d_eq = 1
target_gas_vel = 1
target_void_frac = 1



# TS Const
const_TS = 10 # s
node_multiplier = 4

# Quadrature Settings
p_order_quadPnts =  1 #2       # 1
quad_type  =  TRAP #      GAUSS   # TRAP
quad_order =  FIRST #     SECOND  # FIRST
scheme =  implicit-euler # BDF2 #    # # crank-nicolson #

nodes =          ${fparse 6 * node_multiplier} # 30 #
nodes_melter =   ${fparse 2 * node_multiplier} # 10 #
midnode =        ${fparse 3 * node_multiplier} # 15 # 

###### Under the hood -- Making usable ########
heater_power = ${fparse ${q_net} / (0.0003835 * 36 * 0.0254)} # # Volumetric # Watts / m^3 # m^3 = area * length_inches * conversion # SI units # Can use ipython as calc

##############################################################################################################

# Geometry  and Positions
end_pipe_up =        '0  0      ${fparse (36) * 0.0254}'
end_cooling_jacket = '0  ${fparse (36* cos(0.349)) * 0.0254}      ${fparse (36 - 36 * sin(0.349)) * 0.0254}'
ht_entry_loc =       '0  ${fparse (36* cos(0.349)) * 0.0254}      ${fparse ( - 36 * sin(0.349)) * 0.0254}'

# How do I add temperature probes at these locations??
# ts_in_loc =          '0  0      ${fparse 14.34 * 0.0254}'
# ts_out_loc =         '0  0      ${fparse (14.34 + 7.32) * 0.0254}' # Will keep ts locations for postprocessors

[GlobalParams]
  global_init_P = ${p_0}                      # I think this is ambient pressure # Global initial fluid pressure # --> Depends on problem, IC to make problem converge, changing IC and scaling factor to make converge
  global_init_V = ${v_0} # Probably shouldn't start with zero velocity, and in loop they defined 1.5 originally             # Global initial fluid velocity
  global_init_T = ${T_0} # Kelvin # Starting water luke-warm           # I am pretty sure SAM uses Kelvin          # Global initial temperature for fluid and solid

  p_order = ${p_order_quadPnts} # 1 # Specifies the order of mesh... How many quadrature points in FE sol # P order 1 runs faster but not as accurate
  gravity = '0 0 -9.8' # switched sign gravity

  f = ${fric_factor} #6.5 # Use global friction factor
  eos = water

  # 2 Phase input values
  Weber = ${We_exp} # Placeholder value, should be substituted for runs
  eos_gas = Ar_eos

  [PBModelParams]
    gas_scaling_factor = '1e6' # '1e4'
    gas_model = true
    gas_slip_model = 'drift_flux'
    Courant_control = true
  []
[]

[EOS]
  [air_eos]
    type = AirEquationOfState # HeEquationOfState # # N, He, Na
  []
  [Ar_eos]
    type = PTFluidPropertiesEOS
    fp = Argon_fluid_props
  []
    [fp_water] # Water from single phase validation, for reference
    type = PTFluidPropertiesEOS
    fp = water_fp
    p_0 =  ${p_0}
  []
  [water]
    type = PTFunctionsEOS
    rho = water-rho
    k = water-k
    cp = water-cp
    mu = water-mu
    T_min = 273.15
    T_max = 373.15
    sigma = 0.0678  # ${fparse 0.2358 * pow(1 - T_h/647.096, 1.256) * (1 - 0.625*(1 - T_h/647.096))} #0.06 # water-sigma #
  []
[]




[MaterialProperties]
  [ss-mat] # my HX is SS 315, manual says ss HT9 and D9 are implemented, but I don't see an example on how to use D9... D9 looks like closest to SS-316... constant is probably faster though
    type = SolidMaterialProps
    k = 15 # K ranges from (13 - 17) https://www.azom.com/properties.aspx?ArticleID=863
    Cp = 500 #638 # Ranges from 490 - 530
    rho = 7.7e3 # Density is reported to range from 7.87e3 to 8.07e3...
  []
  [Argon_fluid_props]
    type = IdealGasFluidProperties
    gamma = 1.667 # Noble gas
    molar_mass = 39.948e-3
    mu = 3.28E-5 # Viscosity Pa-s at 200*C # #
    k = 0.0172 # W/m*K
  []

  [water_fp] # used for EOS
    type = Water97FluidProperties
  []
[]

[Functions]
  
  [water-rho]
    type = PiecewiseLinear
    data_file = water_eos_P101325_1000.csv
    xy_in_file_only = false
    x_index_in_file = 0
    y_index_in_file = 1
    format = columns
  []
  [water-cp]
    type = PiecewiseLinear
    data_file = water_eos_P101325_1000.csv
    xy_in_file_only = false
    x_index_in_file = 0
    y_index_in_file = 2
    format = columns
  []
  [water-k]
    type = PiecewiseLinear
    data_file = water_eos_P101325_1000.csv
    xy_in_file_only = false
    x_index_in_file = 0
    y_index_in_file = 3
    format = columns
  []
  [water-mu]
    type = PiecewiseLinear
    data_file = water_eos_P101325_1000.csv
    xy_in_file_only = false
    x_index_in_file = 0
    y_index_in_file = 4
    format = columns
  []
  # [water-sigma]
  #   type = PiecewiseLinear
  #   data_file = water_eos_P101325_1000.csv
  #   xy_in_file_only = false
  #   x_index_in_file = 0
  #   y_index_in_file = 5
  #   format = columns
  # []
  [injection_loc] # Spatial domains of bubble injection
      type = PiecewiseConstant
      x = '0.0  0.1   0.8    0.81'
      y =  '1.  0     0.0       0' # 
      direction = left_inclusive
      axis = x
  []
  [time_dependance]
    type = PiecewiseConstant
    x = '-5000 0'
    y = '0 1'
  []
  [scaling_density]
    type = ConstantFunction
    value = ${fparse ${injection_vol_rate} * ${ar_density} / (pi* (0.87*0.0254)^2 / 4 * 0.1)} #0.00504 #504# 5.04
      # 1.5e-5 gas injected  # rho ~= 1.29 kg/m3 (ideal gas) # h = 0.01 m # A =  0.0003835 # m^2# ${fparse pi* (0.87^2 / 4 * 0.0254}
      # P / (R * T) = M / V = 1.01e5 / (8.314/ 0.039948 * 319.6) = 1.518
      #  1.5e-5 * 1.29/(.01* 0.0003835) =  5.045632333767927
      #  1.5e-5 * 1.29/(.1* 0.0003835) =   0.5045632333767927
  []
  [injection]
    type = CompositeFunction
    functions = 'injection_loc time_dependance scaling_density'
  []
[]




[ComponentInputParameters] # used when you have repeated components, so you don't have to type as much
  [ss_pipe]
    type = PBPipeParameters
    A = 0.0003835 # m^2# ${fparse pi* 0.87^2 / 4 * 0.0254} # I think cross-sectional area. Does this need to match test section? Can rest be same diameter except for TS?
    Dh = 0.022098 # m ${fparse 0.87*.0254} #  Hydraulic diameter, 4*A / p = D
    hs_type = cylinder
    n_wall_elems = '1' # '3' # num of radial elements in the pipe wall, not the fluid
    wall_thickness = '0.003302' #
    material_wall = 'ss-mat'

  []
  [flow_channel]
    type = PBOneDFluidComponentParameters
    A = 0.0003835 # m^2# ${fparse pi* 0.87^2 / 4 * 0.0254} # I think cross-sectional area. Does this need to match test section? Can rest be same diameter except for TS?
    Dh = 0.022098 # m ${fparse 0.87*.0254} #  Hydraulic diameter, 4*A / p = D
  []
[]  # Can adjust heat loss and heat input by pinning temp and having varying heat input # Look at Jadyn's approach, compare
    # Putting the reference paper above the upcomer, it seems to help and hit large time steps with

[Components]

  # Switch from PBOneDFluidComponent to PBPipe if you want to simulate the pipe wall, insulation, and ambient heat loss
  [up1]
    type = PBOneDFluidComponent # PBPipe # Updating with what Jadyn used
    input_parameters = flow_channel # this may need to be removed bc no longer pipe # Meaning I would heed to add A and Dh back in probably
    position = '0 0 0'
    orientation = '0 0 1'
    length = ${fparse 36 * 0.0254}   # 0.9144 meters
    n_elems = ${nodes} # number of axial elements in direction of flow # If you change this, change postprocessor TS_TP

    gas_source = 'injection' # 'injection' # 3.0 #
  []

  [CoolingJacket]
    type = PBPipe # Jadyn coupled a heat tructure on pipe wall... why not just use pipe?
    position =   ${end_pipe_up}
    orientation =  '0  ${fparse cos(0.349)}  ${fparse -1 * sin(0.349)}' # Assuming in radians, 20*
    input_parameters = ss_pipe
    length = ${fparse 36 * 0.0254}
    n_elems = ${nodes} # She used 10, I want to use 12 for each

    # f = 0.02 # FIXME: Use convective flux BC to have a temp pin
     # in sourcecode  can go to SAM/tests/ --> regression tests have ex of diff model and components; can look at PBPipe tests for more examples
    # heat_source = '${fparse -1 * ${heater_power} / 2}' # Instead of heat source, want BC on outside of wall;  # Change to flux BC
    HS_BC_type = 'Convective' # 'Adiabatic'
    T_amb = ${T_c}
    h_amb = ${h_amb} # HTC
    Hw = ${h_amb}
  []

  [Melter] # Provides a pressure pin of sorts.. should help with stability
    type = PBOneDFluidComponent
    position = ${end_pipe_up} # '${end_cooling_jacket}' # Travis moved melter to top left... not what is in experiment, but might help stabilize pressure
    orientation = '0 0 1'
    input_parameters = flow_channel
    length = ${fparse 6 * sin(0.349) * 0.0254} # Made the outlet much smaller
    n_elems = ${nodes_melter}
    A = ${fparse 0.0003835} # m^2 # ${fparse pi* 0.87^2 / 4 * 0.0254}
  []


  [downcomer]
    type = PBOneDFluidComponent
    position = ${end_cooling_jacket}
    orientation = '0 0 -1'
    input_parameters = flow_channel

    length =  ${fparse (36) * 0.0254}
    n_elems = ${nodes}
  []


  [Heater] # For an external heating, consider changing to wall heat flux;
    type = PBOneDFluidComponent
    position =    ${ht_entry_loc}
    orientation = '0  ${fparse -1*cos(0.349)}   ${fparse sin(0.349)}' # Assuming in radians, 20*
    input_parameters = flow_channel

    length = ${fparse 36 * 0.0254} # meters
    n_elems = ${nodes}

    # f = 0.02     #

    heat_source = ${heater_power} # volumetric heat source # average over fluid volume 👁️👁️
  []



  [TopLeft]  # It looks like it connects pipes...
      type = PBBranch
      inputs = 'up1(out)'
      outputs = 'CoolingJacket(in) Melter(in)'
      K = '0.0 1.8 1.8'
      Area = 0.0003835 # This area is the pipe CS area

  []

  [TopRight]
      type = PBSingleJunction
      inputs = 'CoolingJacket(out)'
      outputs = 'downcomer(in)'
      K = 1.8


  []

  [pipe5_out_pressure_pin]
    type = PBTDV
    input = 'Melter(out)'
    p_bc = ${p_out} # Pressure pin at same P as initial of system... Hopefully no more salt flowing out of system
    T_bc = ${T_h}
  []

  [BottomRight]
      type = PBSingleJunction
      inputs = 'downcomer(out)'
      outputs = 'Heater(in)'
      K = 1.8

  []

  [BottomLeft]
      type = PBSingleJunction
      inputs = 'Heater(out)'
      outputs = 'up1(in)'
      K = 1.8
  []
[]

[Postprocessors]
  [TS_cp]
    type = FunctionValuePostprocessor
    function = 'water-cp'
    time = 'TP_TS'
    indirect_dependencies = 'TP_TS'
  []
  [TS_mu]
    type = FunctionValuePostprocessor
    function = 'water-mu'
    time = 'TP_TS'
    indirect_dependencies = 'TP_TS'
  []
  [TS_k]
    type = FunctionValuePostprocessor
    function = 'water-k'
    time = 'TP_TS'
    indirect_dependencies = 'TP_TS'
  []
  # [TS_surface_tension] # Ready for whenever function allowed for sigma
  #   type = FunctionValuePostprocessor
  #   function = 'sigma'
  #   time = 'TP_TS'
  #   indirect_dependencies = 'TP_TS'
  # []
  [00_TS_Pr]
    type = ParsedPostprocessor
    expression = 'cp * mu / k'
    pp_symbols = 'cp mu k'
    pp_names = 'TS_cp TS_mu TS_k'
  []

  ## Validation Metrics


  [00_DeltaT]
    type = ParsedPostprocessor
    pp_names = 'TP6 TP2'
    function = 'TP6 - TP2'
  []

  [00_TS_vel]
    type = ComponentNodalVariableValue
    input = up1(${midnode})
    variable = velocity
  []


  [01_TS_gas_velocity]
    type = ComponentNodalVariableValue
    variable = gas_velocity
    input = up1(${midnode})
  []

  [01_TS_gas_void]
    type = ComponentNodalVariableValue
    variable = gas_void
    input = up1(${midnode})
  []

  [01_TS_gas_deq]
    type = ParsedPostprocessor
    expression = '2*TS_bubble_radius'
    pp_names = 'TS_bubble_radius'
  []

  [02_reldif_Pr]
    type = RelativeDifferencePostprocessor
    value1 = 00_TS_Pr
    value2 = ${target_Pr}
  []
  [02_reldif_vel]
    type = RelativeDifferencePostprocessor
    value1 = 00_TS_vel
    value2 = ${target_vel}
  []
  [02_reldif_deltaT]
    type = RelativeDifferencePostprocessor
    value1 = 00_DeltaT
    value2 = ${target_deltaT}
  []
  # Gas Diff postprocessors
  [021_dif_gas_d_eq]
    type = DifferencePostprocessor
    value1 = ${target_bubble_d_eq}
    value2 = 01_TS_gas_deq
  []
  [021_dif_gas_terminal_vel]
    type = DifferencePostprocessor
    value1 = ${target_gas_vel} 
    value2 = 01_TS_gas_velocity
  []
  [021_dif_void_frac]
    type = DifferencePostprocessor
    value1 = ${target_void_frac}
    value2 = 01_TS_gas_void
  []
  [03_reldif_gas_d_eq]
    type = RelativeDifferencePostprocessor
    value1 = 01_TS_gas_deq
    value2 = ${target_bubble_d_eq}
  []
  [03_reldif_gas_terminal_vel]
    type = RelativeDifferencePostprocessor
    value1 = 01_TS_gas_velocity
    value2 = ${target_gas_vel}
  []
  [03_reldif_void_frac]
    type = RelativeDifferencePostprocessor
    value1 = 01_TS_gas_void
    value2 = ${target_void_frac}
  []
    # Extra important

  [TS_gas_velocity]
    type = ComponentNodalVariableValue
    variable = gas_velocity
    input = up1(${midnode})
  []
  # [TS_surface_tension] # Will this work?? # Unsure how to output sigma... :( 
  #   type = ComponentNodalVariableValue
  #   variable = sigma
  #   input = up1(${midnode})
  # []
  [TS_gas_void]
    type = ComponentNodalVariableValue
    variable = gas_void
    input = up1(${midnode})
  []
  [TS_bubble_radius]
    type = ComponentNodalVariableValue
    variable = bubble_radius
    input = up1(${midnode})
  []
  [TP1]                                  # Temperature
    type = ComponentBoundaryVariableValue
    variable = temperature
    input = downcomer(in)
  []
  [TP2]                                  # Temperature Probe
    type = ComponentBoundaryVariableValue
    variable = temperature
    input = Heater(in)
  []
  [TP3]                                  # Temperature Probe
    type = ComponentBoundaryVariableValue
    variable = temperature
    input = up1(in)
  []
  [TP_TS]
    type = ComponentNodalVariableValue                               # Temperature Probe
    input = up1(${midnode}) # this needs to update with discretization of up1
    variable = temperature
  []

  [TS_vel]                  
    type = ComponentNodalVariableValue
    input = up1(${midnode}) # this needs to update with discretization of up1 # unrecognized "end" but I am trying to put a node number
    variable = velocity
  []

  [TP6]                                  # Temperature at inlet of TP6
    type = ComponentBoundaryVariableValue
    variable = temperature
    input = CoolingJacket(in)
  []
  # [Bottom_Left_bubble_radius]
  #   type = ComponentNodalVariableValue
  #   variable = bubble_radius
  #   input = up1(0)
  # []
  # [Top_Left_bubble_radius]
  #   type = ComponentNodalVariableValue
  #   variable = bubble_radius
  #   input = up1(9)
  # []

  # [TS_gas_int_area]
  #   type = ComponentNodalVariableValue
  #   variable = gas_int_area
  #   input = up1(${midnode})
  # []
  # [Bottom_Left_gas_int_area]
  #   type = ComponentNodalVariableValue
  #   variable = gas_int_area
  #   input = up1(0)
  # []
  # [Top_Left_gas_int_area]
  #   type = ComponentNodalVariableValue
  #   variable = gas_int_area
  #   input = up1(9)
  # []

  # [bottom_right_gas_content]
  #   type = ComponentNodalGasMassFlowRate
  #   input = downcomer(9)
  # []
  # [Top_right_gas_content]
  #   type = ComponentNodalGasMassFlowRate
  #   input = downcomer(0)
  # []

  # [TS_gas_content_kgPers] # KG/s
  #   type = ComponentNodalGasMassFlowRate
  #   input = up1(${midnode})
  # []
  [bot_right_gas_void]
    type = ComponentNodalVariableValue
    variable = gas_void
    input = downcomer(9)
  []

  # [top_left_gas_corner]
  #   type = ComponentNodalGasMassFlowRate
  #   input = up1(9)
  # []
  [dt]
    type = TimestepSize
  []
  # [run_time]
  #   type = PerfGraphData
  #   data_type = TOTAL
  #   section_name = Root
  # []

  # [massFlowRate]                                      # Output mass flow rate at inlet of TS
  #   type = ComponentBoundaryFlow
  #   input = CoolingJacket(in)
  # []

  [TopL_velocity]                                  # Output velocity at inlet of CH1
    type = ComponentBoundaryVariableValue
    variable = velocity
    input = CoolingJacket(in)
  []
  #  [Vel_downcomer_in]                                  # Output velocity at inlet of CH1
  #   type = ComponentBoundaryVariableValue
  #   variable = velocity
  #   input = downcomer(in) #                             The difference in vel topL vel and downcomer in vel is the vel input from the branched element. It is mass that flows into or out of the system.
  # []
  #  [downcomer_out_velocity]                                  # Output velocity at inlet of CH1
  #   type = ComponentBoundaryVariableValue
  #   variable = velocity
  #   input = downcomer(out)
  # []


  [delta_Temp_TP6-TP2]
    type = ParsedPostprocessor
    pp_names = 'TP6 TP2'
    function = 'TP6 - TP2'
  []

  [coolingJacket_T_in_primary]                                  # Temperature at IHX inlet
    type = ComponentBoundaryVariableValue
    variable = temperature
    input = CoolingJacket(in)
  []

  [coolingJacket_T_out_primary]                                  # Temperature at IHX outlet
    type = ComponentBoundaryVariableValue
    variable = temperature
    input = CoolingJacket(out)
  []

  [TS_rhog]
    type = ComponentNodalVariableValue
    input = up1(${midnode})
    variable = rhog
  []

  [TS_pressure]
    type = ComponentNodalVariableValue
    input = up1(${midnode})
    variable = pressure
  []
[]

[Preconditioning] # Advised not to touch these
  [SMP_PJFNK]
    type = SMP
    full = true
    solve_type = 'PJFNK'
    petsc_options_iname = '-pc_type -ksp_gmres_restart' # ksp_gmres is the number of nonlinear iterations
    petsc_options_value = 'lu 101' # I don't know what these do, I won't touch them yet
  []
[]

[Functions]
  [time_stepper] # Determines max timestep in domain, bc timestepper uses min timestep available
    type = PiecewiseConstant
    x = '-5000  -10   3. '
    y = ' 200    0.1  2.0  '
    direction = left_inclusive
  []
[]

[Executioner] # Creating timestepper
  type =  Transient #  SAMSegregatedTransient #
  # solve_type = 'PJFNK'  # PJFNK JFNK NEWTON FD LINEAR # no n
  start_time = -500
  end_time = 200 # 1e3 used by Travis
  dtmin = 1e-7 # after this point starts diverging
  automatic_scaling = false

  scheme = ${scheme}

  dt = ${const_TS}

  dtmax = 100

  [TimeSteppers]
    [IterationAdaptiveDT]
      type = IterationAdaptiveDT
      growth_factor = 1.1
      optimal_iterations = 8
      linear_iteration_ratio = 150
      dt = 0.01
      cutback_factor = 0.8
      cutback_factor_at_failure = 0.5
    []

    [FunctionDT]
      type = FunctionDT
      function = time_stepper
      min_dt = 1e-6
    []
  []

  # These values are a good starting point
  nl_rel_tol = 1e-7 # -6
  nl_abs_tol = 1e-6 # -7 # e-6 could be too high, want abs to be couple order magn below rel, charlie suggests e-8
  nl_max_its = 12 # Consider increasing to 20
  l_tol =      1e-5
  l_max_its = 100

  [Quadrature]
    type =  ${quad_type}  # GAUSS # # For second, do Gauss or simpson # For first, do Trap
    order = ${quad_order} # SECOND # Needs to be same order as p_order at the very top
  []
[]



[Outputs]
  print_linear_residuals = false
  perf_graph = true
  checkpoint = true

  # show_var_residual_norms = true
  # show_top_residuals = 3
  [out]
    type = Exodus
    use_displaced = true # always keep true to let mesh look good
    execute_on = 'initial timestep_end'
    sequence = false
  []
  [csv]
    type = CSV
    sync_times = '0.0'
  []
  [console]
    type = Console
    execute_scalars_on = 'none'
  []
[]
