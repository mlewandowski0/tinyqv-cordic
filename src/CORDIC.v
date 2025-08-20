`include "defines.v"

// Unified microrotation algortihm can be expressed in the following form
// x[j+1] = x[j] - m * \sigma_{j} 2^{-j} y[j]
// y[j+1] = y[j] + \sigma_{j} 2^{-j} x[j]
//
//           { z[j] - sigma_{j} * tan^{-1} (2^{-j})    if m = 1
//  z[j+1] = { z[j] - sigma_{j} * tanh^{-1} (2^{-j})   if m = -1
//           { z[j] - sigma_{j} * tanh



module CORDIC #(
    parameter ITERATIONS = 9,
    parameter FIXED_WIDTH = 16
) (
    input                           clk,
    input                           rst_n,
    input                           start,
    input                           is_rotating,            // 1 = rotate, 0 = vector
    input [1:0]                     mode,                   // `CIRCULAR_MODE`, `LINEAR_MODE`, `HYPERBOLIC_MODE`
    input [$clog2(FIXED_WIDTH)-1:0] alpha_one_left_shift,   // on which bit, the 1.0 is stored 
                                                            // for example for WIDTH=16 and this value set to 10
                                                            // 1.0 = 0000 0100 0000 0000

    input [FIXED_WIDTH-1:0]         A,                      // first input to module
    input [FIXED_WIDTH-1:0]         B,                      // second input to module
    output reg [FIXED_WIDTH-1:0]    out1,                   // first ouput
    output reg [FIXED_WIDTH-1:0]    out2,                   // second output
    output reg done                                         // 1-cycle pulse on finish, pluggable to interrupt ? 
);

    localparam ITERATION_WIDTH = $clog2(ITERATIONS)-1;

    // internal path
    reg signed [FIXED_WIDTH-1:0] x;
    reg signed [FIXED_WIDTH-1:0] y;
    reg signed [FIXED_WIDTH-1:0] z;

    wire signed [FIXED_WIDTH-1:0] next_x;
    wire signed [FIXED_WIDTH-1:0] next_y;
    wire signed [FIXED_WIDTH-1:0] next_z;

    // iteration counter
    reg [ITERATION_WIDTH:0] iteration;

    // shift amount clamped
    wire [ITERATION_WIDTH:0] sh = (iteration > (FIXED_WIDTH-1)) ? (FIXED_WIDTH-1) : iteration;

    // determining the sigma sign
    wire is_sigma_positive = (is_rotating) ? (z >= 0) : (y < 0); // rotate : sign(z); vector : -sign(y)

    wire signed [FIXED_WIDTH-1:0] alpha_one_value = 1 << alpha_one_left_shift;

    // needs updating for smaller iterations
    localparam signed [FIXED_WIDTH-1:0] K_INV_Q = 16'sd9949; // ≈0.607254

    // atan lookup table
    wire signed [FIXED_WIDTH-1:0] delta_theta;
    CORDIC_angles_ROM #(.FIXED_WIDTH(FIXED_WIDTH),
                               .ITERATIONS(ITERATIONS)) angles_rom(.clk(clk),
                                                                   .rst_n(rst_n),
                                                                   .which_angle(sh),
                                                                   .angle_out(delta_theta));


    wire signed [FIXED_WIDTH-1:0] delta_z;
    assign delta_z = (mode == `CIRCULAR_MODE) ? delta_theta : 
                  (mode == `LINEAR_MODE) ? (alpha_one_value >> (iteration-1)) :
                  (mode == `HYPERBOLIC_MODE) ? 1 : 0;

    CORDIC_iteration #(.FIXED_WIDTH(FIXED_WIDTH),
                       .ITERATIONS(ITERATIONS)) iter( .x(x),
                                                      .y(y),
                                                      .z(z),
                                                      .shift(sh-1),
                                                      .delta_z(delta_z),

                                                      .is_sigma_positive(is_sigma_positive),
                                                      .mode(mode),

                                                      .next_x(next_x),
                                                      .next_y(next_y),
                                                      .next_z(next_z));

    // running flag
    reg running;

    // 1-cycle done pulse
    wire last_iter = (iteration == (ITERATIONS-1));

    always @(posedge clk) begin
        if (!rst_n) 
        begin
            running <= 1'b0;
            iteration <= 0;
            x <= '0;
            y <= '0;
            z <= '0;
            out1 <= '0;
            out2 <= '0;
            done <= 1'b0;
        end 
        else 
        begin
            
            // default 
            done <= 1'b0;

            if (start && !running)
            begin 
                running <= 1'b1;
                iteration <= 1;

                // initialize per mode + rotation/vector mode

                case(mode)
                    `CIRCULAR_MODE:
                    begin
                        if (is_rotating)
                        begin
                            // rotate by angle A : output cos/sin in x/y
                            z <= A;
                            x <= K_INV_Q; // 16'b0100_0000_0000_0000; //
                            y <= {FIXED_WIDTH{1'b0}};
                        end
                        else 
                        begin
                            // vectoring mode : input A,B output = K * sqrt(A^2 + B^2), z=atan(B/A)
                            x <= $signed(A);
                            y <= $signed(B);
                            z <= 0;
                        end
                    end
                    `LINEAR_MODE:
                    begin
                        
                        if (is_rotating)
                        begin
                            // multiplication : input A, B, output  ~ A * B (output 2 stores something like and error, kind of)
                            x <= $signed(A);
                            y <= 0;
                            z <= $signed(B);
                        end
                        else 
                        begin
                            // division : input A, B, output  ~ A / B (output 2 stores something like and error, kind of)
                            x <= $signed(A);
                            y <= $signed(B);
                            z <= 0;
                        end
                    end
                    `HYPERBOLIC_MODE:
                    begin
                    end

                    default:
                    begin
                        x <= 0;
                        y <= 0;
                        z <= 0;
                    end
                endcase
            end
            else if (running)
            begin
                // perform iteration
                x <= next_x;
                y <= next_y;
                z <= next_z;

            if (last_iter) 
            begin
                    running <= 1'b0;
                    done    <= 1'b1;
                    iteration <= 0;
                    case (mode)
                        `CIRCULAR_MODE: begin
                            if (is_rotating) begin
                                out1 <= x; // cos
                                out2 <= y; // sin
                            end else begin
                                out1 <= x; // r ≈ K*sqrt(A^2+B^2)
                                out2 <= z; // atan2(B,A)
                            end
                        end
                        `LINEAR_MODE: begin
                            if (is_rotating)
                            begin
                                out1 <= y;  // A * B 
                                out2 <= z;  // ~ error
                            end
                            else 
                            begin
                                out1 <= z;  // B / A
                                out2 <= y;  // ~ error
                            end
                        end
                        default: begin
                            out1 <= '0; out2 <= '0;
                        end
                    endcase
                end 
                else 
                begin
                    iteration <= iteration + 1'b1;
                end
            end
        end
    end


endmodule