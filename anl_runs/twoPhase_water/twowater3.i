!include jwater_base_case.i
# Created:  1 Aug 2025
# Today is: 1 Aug 2025

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 
# 2Phase Water Test 3
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ 

target_Pr := 3.78
target_vel := 0.026
target_deltaT := 1.43

target_bubble_d_eq  := 0.0026
target_gas_vel := 0.2679
target_void_frac    := 0.0036


We_exp :=  4.496 # 2.73 #
injection_vol_rate := ${fparse 4.8e-7}


fric_factor := 0.07 #0.0417
T_c := 319 #319.2 # Pin the temperature you want the cooler to cool fluid to #${fparse 168.22 + 273.15} # Use measured temp at TP1  # 168.22 + 273.15 := 441.37
q_net := 60 #45 # W #



T_h := 322# 324 # 320.5 # 321 #324  # Turns out simulation stability is incredibly sensitive to value chosen here, but not numerical result for some strange reason # Maybe not highest temp, but avg temp of loop?
T_0 := 320 #323.5 # T_0 := T_c # 441.37 # 430 # Kelvin # Initial System, start a bit warmer than T_c


v_0 := 0.02 # 0.0185
h_amb := 1e5  # Arbitrarily large, as specified in paper
p_0 := 1.1e5 # 1.01e5 # try change to 1.5 or 2 # Initial pressure, and ambient


# Quadrature Settings
p_order_quadPnts :=   1     #  2      #
quad_type :=          TRAP  #  GAUSS  #
quad_order :=         FIRST #  SECOND #
scheme :=  implicit-euler # BDF2 #    # # crank-nicolson #
node_multiplier := 10 



[Functions]
  [time_stepper] # Determines max timestep in domain, bc timestepper uses min timestep available
    x := '-5000  -7   3. '
    y := ' 200    0.1  .25  '
  []
  [injection_loc] # Spatial domains of bubble injection
      x := '0.0 0.4  0.5   0.8    0.81'
      y := '0.0  1.  0     0.0       0' # 
  []
[]


[Executioner]
  start_time := -700
  end_time := 250.0
[]
