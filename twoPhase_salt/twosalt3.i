!include jsalt_base_case.i

target_Pr := 47.50
target_vel := 0.028
target_deltaT := 11.94

We_exp := 2.3
injection_vol_rate := 1.5e-7

fric_factor := 0.6 #0.4715
T_c := 435 #446 # Pin the temperature you want the cooler to cool fluid to #${fparse 168.22 + 273.15} # Use measured temp at TP1  # 168.22 + 273.15 := 441.37
q_net := 560 # W


T_h := 450 #472  # Turns out simulation stability is incredibly sensitive to value chosen here, but not numerical result for some strange reason # Maybe not highest temp, but avg temp of loop?
T_0 := 440 #465   # T_0 := T_c # 441.37 # 430 # Kelvin # Initial System, start a bit warmer than T_c



p_0 := 1.1e5 # 1.01e5 # try change to 1.5 or 2 # Initial pressure, and ambient
v_0 := 0.02 # 0.0185
h_amb := 1e5  # Arbitrarily large, as specified in paper
p_out := 1.1e5


# Quadrature Settings
p_order_quadPnts :=   1     #  2      #
quad_type :=          TRAP  #  GAUSS  #
quad_order :=         FIRST #  SECOND #
scheme :=  implicit-euler # BDF2 #    # # crank-nicolson #

# Uncomment to run TH-only

# [Executioner]
#   end_time := 0.0
# []
