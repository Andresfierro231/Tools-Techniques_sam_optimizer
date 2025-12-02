!include jsalt_base_case.i 

fric_factor := 0.456
T_c := 459.0 # Pin the temperature you want the cooler to cool fluid to #${fparse 168.22 + 273.15} # Use measured temp at TP1  # 168.22 + 273.15 := 441.37
q_net := 230.47 # W # Note, I don't think she is using Q_heater


T_h := 466.0  # Turns out simulation stability is incredibly sensitive to value chosen here, but not numerical result for some strange reason # Maybe not highest temp, but avg temp of loop? 
T_0 := 460.0 # T_0 := 460.0 # 441.37 # 430 # Kelvin # Initial System, start a bit warmer than T_c


p_0 := 1.1e5 # 1.01e5 # try change to 1.5 or 2 # Initial pressure, and ambient
v_0 := 0.02 # 0.0185
h_amb := 200000.0  # Arbitrarily large, as specified in paper


# Quadrature Settings
p_order_quadPnts := 2 # 1
quad_type := GAUSS # TRAP
quad_order := SECOND # FIRST
scheme :=  implicit-euler # BDF2 #    # # crank-nicolson #  
node_multiplier := 6 # min is 6 can go up to 20, 30...
