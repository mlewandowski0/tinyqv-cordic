from fixed_point import *
import math 
from cocotb.triggers import ClockCycles

def angle_to_rad(angle):
    return angle * math.pi / 180.


def is_close_rtol(pred, true, r_tol = 1e-2):
    return abs(pred - true) / true < r_tol

def is_close_atol(pred, true, a_tol = 1e-2):
    return abs(pred - true)  < a_tol

def format_to_fixed_width(value, width):
    return format(value, f'0{width}b')


# BITS for mode
MODE_BITS           = 1
CIRCULAR_MODE       = 0
LINEAR_MODE         = 1
HYPERBOLIC_MODE     = 2

# 
IS_ROTATING_BIT     = 3 

# When submitting your design, change this to the peripheral number
# in peripherals.v.  e.g. if your design is i_user_peri05, set this to 5.
# The peripheral number is not used by the test harness.
PERIPHERAL_NUM = 0

async def test_sin_cos(dut, tqv, angle, tol_mode="rel", tol=0.01):
    
    angle_rad = angle_to_rad(angle)
    angle_fixed_point = float_to_fixed(angle_rad, 16, 2)  # 16 bits, 2 integer bits
    dut._log.info(f"angle of {angle} degrees (in rad = {angle_rad:.4f}), is angle_fixed_point = {angle_fixed_point:0{16}b}")
    await tqv.write_word_reg(1, angle_fixed_point)

    # configure the cordic : set the mode to ROTATING, CIRCULAR, and running
    # this corresponds to setting it to       {1'b1,,  2'b00,         1'b1 }
    
    config_to_write = (CIRCULAR_MODE << MODE_BITS) | (1 << IS_ROTATING_BIT) | 1     
    dut._log.info(f"Configuring CORDIC with {config_to_write:#04x} ({bin(config_to_write)}) (mode={CIRCULAR_MODE}, is_rotating=1, start=1)")
    await tqv.write_byte_reg(0, config_to_write)
   
    # check if the device is busy
    await ClockCycles(dut.clk, 1)
    #assert await tqv.read_byte_reg(6) == 1, "status register should be 1 (BUSY)"

    await ClockCycles(dut.clk, 11)
    #assert await tqv.read_byte_reg(6) == 2, "status register should be 2 (DONE)"

    out1 = await tqv.read_hword_reg(4)
    out2 = await tqv.read_hword_reg(5)
    
    # because we read unsigned 16bit half word, we need to conver it to signed representation
    if out1 & (1<<15):
        out1 = out1 - 2**16
    
    if out2 & (1<<15):
        out2 = out2 - 2**16

    
    # conver to floating point for easier comparison
    out1_float = fixed_to_float(out1, 16, 2)
    out2_float = fixed_to_float(out2, 16, 2)
    sin_true = math.sin(angle_rad)
    cos_true = math.cos(angle_rad)

    dut._log.info(f"out1 = {out1_float:.4f} (true = {cos_true:.4f}), out2 = {out2_float:.4f} (true = {sin_true:.4f})")
    dut._log.info(f"out1/out2 = {out1_float/out2_float}")
    
    if tol_mode == "rel":
        assert is_close_rtol(out1_float, cos_true, r_tol=tol), f"sin({angle}) = {sin_true}, got {out1_float}"
        assert is_close_rtol(out2_float, sin_true, r_tol=tol), f"cos({angle}) = {cos_true}, got {out2_float}"
    elif tol_mode == "abs":
        assert is_close_atol(out1_float, cos_true, a_tol=tol), f"sin({angle}) = {sin_true}, got {out1_float}"
        assert is_close_atol(out2_float, sin_true, a_tol=tol), f"cos({angle}) = {cos_true}, got {out2_float}"
    else:
        raise NotImplementedError(f"Unknown tolerance mode {tol_mode}")        


    dut._log.info(f"Finished CORDIC computation for circular and rotating, angle {angle} degrees\n\n")
    return out1, out2

