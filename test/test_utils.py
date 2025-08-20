from fixed_point import *
import math 
from cocotb.triggers import ClockCycles

def angle_to_rad(angle):
    return angle * math.pi / 180.


def is_close_rtol(pred, true, r_tol = 1e-2):
    return abs(pred - true) / true < r_tol

def is_close_atol(pred, true, a_tol = 1e-2):
    return abs(pred - true)  < a_tol


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
        assert is_close_rtol(out1_float, cos_true, r_tol=tol), f"sin({angle}) = {cos_true}, got {out1_float}"
        assert is_close_rtol(out2_float, sin_true, r_tol=tol), f"cos({angle}) = {sin_true}, got {out2_float}"
    elif tol_mode == "abs":
        assert is_close_atol(out1_float, cos_true, a_tol=tol), f"sin({angle}) = {cos_true}, got {out1_float}"
        assert is_close_atol(out2_float, sin_true, a_tol=tol), f"cos({angle}) = {sin_true}, got {out2_float}"
    else:
        raise NotImplementedError(f"Unknown tolerance mode {tol_mode}")        


    dut._log.info(f"Finished CORDIC computation for angle {angle} degrees\n\n")
    return out1, out2