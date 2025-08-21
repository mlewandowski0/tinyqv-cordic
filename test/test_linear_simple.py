# SPDX-FileCopyrightText: © 2025 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

from tqv import TinyQV
from fixed_point import *
import math 
from test_utils import use_multiplication_mode_input_float, use_division_mode_float_input

# When submitting your design, change this to the peripheral number
# in peripherals.v.  e.g. if your design is i_user_peri05, set this to 5.
# The peripheral number is not used by the test harness.
PERIPHERAL_NUM = 0

@cocotb.test()
async def test_multiplication(dut):
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
 
    width = 16
    XY_INT = 5
    Z_INT  = 5
    alpha_one_position = 11

    # alpha posiition is 11, therefore
    #  A = 5b.11b
    a = 0.75
    b = 2.0
    await use_multiplication_mode_input_float(dut, tqv, a, b, alpha_one_position, 
                                              tol_mode="rel", tol=0.01, width=width, XY_INT=XY_INT, Z_INT=Z_INT)

    
    # alpha posiition is 11, therefore
    #  A = 5b.11b
    a = 1.25
    b = 2.5
    await use_multiplication_mode_input_float(dut, tqv, a, b, alpha_one_position, 
                                              tol_mode="rel", tol=0.01, width=width, XY_INT=XY_INT, Z_INT=Z_INT)


    # alpha posiition is 11, therefore
    #  A = 5b.11b
    a = 1.1
    b = 0.341
    A = float_to_fixed(a, width=width, integer_part=XY_INT)   
    B = float_to_fixed(b, width=width, integer_part=XY_INT) 
    alpha_one_position = 11 
    await use_multiplication_mode_input_float(dut, tqv, a, b, alpha_one_position, 
                                              tol_mode="rel", tol=0.01, width=width, XY_INT=XY_INT, Z_INT=Z_INT)

    # alpha posiition is 11, therefore
    #  A = 5b.11b
    a = 4.0
    b = 4.0
    A = float_to_fixed(a, width=width, integer_part=XY_INT)   
    B = float_to_fixed(b, width=width, integer_part=XY_INT) 
    alpha_one_position = 11 
    await use_multiplication_mode_input_float(dut, tqv, a, b, alpha_one_position, 
                                              tol_mode="rel", tol=0.01, width=width, XY_INT=XY_INT, Z_INT=Z_INT)


    # alpha posiition is 11, therefore
    #  A = 5b.11b
    a = 0.125
    b = 0.512
    A = float_to_fixed(a, width=width, integer_part=XY_INT)   
    B = float_to_fixed(b, width=width, integer_part=XY_INT) 
    alpha_one_position = 11 
    await use_multiplication_mode_input_float(dut, tqv, a, b, alpha_one_position, 
                                              tol_mode="rel", tol=0.01, width=width, XY_INT=XY_INT, Z_INT=Z_INT)


    
    # the input to circular mode in rotating, is only angle, stored as radians, fixed point 
    # arithmetic in signed 1.14 bits format ( for FIXED WIDTH = 16, in general case, in signed 1.{FIXED_WIDTH-2} format )
    


@cocotb.test()
async def test_division(dut):
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

    width = 16
    XY_INT = 5
    Z_INT  = 5

    # Reset
    await tqv.reset()

    dut._log.info("Test project behavior")

    # Test register write and read back
    value = await tqv.read_word_reg(0) 

    # read the identificator
    assert value == 0xbadcaffe, "when reading from reg 0, we should see magic string '0xbadcaffe'"

    # Check the status register : we don't yet run anything, it should be 0
    assert await tqv.read_byte_reg(6) == 0, "status register should be 0 (READY TO BE RUN)"
 
 
    alpha_one_position = 11
    # computing 1.5 / 0.6
    a = 0.6
    b = 1.5
    out1, out2 = await use_division_mode_float_input(dut, tqv, a, b, alpha_one_position, tol_mode="rel", tol=0.01)


    # computing 2.0 / 0.6
    a = 0.6
    b = 2.0
    out1, out2 = await use_division_mode_float_input(dut, tqv, a, b, alpha_one_position, tol_mode="rel", tol=0.01)

    # computing 9.12 / 6.3
    a = 6.3
    b = 9.12
    out1, out2 = await use_division_mode_float_input(dut, tqv, a, b, alpha_one_position, tol_mode="rel", tol=0.01)

    # computing 2.0 / 0.6
    a = 8.12
    b = 11.22
    out1, out2 = await use_division_mode_float_input(dut, tqv, a, b, alpha_one_position, tol_mode="rel", tol=0.01)