async def test_sinh_cosh(dut, tqv, x, tol_mode="rel", tol=0.01):

    angle_fixed_point = float_to_fixed(x, 16, 2)  # 16 bits, 2 integer bits

    await tqv.write_word_reg(1, angle_fixed_point)

    # configure the cordic : set the mode to ROTATING, hyperbolic, and running
    # this corresponds to setting it to       {1'b1,  2'b10,         1'b1 }
    
    config_to_write = (HYPERBOLIC_MODE << MODE_BITS) | (1 << IS_ROTATING_BIT) | 1     
    dut._log.info(f"Configuring CORDIC with {config_to_write:#04x} ({bin(config_to_write)}) (mode={CIRCULAR_MODE}, is_rotating=1, start=1)")
    await tqv.write_byte_reg(0, config_to_write)
   
    # check if the device is busy
    await ClockCycles(dut.clk, 1)
    #assert await tqv.read_byte_reg(6) == 1, "status register should be 1 (BUSY)"

    await ClockCycles(dut.clk, 11)
    #assert await tqv.read_byte_reg(6) == 2, "status register should be 2 (DONE)"

    out1 = await tqv.read_hword_reg(4)
    out2 = await tqv.read_hword_reg(5)
    
    # because we read unsigned 16bit half word, we need to conver it to signed representation
    if out1 & (1<<15):
        out1 = out1 - 2**16
    
    if out2 & (1<<15):
        out2 = out2 - 2**16

    # conver to floating point for easier comparison
    out1_float = fixed_to_float(out1, 16, 2)
    out2_float = fixed_to_float(out2, 16, 2)
    sinh_true = math.sinh(x)
    cosh_true = math.cosh(x)

    dut._log.info(f"out1 = {out1_float:.4f} (true = {cosh_true:.4f}), out2 = {out2_float:.4f} (true = {sinh_true:.4f})")

    if tol_mode == "rel":
        assert is_close_rtol(out1_float, cosh_true, r_tol=tol), f"cosh({x}) = {cosh_true}, got {out1_float}"
        assert is_close_rtol(out2_float, sinh_true, r_tol=tol), f"sinh({x}) = {sinh_true}, got {out2_float}"
    elif tol_mode == "abs":
        assert is_close_atol(out1_float, cosh_true, a_tol=tol), f"cosh({x}) = {cosh_true}, got {out1_float}"
        assert is_close_atol(out2_float, sinh_true, a_tol=tol), f"sinh({x}) = {sinh_true}, got {out2_float}"
    else:
        raise NotImplementedError(f"Unknown tolerance mode {tol_mode}")        

    dut._log.info(f"Finished CORDIC computation for hyperbolic and rotating, input x={x}\n\n")
    return out1, out2

async def use_multiplication_mode_input_float(dut, tqv, a, b, alpha_one_position, 
                                              width=16, XY_INT=5, Z_INT=5, tol_mode="rel", tol=0.01):
    
    A = float_to_fixed(a, width=width, integer_part=XY_INT)   
    B = float_to_fixed(b, width=width, integer_part=Z_INT) 

    await tqv.write_word_reg(1, A)
    await tqv.write_word_reg(2, B)
    await tqv.write_byte_reg(3, alpha_one_position)

    # configure the cordic : set the mode to ROTATING, LINEAR, and running
    # this corresponds to setting it to       {1'b1,,  2'b00,         1'b1 }
    
    config_to_write = (LINEAR_MODE << MODE_BITS) | (1 << IS_ROTATING_BIT) | 1     
    dut._log.info(f"Configuring CORDIC with {config_to_write:#04x} ({bin(config_to_write)}) (mode={CIRCULAR_MODE}, is_rotating=1, start=1)")
    dut._log.info(f"input to module is A={A}(float={a}, fixed={float_to_fixed(A, width, XY_INT)}), B={B}(float={b}, fixed={float_to_fixed(B, width, Z_INT)})")
    await tqv.write_byte_reg(0, config_to_write)
   
    # check if the device is busy
    await ClockCycles(dut.clk, 1)
    #assert await tqv.read_byte_reg(6) == 1, "status register should be 1 (BUSY)"

    await ClockCycles(dut.clk, 11)
    #assert await tqv.read_byte_reg(6) == 2, "status register should be 2 (DONE)"

    out1 = await tqv.read_hword_reg(4)
    out2 = await tqv.read_hword_reg(5)
    
    
    # because we read unsigned 16bit half word, we need to conver it to signed representation
    if out1 & (1<<15):
        out1 = out1 - 2**16
    
    if out2 & (1<<15):
        out2 = out2 - 2**16

    dut._log.info(f"bin(out1) = {out1:0{16}b}, bin(out2) = {out2:0{16}b}")
    dut._log.info(f"out1 = {out1}, out2 = {out2}")
    dut._log.info(f"fixed_to_float(out1) = {fixed_to_float(out1, width, XY_INT)}, fixed_to_float(out2) = {fixed_to_float(out2, width, Z_INT)}")
    dut._log.info(f"true value = {a * b} (float)")
    dut._log.info(f"\n")

    return out1, out2

