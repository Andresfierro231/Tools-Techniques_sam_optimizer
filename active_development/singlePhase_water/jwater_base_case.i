################## MSFL Draft Script
### First Created: 12 Jun 25 
# ⭐⭐ Today editing: 30 Jun 25
# 
# 
#                             SALT 1 SAM - Replicating Jadyn's Build

# - Goals -
# [] Replicate Jadyn's paper description of SAM
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


fric_factor = 0.064
q_net = 44.5 # W # Note, I don't think she is using Q_heater
T_c = 313.48 # Pin the temperature you want the cooler to cool fluid to #${fparse 168.22 + 273.15} # Use measured temp at TP1  # 168.22 + 273.15 = 441.37


T_h = 314  # Turns out simulation stability is incredibly sensitive to value chosen here, but not numerical result for some strange reason # Maybe not highest temp, but avg temp of loop? 
p_0 = 1.1e5 # 1.01e5 # try change to 1.5 or 2 # Initial pressure, and ambient
T_0 = 314 # T_0 = T_c # 441.37 # 430 # Kelvin # Initial System, start a bit warmer than T_c


v_0 = 0.02 # 0.0185
h_amb = 1e5  # Arbitrarily large, as specified in paper


# TS Const
const_TS = 10 # s

# Quadrature Settings
p_order_quadPnts = 2 # 1
quad_type = GAUSS # TRAP
quad_order = SECOND # FIRST
scheme =  implicit-euler # BDF2 #    # # crank-nicolson # 

###### Under the hood -- Making usable ########
heater_power = ${fparse ${q_net} / (0.0003835 * 36 * 0.0254)} # # Volumetric # Watts / m^3 # m^3 = area * length_inches * conversion # SI units # Can use ipython as calc

##############################################################################################################

# Geometry  and Positions
end_pipe_up =        '0  0      ${fparse (36) * 0.0254}'
end_cooling_jacket = '0  ${fparse (36* cos(0.349)) * 0.0254}      ${fparse (36 - 36 * sin(0.349)) * 0.0254}'
ht_entry_loc =       '0  ${fparse (36* cos(0.349)) * 0.0254}      ${fparse ( - 36 * sin(0.349)) * 0.0254}'


[GlobalParams]
  global_init_P = ${p_0}                      # I think this is ambient pressure # Global initial fluid pressure # --> Depends on problem, IC to make problem converge, changing IC and scaling factor to make converge
  global_init_V = ${v_0} # Probably shouldn't start with zero velocity, and in loop they defined 1.5 originally             # Global initial fluid velocity
  global_init_T = ${T_0} # Kelvin # Starting water luke-warm           # I am pretty sure SAM uses Kelvin          # Global initial temperature for fluid and solid

  p_order = ${p_order_quadPnts} # 1 # Specifies the order of mesh... How many quadrature points in FE sol # P order 1 runs faster but not as accurate
  gravity = '0 0 -9.8' # switched sign gravity

  # Trying debug
  f = ${fric_factor} #6.5 # Use global friction factor
[]

[EOS] 

  [air_eos]
    type = AirEquationOfState # HeEquationOfState # # N, He, Na
  []
  [eos] # Water # active eos should be called eos
    type = PTFluidPropertiesEOS
    fp = water_fp
    p_0 =  ${p_0}
  []
[]


 
[MaterialProperties]
  [ss-mat] # my HX is SS 315, manual says ss HT9 and D9 are implemented, but I don't see an example on how to use D9... D9 looks like closest to SS-316... constant is probably faster though 
    type = SolidMaterialProps
    k = 15 # K ranges from (13 - 17) https://www.azom.com/properties.aspx?ArticleID=863
    Cp = 500 #638 # Ranges from 490 - 530
    rho = 7.7e3 # Density is reported to range from 7.87e3 to 8.07e3... 
  []
  [water_fp] # used for EOS
    type = Water97FluidProperties
  []
[]

