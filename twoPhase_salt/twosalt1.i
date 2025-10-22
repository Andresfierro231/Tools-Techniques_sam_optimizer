!include jsalt_base_case.i

# Vel: 0.032
# Delta T: 11.02

target_Pr := 15.60
target_vel := 0.032
target_deltaT := 11.02

target_bubble_d_eq  := 0.0105
target_gas_vel := 0.2214
target_void_frac    := 0.0504

We_exp := 10.5
injection_vol_rate := 1e-6 # Maybe 1e-5 is a typo? 1.5e-6 gives more reasonable results

fric_factor := 0.55 # 318
T_c := 486 # 514.13 # Pin the temperature you want the cooler to cool fluid to #${fparse 168.22 + 273.15} # Use measured temp at TP1  # 168.22 + 273.15 := 441.37
q_net := 550 # W


T_h := 492 # 525   # Turns out simulation stability is incredibly sensitive to value chosen here, but not numerical result for some strange reason # Maybe not highest temp, but avg temp of loop?
T_0 := 492   # T_0 := T_c # 441.37 # 430 # Kelvin # Initial System, start a bit warmer than T_c

[Functions]
  [time_stepper] # Determines max timestep in domain, bc timestepper uses min timestep available
    x := '-5000  -10   3. '
    y := ' 200    0.1  .50  '
  []
[]


p_0 := 1.1e5 # 1.01e5 # try change to 1.5 or 2 # Initial pressure, and ambient
v_0 := 0.02 # 0.0185
h_amb := 1e5  # Arbitrarily large, as specified in paper
p_out := 1.1e5

# Quadrature Settings
p_order_quadPnts :=   1     #  2      #
quad_type :=          TRAP  #  GAUSS  #
quad_order :=         FIRST #  SECOND #
scheme :=  implicit-euler # BDF2 #    # # crank-nicolson #
node_multiplier := 8 # This does something but I don't know what it is so I won't touch it... 


# Uncomment to run TH-only

# [Executioner]
#   end_time := 0.0
# []