async def use_division_mode_float_input(dut, tqv, a, b, alpha_one_position, tol_mode="rel", tol=0.01,
                            width=16, XY_INT=5, Z_INT=5):

    A = float_to_fixed(a, width=width, integer_part=XY_INT)
    B = float_to_fixed(b, width=width, integer_part=XY_INT)

    await tqv.write_word_reg(1, A)
    await tqv.write_word_reg(2, B)
    await tqv.write_byte_reg(3, alpha_one_position)

    # configure the cordic : set the mode to ROTATING, LINEAR, and running
    # this corresponds to setting it to       {1'b0,,  2'b00,         1'b1 }
    
    config_to_write = (LINEAR_MODE << MODE_BITS) |  1     
    dut._log.info(f"Configuring CORDIC with {config_to_write:#04x} ({bin(config_to_write)}) (mode={CIRCULAR_MODE}, is_rotating=0, start=1)")
    dut._log.info(f"input to module is A={A}(float={a}, fixed={float_to_fixed(A, width, XY_INT)}), B={B}(float={b}, fixed={float_to_fixed(B, width, Z_INT)})")
    await tqv.write_byte_reg(0, config_to_write)
   
    # check if the device is busy
    await ClockCycles(dut.clk, 1)
    #assert await tqv.read_byte_reg(6) == 1, "status register should be 1 (BUSY)"

    await ClockCycles(dut.clk, 11)
    #assert await tqv.read_byte_reg(6) == 2, "status register should be 2 (DONE)"

    out1 = await tqv.read_hword_reg(4)
    out2 = await tqv.read_hword_reg(5)
    
    
    # because we read unsigned 16bit half word, we need to conver it to signed representation
    if out1 & (1<<15):
        out1 = out1 - 2**16
    
    if out2 & (1<<15):
        out2 = out2 - 2**16

    dut._log.info(f"out1 = {out1:0{16}b}, out2 = {out2:0{16}b}")
    dut._log.info(f"out1 = {out1}, out2 = {out2}")
    dut._log.info(f"fixed_to_float(out1) = {fixed_to_float(out1, width, XY_INT)}, fixed_to_float(out2) = {fixed_to_float(out2, width, Z_INT)}")
    dut._log.info(f"true value = {b / a} (float)")
    dut._log.info(f"\n")

    return out1, out2

async def test_vectoring_hyperbolic(dut, tqv, x, y, tol_mode="rel", tol=0.01,
                                    integer_bits=5):

    x_float = float_to_fixed(x, 16, integer_bits)  # 16 bits, 5 integer bits
    y_float = float_to_fixed(y, 16, integer_bits)  # 16 bits, 5 integer bits

    await tqv.write_word_reg(1, x_float)
    await tqv.write_word_reg(2, y_float)

    # configure the cordic : set the mode to Vectoring, Hyperbolic, and running
    # this corresponds to setting it to       {1'b0,  2'b10,         1'b1 }
    
    config_to_write = (HYPERBOLIC_MODE << MODE_BITS) | 1     
    dut._log.info(f"Configuring CORDIC with {config_to_write:#04x} ({bin(config_to_write)}) (mode={CIRCULAR_MODE}, is_rotating=0, start=1)")
    await tqv.write_byte_reg(0, config_to_write)
   
    # check if the device is busy
    await ClockCycles(dut.clk, 1)
    #assert await tqv.read_byte_reg(6) == 1, "status register should be 1 (BUSY)"

    await ClockCycles(dut.clk, 11)
    #assert await tqv.read_byte_reg(6) == 2, "status register should be 2 (DONE)"

    out1 = await tqv.read_hword_reg(4)
    out2 = await tqv.read_hword_reg(5)
    
    # because we read unsigned 16bit half word, we need to conver it to signed representation
    if out1 & (1<<15):
        out1 = out1 - 2**16
    
    if out2 & (1<<15):
        out2 = out2 - 2**16

    # conver to floating point for easier comparison
    out1_float = fixed_to_float(out1, 16, integer_bits)
    out2_float = fixed_to_float(out2, 16, integer_bits)
    """
    sinh_true = math.sinh(x)
    cosh_true = math.cosh(x)

    dut._log.info(f"out1 = {out1_float:.4f} (true = {cosh_true:.4f}), out2 = {out2_float:.4f} (true = {sinh_true:.4f})")

    if tol_mode == "rel":
        assert is_close_rtol(out1_float, cosh_true, r_tol=tol), f"cosh({x}) = {cosh_true}, got {out1_float}"
        assert is_close_rtol(out2_float, sinh_true, r_tol=tol), f"sinh({x}) = {sinh_true}, got {out2_float}"
    elif tol_mode == "abs":
        assert is_close_atol(out1_float, cosh_true, a_tol=tol), f"cosh({x}) = {cosh_true}, got {out1_float}"
        assert is_close_atol(out2_float, sinh_true, a_tol=tol), f"sinh({x}) = {sinh_true}, got {out2_float}"
    else:
        raise NotImplementedError(f"Unknown tolerance mode {tol_mode}")        

    dut._log.info(f"Finished CORDIC computation for hyperbolic and rotating, input x={x}\n\n")
    """
    return out1, out1_float, out2, out2_float