[ComponentInputParameters] # used when you have repeated components, so you don't have to type as much
  [ss_pipe]
    type = PBPipeParameters
    eos = eos
    A = 0.0003835 # m^2# ${fparse pi* 0.87^2 / 4 * 0.0254} # I think cross-sectional area. Does this need to match test section? Can rest be same diameter except for TS?
    Dh = 0.022098 # m ${fparse 0.87*.0254} #  Hydraulic diameter, 4*A / p = D
    hs_type = cylinder
    n_wall_elems = '1' # '3' # num of radial elements in the pipe wall, not the fluid    
    wall_thickness = '0.003302' # 
    material_wall = 'ss-mat'

  []
  [flow_channel]
    type = PBOneDFluidComponentParameters
    eos = eos
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
    eos = eos # should be able to comment this out
    position = '0 0 0'
    orientation = '0 0 1'
    length = ${fparse 36 * 0.0254}  # 14.34 inches up z # 0.364 # Meters
    n_elems = 10 # number of axial elements in direction of flow # If you change this, change postprocessor TS_TP
   
  []

  [CoolingJacket]
    type = PBPipe # Jadyn coupled a heat tructure on pipe wall... why not just use pipe? 
    eos = eos
    position =   ${end_pipe_up}
    orientation =  '0  ${fparse cos(0.349)}  ${fparse -1 * sin(0.349)}' # Assuming in radians, 20*
    input_parameters = ss_pipe

    length = ${fparse 36 * 0.0254} 
    n_elems = 10 # She used 10, I want to use 12 for each

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
    eos = eos
    position = ${end_pipe_up} # '${end_cooling_jacket}' # Travis moved melter to top left... not what is in experiment, but might help stabilize pressure
    orientation = '0 0 1'
    input_parameters = flow_channel

    length = ${fparse 6 * sin(0.349) * 0.0254} # Made the outlet much smaller
    n_elems = 2
    A = ${fparse 0.0003835} # m^2 # ${fparse pi* 0.87^2 / 4 * 0.0254}
  []


  [downcomer]
    type = PBOneDFluidComponent
    eos = eos
    position = ${end_cooling_jacket}
    orientation = '0 0 -1'

    input_parameters = flow_channel

    length =  ${fparse (36) * 0.0254}
    n_elems = 10 
  []


  [Heater] # For an external heating, consider changing to wall heat flux; 
    type = PBOneDFluidComponent 
    eos = eos
    position =    ${ht_entry_loc}
    orientation = '0  ${fparse -1*cos(0.349)}   ${fparse sin(0.349)}' # Assuming in radians, 20*
    input_parameters = flow_channel

    length = ${fparse 36 * 0.0254} # meters
    n_elems = 10

    # f = 0.02     # 

    heat_source = ${heater_power} # volumetric heat source # average over fluid volume 👁️👁️
  []



  [TopLeft]  # It looks like it connects pipes... 
      type = PBBranch
      inputs = 'up1(out)'
      outputs = 'CoolingJacket(in) Melter(in)'
      eos = eos
      K = '0.0 1.8 1.8' 
      Area = 0.0003835 # This area is the pipe CS area

  []

  [TopRight]   
      type = PBSingleJunction
      inputs = 'CoolingJacket(out)'
      outputs = 'downcomer(in)'
      K = 1.8

      eos = eos
      
  []

  [pipe5_out_pressure_pin]
    type = PBTDV
    input = 'Melter(out)'
    eos = eos
    p_bc = ${p_0} # Pressure pin at same P as initial of system... Hopefully no more salt flowing out of system
    T_bc = ${T_h} 
  []

  [BottomRight]   
      type = PBSingleJunction
      inputs = 'downcomer(out)'
      outputs = 'Heater(in)'
      eos = eos
      K = 1.8

  []

  [BottomLeft] 
      type = PBSingleJunction
      inputs = 'Heater(out)'
      outputs = 'up1(in)'

      eos = eos
      K = 1.8

  []

[]



[Postprocessors] # Will need to fix all of these... 
  [massFlowRate]                                      # Output mass flow rate at inlet of TS
    type = ComponentBoundaryFlow
    input = CoolingJacket(in)
  []

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
   [downcomer_out_velocity]                                  # Output velocity at inlet of CH1
    type = ComponentBoundaryVariableValue
    variable = velocity
    input = downcomer(out)
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
  [TS_TP]
    type = ComponentNodalVariableValue                               # Temperature Probe
    input = up1(4) # this needs to update with discretization of up1

    variable = temperature
  []

  [TS_vel]                    # Was not able to get this running :(              
    type = ComponentNodalVariableValue

    input = up1(4) # this needs to update with discretization of up1 # unrecognized "end" but I am trying to put a node number

    variable = velocity
  []
  
  [TP6]                                  # Temperature at inlet of TP6
    type = ComponentBoundaryVariableValue
    variable = temperature
    input = CoolingJacket(in)
  []
 
  [delta_t]
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

# [Executioner] # Change out once mesh is correct
 #   type = mesh-only
 # []

[Executioner] # Creating timestepper
  type =  Transient #  SAMSegregatedTransient #
  # solve_type = 'PJFNK'  # PJFNK JFNK NEWTON FD LINEAR # no n
  # start_time = 0
  end_time = 1e6 # 1e3 used by Travis 
  dtmin = 1e-7 # after this point starts diverging
  automatic_scaling = false
  
  scheme = ${scheme}

  dt = ${const_TS}

  dtmax = 3600
  [TimeStepper]
    type = IterationAdaptiveDT
    optimal_iterations = 10
    iteration_window = 4
    dt = 0.01 # 100
    growth_factor = 1.15     # Step size multiplier if solve is good
    cutback_factor = 0.8     # Step size divisor if solve is poor    
    
  []

  # These values are a good starting point
  nl_rel_tol = 1e-7 # -6
  nl_abs_tol = 1e-6 # -7 # e-6 could be too high, want abs to be couple order magn below rel, charlie suggests e-8
  nl_max_its = 20 # Consider increasing to 20
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
  [out_displaced]
    type = Exodus
    use_displaced = true # always keep true to let mesh look good
    execute_on = 'initial timestep_end'
    sequence = false
  []
  [csv]
    type = CSV
  []
  [console]
    type = Console
    execute_scalars_on = 'none'
  []
[]


# PB means Primitive Based - Like based on values P, T, v --> Comes from Relap 
