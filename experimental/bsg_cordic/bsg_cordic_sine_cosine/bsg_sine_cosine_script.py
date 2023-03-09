import math, sys

def lookup_compute(posprec, precision_result):
    lookup=[]
    for j in range(0,posprec+1):
        m=(math.atan2(1,2**j)*180)/math.pi
        lookup.append(format(round(m*(2**precision_result)),'x'))
    return lookup

def constant_compute(posprec, ansbitlen):
    const=1
    for i in range(0,posprec):
        comp = math.cos(math.atan2(1,2**i))
        const=const*comp
    const = format(round(const*(2**(ansbitlen-1))),'x')
    return const

def bsg_sine_cosine_init(angbitlen, ansbitlen, posprec):
    print('''
    module bsg_cordic_sine_cosine #(precis_p = %(p)d, ang_width_p = %(g)d, ans_width_p = %(s)d)
    (
    input clk_i
    ,input signed [ang_width_p-1:0] ang_i
    ,input ready_i
    ,input val_i
    ,output signed [ans_width_p-1:0] sin_o
    ,output signed [ans_width_p-1:0] cos_o
    ,output ready_o
    ,output val_o
    );
    logic val_in ;
    logic signed [precis_p+1:0][ans_width_p-1:0] x ;
    logic signed [precis_p+1:0][ans_width_p-1:0] y ;
    logic signed [precis_p+1:0][ang_width_p-1:0] ang ;
    logic [precis_p+1:0] val ;
    logic sign_cos [precis_p+1:0];
    logic sign_sin [precis_p+1:0];
    logic signed [precis_p:0][ans_width_p-1:0] x_ans ;
    logic signed [precis_p:0][ans_width_p-1:0] y_ans ;
    logic signed [precis_p:0][ang_width_p-1:0] ang_ans ;
    logic [precis_p:0] val_ans ;
    logic sign_cos_ans [precis_p:0];
    logic sign_sin_ans [precis_p:0];
    logic signed [ang_width_p-1:0] quant_i;
    logic sign_op_sin;
    logic sign_op_cos;
    wire stall_pipe = val_o & (~ready_i);
    
    ''' %{'s':ansbitlen, 'g':angbitlen, 'p':posprec})
    return
def quadrant_print(angbitlen,constant):
    print(''' 
    always_ff @(posedge clk_i)
    begin
    if(~stall_pipe) begin
    val_in <= val_i;
    case(ang_i[ang_width_p-1])

        1'b0: begin
            if((ang_i[(ang_width_p-2)-:8] > 8'h5A) && (ang_i[(ang_width_p-2)-:8] < 8'hB4)==1) begin
                quant_i <= %(g)d'h0%(c)s - ang_i;
                sign_op_cos <= 1'b1;
                sign_op_sin <= 1'b0;
            end
            else begin
                quant_i <= ang_i;
                sign_op_cos <= 1'b0;
                sign_op_sin <= 1'b0;
            end
        end
        1'b1:begin
            if((ang_i[(ang_width_p-2)-:8] > 8'h4C) && (ang_i[(ang_width_p-2)-:8] < 8'hA6)==1) begin
                quant_i <= %(g)d'h0%(c)s + ang_i;
                sign_op_cos <= 1'b1;
                sign_op_sin <= 1'b1;
            end
            else begin
                quant_i <=  ~ang_i + 1;
                sign_op_cos <= 1'b0;
                sign_op_sin <= 1'b1;
        end
    end
    endcase
    end
    end
    
    '''%{'g':angbitlen, 'c':constant})
    return

def constant_180(precision):
    const = '010110100'
    for i in range(0,precision):
        const = const + '0'
    return (format(int(const, 2),'x'))
    
def lookup_initialization(posprec, angbitlen, result):
    print("    localparam [precis_p:0][ang_width_p-1:0] ang_lookup_lp={" )
    for i in range(posprec,0,-1):
        print("     %(g)d'h%(r)s," %{'g':angbitlen,'r':result[i] })
    print("     %(g)d'h%(r)s };" %{'g':angbitlen,'r':result[0] })
    return

def bsg_constxy_initialization(constant, ansbitlen):
    print("""    
    localparam x_start = %(s)d'h%(c)s;
    localparam y_start = %(s)d'h0;               
    """ %{'s':ansbitlen, 'c':constant})
    return

