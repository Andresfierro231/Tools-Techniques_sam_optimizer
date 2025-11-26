!include jsalt_base_case.i

target_Pr := 36.50
target_vel := 0.030
target_deltaT := 10.27


We_exp := 3.5
injection_vol_rate := 3.5e-7

fric_factor := 0.5 #346
T_c := 450 #462.5 # Pin the temperature you want the cooler to cool fluid to #${fparse 168.22 + 273.15} # Use measured temp at TP1  # 168.22 + 273.15 := 441.37
q_net := 560 #385 # W


T_h := 470.5  # Turns out simulation stability is incredibly sensitive to value chosen here, but not numerical result for some strange reason # Maybe not highest temp, but avg temp of loop?
T_0 := 460   # T_0 := T_c # 441.37 # 430 # Kelvin # Initial System, start a bit warmer than T_c



p_0 := 1.1e5 # 1.01e5 # try change to 1.5 or 2 # Initial pressure, and ambient
v_0 := 0.02 # 0.0185
h_amb := 1e5  # Arbitrarily large, as specified in paper
p_out := 1.1e5



# Quadrature Settings
p_order_quadPnts :=   1     #  2      #
quad_type :=          TRAP  #  GAUSS  #
quad_order :=         FIRST #  SECOND #
scheme :=  implicit-euler # BDF2 #    # # crank-nicolson #
node_multiplier := 5

[Functions]
  [time_stepper] # Determines max timestep in domain, bc timestepper uses min timestep available
    x := '-5000  -10   3. '
    y := ' 200    0.1  1.0  '
  []
    [injection_loc] # Spatial domains of bubble injection
        x := '0 0.4  0.5   0.8    0.81'
        y := '0 1.  0     0.0       0' # '0.0 gas_injection_rate 0.0   gas_remove_rate 0' #
    []

[]

# Uncomment to run TH-only

# [Executioner]
#   end_time := 0.0
# []
