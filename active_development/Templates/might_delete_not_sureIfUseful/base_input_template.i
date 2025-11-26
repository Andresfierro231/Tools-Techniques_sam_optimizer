################## MSFL Draft Script
### First Created: 18 Oct 25
# ⭐⭐ Today editing: 18 Oct 25
# 
# 
#                             SALT Base Case - Using for parameter tuning
#  
# Initially copied from jsalt_base_case.i

######    --> I don't know if I am using this anywhere 12 Nov 25
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


T_h = 446  # Turns out simulation stability is incredibly sensitive to value chosen here, but not numerical result for some strange reason # Maybe not highest temp, but avg temp of loop? 
p_0 = 1.1e5 # 1.01e5 # try change to 1.5 or 2 # Initial pressure, and ambient
T_0 = 442 # T_0 = T_c # 441.37 # 430 # Kelvin # Initial System, start a bit warmer than T_c


v_0 = 0.02 # 0.0185
h_amb = 1e5  # Arbitrarily large, as specified in paper
p_out = 1.1e5

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

# How do I add temperature probes at these locations??
# ts_in_loc =          '0  0      ${fparse 14.34 * 0.0254}' 
# ts_out_loc =         '0  0      ${fparse (14.34 + 7.32) * 0.0254}' # Will keep ts locations for postprocessors

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


  [eos] #hitec # active eos should be called eos

    type = TabulatedEquationOfState 
    interp_type = Linear 
    temperature = '  381.     	382.     	383.     	384.     	385.     	386.     	387.     	388.     	389.     	390.     	391.     	392.     	393.     	394.     	395.     	396.     	397.     	398.     	399.     	400.     	401.     	402.     	403.     	404.     	405.     	406.     	407.     	408.     	409.     	410.     	411.     	412.     	413.     	414.     	415.     	416.     	417.     	418.     	419.     	420.     	421.     	422.     	423.     	424.     	425.     	426.     	427.     	428.     	429.     	430.     	431.     	432.     	433.     	434.     	435.     	436.     	437.     	438.     	439.     	440.     	441.     	442.     	443.     	444.     	445.     	446.     	447.     	448.     	449.     	450.     	451.     	452.     	453.     	454.     	455.     	456.     	457.     	458.     	459.     	460.     	461.     	462.     	463.     	464.     	465.     	466.     	467.     	468.     	469.     	470.     	471.     	472.     	473.     	474.     	475.     	476.     	477.     	478.     	479.     	480.     	481.     	482.     	483.     	484.     	485.     	486.     	487.     	488.     	489.     	490.     	491.     	492.     	493.     	494.     	495.     	496.     	497.     	498.     	499.     	500.     	501.     	502.     	503.     	504.     	505.     	506.     	507.     	508.     	509.     	510.     	511.     	512.     	513.     	514.     	515.     	516.     	517.     	518.     	519.     	520.     	521.     	522.     	523.     	524.     	525.     '
    mu  =         '2.848E-02	2.814E-02	2.781E-02	2.749E-02	2.716E-02	2.684E-02	2.653E-02	2.621E-02	2.590E-02	2.559E-02	2.528E-02	2.498E-02	2.468E-02	2.438E-02	2.408E-02	2.379E-02	2.350E-02	2.321E-02	2.293E-02	2.264E-02	2.236E-02	2.209E-02	2.181E-02	2.154E-02	2.127E-02	2.100E-02	2.074E-02	2.048E-02	2.022E-02	1.996E-02	1.971E-02	1.945E-02	1.920E-02	1.896E-02	1.871E-02	1.847E-02	1.823E-02	1.799E-02	1.776E-02	1.752E-02	1.729E-02	1.707E-02	1.684E-02	1.662E-02	1.640E-02	1.618E-02	1.596E-02	1.575E-02	1.554E-02	1.533E-02	1.512E-02	1.492E-02	1.471E-02	1.451E-02	1.431E-02	1.412E-02	1.392E-02	1.373E-02	1.354E-02	1.336E-02	1.317E-02	1.299E-02	1.281E-02	1.263E-02	1.245E-02	1.227E-02	1.210E-02	1.193E-02	1.176E-02	1.160E-02	1.143E-02	1.127E-02	1.111E-02	1.095E-02	1.079E-02	1.064E-02	1.049E-02	1.033E-02	1.019E-02	1.004E-02	9.893E-03	9.750E-03	9.608E-03	9.469E-03	9.331E-03	9.195E-03	9.061E-03	8.929E-03	8.798E-03	8.669E-03	8.542E-03	8.417E-03	8.294E-03	8.172E-03	8.052E-03	7.934E-03	7.817E-03	7.702E-03	7.589E-03	7.477E-03	7.367E-03	7.259E-03	7.152E-03	7.047E-03	6.944E-03	6.842E-03	6.741E-03	6.643E-03	6.545E-03	6.450E-03	6.356E-03	6.263E-03	6.172E-03	6.082E-03	5.994E-03	5.907E-03	5.822E-03	5.738E-03	5.656E-03	5.575E-03	5.495E-03	5.417E-03	5.341E-03	5.265E-03	5.191E-03	5.118E-03	5.047E-03	4.977E-03	4.908E-03	4.841E-03	4.775E-03	4.710E-03	4.646E-03	4.584E-03	4.522E-03	4.463E-03	4.404E-03	4.346E-03	4.290E-03	4.235E-03	4.181E-03	4.128E-03	4.076E-03	4.026E-03	3.976E-03'
    rho =         '2.008E+03	2.007E+03	2.006E+03	2.006E+03	2.005E+03	2.004E+03	2.003E+03	2.003E+03	2.002E+03	2.001E+03	2.000E+03	2.000E+03	1.999E+03	1.998E+03	1.997E+03	1.997E+03	1.996E+03	1.995E+03	1.994E+03	1.994E+03	1.993E+03	1.992E+03	1.991E+03	1.991E+03	1.990E+03	1.989E+03	1.988E+03	1.988E+03	1.987E+03	1.986E+03	1.985E+03	1.985E+03	1.984E+03	1.983E+03	1.982E+03	1.982E+03	1.981E+03	1.980E+03	1.979E+03	1.979E+03	1.978E+03	1.977E+03	1.976E+03	1.976E+03	1.975E+03	1.974E+03	1.973E+03	1.973E+03	1.972E+03	1.971E+03	1.970E+03	1.970E+03	1.969E+03	1.968E+03	1.967E+03	1.967E+03	1.966E+03	1.965E+03	1.964E+03	1.964E+03	1.963E+03	1.962E+03	1.961E+03	1.961E+03	1.960E+03	1.959E+03	1.958E+03	1.958E+03	1.957E+03	1.956E+03	1.955E+03	1.955E+03	1.954E+03	1.953E+03	1.952E+03	1.952E+03	1.951E+03	1.950E+03	1.949E+03	1.949E+03	1.948E+03	1.947E+03	1.946E+03	1.946E+03	1.945E+03	1.944E+03	1.943E+03	1.943E+03	1.942E+03	1.941E+03	1.940E+03	1.940E+03	1.939E+03	1.938E+03	1.937E+03	1.937E+03	1.936E+03	1.935E+03	1.934E+03	1.934E+03	1.933E+03	1.932E+03	1.931E+03	1.931E+03	1.930E+03	1.929E+03	1.929E+03	1.928E+03	1.927E+03	1.926E+03	1.926E+03	1.925E+03	1.924E+03	1.923E+03	1.923E+03	1.922E+03	1.921E+03	1.920E+03	1.920E+03	1.919E+03	1.918E+03	1.917E+03	1.917E+03	1.916E+03	1.915E+03	1.914E+03	1.914E+03	1.913E+03	1.912E+03	1.911E+03	1.911E+03	1.910E+03	1.909E+03	1.908E+03	1.908E+03	1.907E+03	1.906E+03	1.905E+03	1.905E+03	1.904E+03	1.903E+03	1.902E+03	1.902E+03	1.901E+03	1900.01  '
    cp  =         '2.730E+03	2.724E+03	2.719E+03	2.714E+03	2.709E+03	2.703E+03	2.698E+03	2.693E+03	2.688E+03	2.683E+03	2.677E+03	2.672E+03	2.667E+03	2.662E+03	2.657E+03	2.652E+03	2.647E+03	2.642E+03	2.636E+03	2.631E+03	2.626E+03	2.621E+03	2.616E+03	2.611E+03	2.606E+03	2.601E+03	2.596E+03	2.592E+03	2.587E+03	2.582E+03	2.577E+03	2.572E+03	2.567E+03	2.562E+03	2.557E+03	2.553E+03	2.548E+03	2.543E+03	2.538E+03	2.534E+03	2.529E+03	2.524E+03	2.519E+03	2.515E+03	2.510E+03	2.505E+03	2.501E+03	2.496E+03	2.491E+03	2.487E+03	2.482E+03	2.478E+03	2.473E+03	2.468E+03	2.464E+03	2.459E+03	2.455E+03	2.450E+03	2.446E+03	2.441E+03	2.437E+03	2.433E+03	2.428E+03	2.424E+03	2.419E+03	2.415E+03	2.411E+03	2.406E+03	2.402E+03	2.398E+03	2.393E+03	2.389E+03	2.385E+03	2.380E+03	2.376E+03	2.372E+03	2.368E+03	2.363E+03	2.359E+03	2.355E+03	2.351E+03	2.347E+03	2.343E+03	2.339E+03	2.334E+03	2.330E+03	2.326E+03	2.322E+03	2.318E+03	2.314E+03	2.310E+03	2.306E+03	2.302E+03	2.298E+03	2.294E+03	2.290E+03	2.286E+03	2.282E+03	2.278E+03	2.275E+03	2.271E+03	2.267E+03	2.263E+03	2.259E+03	2.255E+03	2.252E+03	2.248E+03	2.244E+03	2.240E+03	2.236E+03	2.233E+03	2.229E+03	2.225E+03	2.222E+03	2.218E+03	2.214E+03	2.211E+03	2.207E+03	2.203E+03	2.200E+03	2.196E+03	2.193E+03	2.189E+03	2.186E+03	2.182E+03	2.179E+03	2.175E+03	2.172E+03	2.168E+03	2.165E+03	2.161E+03	2.158E+03	2.154E+03	2.151E+03	2.148E+03	2.144E+03	2.141E+03	2.138E+03	2.134E+03	2.131E+03	2.128E+03	2.124E+03	2.121E+03	2.118E+03	2114.560 '
    
    k   =          '0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.54	0.55	0.55	0.55	0.55	0.55	0.55	0.55	0.55	0.55	0.55	0.55	0.55	0.55	0.55	0.55	0.55	0.55	0.55	0.55	0.55	0.55	0.55	0.55	0.55	0.55	0.55	0.55	0.55	0.55	0.55	0.55	0.55	0.55	0.56	0.56	0.56	0.56	0.56	0.56	0.56	0.56	0.56	0.56	0.56	0.56	0.56	0.56	0.56	0.56	0.56	0.56	0.56	0.56	0.56	0.56	0.56	0.56	0.56	0.56'


  [] 
  [air_eos]
    type = AirEquationOfState # HeEquationOfState # # N, He, Na
  []
[]


 
[MaterialProperties]
  [ss-mat] # my HX is SS 315, manual says ss HT9 and D9 are implemented, but I don't see an example on how to use D9... D9 looks like closest to SS-316... constant is probably faster though 
    type = SolidMaterialProps
    k = 15 # K ranges from (13 - 17) https://www.azom.com/properties.aspx?ArticleID=863
    Cp = 500 #638 # Ranges from 490 - 530
    rho = 7.7e3 # Density is reported to range from 7.87e3 to 8.07e3... 
  []

  # [water_fp] # used for EOS
  #   type = Water97FluidProperties
  # []
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
    Hw = ${h_amb} # can be const or function of space and time
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
    p_bc = ${p_out} # Pressure pin at same P as initial of system... Hopefully no more salt flowing out of system
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
