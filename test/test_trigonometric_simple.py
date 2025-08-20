# SPDX-FileCopyrightText: © 2025 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

from tqv import TinyQV
from fixed_point import *
import math 

def angle_to_rad(angle):
    return angle * math.pi / 180.


def is_close(pred, true, r_tol = 1e-2):
    return abs(pred - true) / true < r_tol

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

async def test_sin_cos(dut, tqv, angle, r_tol=0.01):
    
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
    assert is_close(out1_float, cos_true, r_tol=r_tol), f"sin({angle}) = {cos_true}, got {out1_float}"
    assert is_close(out2_float, sin_true, r_tol=r_tol), f"cos({angle}) = {sin_true}, got {out2_float}"

    dut._log.info(f"Finished CORDIC computation for angle {angle} degrees\n\n")
    return out1, out2

    


@cocotb.test()
async def test_trigonometric_basic(dut):
    dut._log.info("Start")

    # Set the clock period to 100 ns (10 MHz)
    clock = Clock(dut.clk, 100, units="ns")
    cocotb.start_soon(clock.start())

    # Interact with your design's registers through this TinyQV class.
    # This will allow the same test to be run when your design is integrated
    # with TinyQV - the implementation of this class will be replaces with a
    # different version that uses Risc-V instructions instead of the SPI test
    # harness interface to read and write the registers.
    tqv = TinyQV(dut, PERIPHERAL_NUM)

    # Reset
    await tqv.reset()

    dut._log.info("Test project behavior")

    # Test register write and read back
    value = await tqv.read_word_reg(0) 

    # read the identificator
    assert value == 0xbadcaffe, "when reading from reg 0, we should see magic string '0xbadcaffe'"

    # Check the status register : we don't yet run anything, it should be 0
    assert await tqv.read_byte_reg(6) == 0, "status register should be 0 (READY TO BE RUN)"
 
    # outputs should be zeroed out 
    assert await tqv.read_hword_reg(4) == 0, "output 1 should be zeroed out"
    assert await tqv.read_hword_reg(5) == 0, "output 2 should be zeroed out"

    # first test : compute the sin(30 degrees) and cos(30 degrees)

    # the input to circular mode in rotating, is only angle, stored as radians, fixed point 
    # arithmetic in signed 1.14 bits format ( for FIXED WIDTH = 16, in general case, in signed 1.{FIXED_WIDTH-2} format )
    # 30 degrees = pi / 6 = 0.52359877 \approx (in fixed point) b00100001_10000011
    await test_sin_cos(dut, tqv, angle=30)

    await test_sin_cos(dut, tqv, angle=45)
    await test_sin_cos(dut, tqv, angle=60)
    
    # 75 degrees and 15 degrees is different by 1 percent
    await test_sin_cos(dut, tqv, angle=75, r_tol=0.025)
    await test_sin_cos(dut, tqv, angle=15, r_tol=0.025)

    # test the negatives
    await test_sin_cos(dut, tqv, angle=-15, r_tol=0.025)
    await test_sin_cos(dut, tqv, angle=-30, r_tol=0.025)
    await test_sin_cos(dut, tqv, angle=-45, r_tol=0.025)
    await test_sin_cos(dut, tqv, angle=-60, r_tol=0.025)
    await test_sin_cos(dut, tqv, angle=-75, r_tol=0.025)

    # The following assersion is just an example of how to check the output values.
    # Change it to match the actual expected output of your module:
    # assert dut.uo_out.value == 0x96

    # Input value should be read back from register 1
    #assert await tqv.read_byte_reg(4) == 30

    # Zero should be read back from register 2
    #assert await tqv.read_word_reg(8) == 0

    # A second write should work
    #await tqv.write_word_reg(0, 40)
    #assert dut.uo_out.value == 70

    # Test the interrupt, generated when ui_in[6] goes high
    #dut.ui_in[6].value = 1
    #3await ClockCycles(dut.clk, 1)
    #dut.ui_in[6].value = 0

    # Interrupt asserted
    #await ClockCycles(dut.clk, 3)
    #assert await tqv.is_interrupt_asserted()

    # Interrupt doesn't clear
    #await ClockCycles(dut.clk, 10)
    #assert await tqv.is_interrupt_asserted()
    
    # Write bottom bit of address 8 high to clear
    #await tqv.write_byte_reg(8, 1)
    #assert not await tqv.is_interrupt_asserted()
