`include "bsg_defines.v"

module bsg_inv #(parameter width_p="inv"
                 , harden_p=1
                 , strength_p=1
                 , clock_p=0
                 , vertical_p=1)
   (input [width_p-1:0] i
    , output [width_p-1:0] o
    );

   assign o = ~i;

endmodule