def main_body_print():
    print('''
    always_ff @(posedge clk_i) begin
    if(~stall_pipe) begin
          x[0] <= x_start;
          y[0] <= y_start;
          ang[0] <= quant_i;
          sign_cos[0] <= sign_op_cos;
          sign_sin[0] <= sign_op_sin;
          val[0] <= val_in;
       end
    end 
    genvar i;
    generate
        for(i = 0; i <= precis_p ; i = i+1)
            begin : stage
                bsg_cordic_sine_cosine_stage #(.stage_p(i), .ang_width_p(ang_width_p), .ans_width_p(ans_width_p)) cs
                       (.x_i(x[i])
                        ,.y_i(y[i])
                        ,.ang_i(ang[i])
                        ,.ang_lookup_i(ang_lookup_lp[i])
                        ,.val_i(val[i])
                        ,.sign_op_cos_i(sign_cos[i])
                        ,.sign_op_sin_i(sign_sin[i])
                        ,.x_o(x_ans[i])
                        ,.y_o(y_ans[i])
                        ,.ang_o(ang_ans[i])
                        ,.val_o(val_ans[i])
                        ,.sign_op_cos_o(sign_cos_ans[i])
                        ,.sign_op_sin_o(sign_sin_ans[i])
                        );
          
                    always_ff @(posedge clk_i)
                      begin
                        if(~stall_pipe) begin
                         x[i+1] <= x_ans[i];
                         y[i+1] <= y_ans[i];
                         ang[i+1] <= ang_ans[i];
                         sign_cos[i+1] <= sign_cos_ans[i];
                         sign_sin[i+1] <= sign_sin_ans[i];
                         val[i+1] <= val_ans[i];
                      end
                    end
                    end
          
            endgenerate
            assign val_o = val[precis_p+1];
            assign cos_o = sign_cos[precis_p+1] ? ~x[precis_p+1] + 1 : x[precis_p+1];
            assign sin_o = sign_sin[precis_p+1] ? ~y[precis_p+1] + 1 : y[precis_p+1];
            assign ready_o = ~stall_pipe;
endmodule
''')
    return

def signed_constant(ansbitlen):
    const = "1"
    for i in range(0,ansbitlen-1):
        const = const + str(0)
    return (hex(int(const, 2)))

def signed_constant2(ansbitlen):
    const = ""
    for i in range(0,ansbitlen):
        const = const + str(1)
    return (hex(int(const, 2)))


angbitlen = (int)(sys.argv[1])
#^^ Advised to use 1-sign bit+8-bits for reperenting a max of 180 degrees+precision number of bits.
ansbitlen = (int)(sys.argv[2])
#^^Output in fixed point format with (anslen-1) number of bits for decimal representation.
posprec = (int)(sys.argv[3])
precision = (int)(sys.argv[4])
startquant_pow = (int)(sys.argv[5])
# ^^Input to the module will start from 2^startquant_pow. Fixed-point value will be 2^(startquant_pow-precision)
# A general recommendation is that if Sin TEST FAILS, try increasing startquant_pow.

lookup = lookup_compute(posprec, precision)
bsg_sine_cosine_init(angbitlen, ansbitlen, posprec)
lookup_initialization(posprec, angbitlen, lookup)
constant = constant_compute(posprec, ansbitlen)
bsg_constxy_initialization(constant, ansbitlen)
const_sign = constant_180(precision)
quadrant_print(angbitlen,const_sign)
main_body_print()
signedconst = signed_constant(ansbitlen)
signedconst2 = signed_constant2(ansbitlen)

# This file object is used to create a header file facilitating the passing of parameters of the module to
# Verilator for testing purposes. 
f_params = open("params_def.h","w+")
f_params.write('#ifndef PARAMS_DEF\n')
f_params.write('#define PARAMS_DEF\n')
f_params.write('int anglen = %(g)d;\n'%{'g':angbitlen})
f_params.write('int anslen = %(s)d;\n'%{'s':ansbitlen})
f_params.write('int startquant_pow = %(s)d;\n'%{'s':startquant_pow})
f_params.write('int precis_p = %(p)d;\n'%{'p':posprec})
f_params.write('int precision = %(p)d;\n'%{'p':precision})
f_params.write('long int signedconst = %(sc)s;\n'%{'sc':signedconst})
f_params.write('long int signedconst2 = %(scc)s;\n'%{'scc':signedconst2})
f_params.write('#endif')
f_params.close()
