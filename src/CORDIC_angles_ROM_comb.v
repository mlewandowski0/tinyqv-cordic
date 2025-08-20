module CORDIC_angles_ROM  #(parameter FIXED_WIDTH = 16,
                          parameter ITERATIONS = 9)
                          (input wire [$clog2(ITERATIONS)-1:0] which_angle,
                           output reg signed [FIXED_WIDTH-1:0]  angle_out);

    // index width
    localparam IDX_W = $clog2(ITERATIONS)-1;

    // clamp index to [0, ITERATIONS - 1]
    localparam [IDX_W:0] MAXI = (ITERATIONS-1);
    wire [IDX_W:0] idx_clamp = (which_angle > MAXI) ? MAXI : which_angle;


    // synthesis safe LUT (fixed float 2.14 radiants). needs update for changes  
    always @(*)
    begin 
            case(idx_clamp)
                0: angle_out        = 16'b0011001001000100; // atan(2^0)
                1: angle_out        = 16'b0001110110101100; // atan(2^-1)
                2: angle_out        = 16'b0000111110101110; // atan(2^-2)
                3: angle_out        = 16'b0000011111110101; // atan(2^-3)
                4: angle_out        = 16'b0000001111111111; // atan(2^-4)
                5: angle_out        = 16'b0000001000000000; // atan(2^-5)
                6: angle_out        = 16'b0000000100000000; // atan(2^-6)
                7: angle_out        = 16'b0000000010000000; // atan(2^-7)
                default: angle_out  = 16'b0000000001000000; // atan(2^-8)\

                // for more terms, see the python files and CORDIC_angles.mem
            endcase
    end



endmodule