# SPDX-FileCopyrightText: © 2025 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

from tqv import TinyQV
from fixed_point import *
import math 
from test_utils import use_multiplication_mode, use_division_mode

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
 
    # outputs should be zeroed out 
    assert await tqv.read_hword_reg(4) == 0, "output 1 should be zeroed out"
    assert await tqv.read_hword_reg(5) == 0, "output 2 should be zeroed out"

    A = 0b0000011000000000  # A is 0.75 
    B = 0b0000100000000000  # B is 2.0
    alpha_one_position = 11 
    await use_multiplication_mode(dut, tqv, A, B, alpha_one_position, tol_mode="rel", tol=0.01)


    A = 0b0000101000000000 # A is 1.25
    B = 0b0000101000000000 #   B is 2.5
    alpha_one_position = 11 
    await use_multiplication_mode(dut, tqv, A, B, alpha_one_position, tol_mode="rel", tol=0.01)


    A = 0b0000100011001101 # A is 1.100098
    B = 0b0000001010111010 #   B is 0.340820
    alpha_one_position = 11 
    await use_multiplication_mode(dut, tqv, A, B, alpha_one_position, tol_mode="rel", tol=0.01)


    A = 0b0010000000000000 #   A is 4.000000
    B = 0b0000100000000000 #   B is 4.000000
    alpha_one_position = 11 
    await use_multiplication_mode(dut, tqv, A, B, alpha_one_position, tol_mode="rel", tol=0.01)


    A = 0b0000000100000000 #   A is 0.125000
    B = 0b0000010000011001 #   B is 0.512207
    alpha_one_position = 11 
    await use_multiplication_mode(dut, tqv, A, B, alpha_one_position, tol_mode="rel", tol=0.01)
    
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

    A = 0b0000010011001101  # A is 0.6
    B = 0b0000011000000000  # B is 1.5
    alpha_one_position = 11 
    await use_division_mode(dut, tqv, A, B, alpha_one_position, tol_mode="rel", tol=0.01)

    A = 0b0000010011001101  # A is 0.600000
    B = 0b0000100000000000  # B is 2.000000
    alpha_one_position = 11 
    await use_division_mode(dut, tqv, A, B, alpha_one_position, tol_mode="rel", tol=0.01)


    A = 0b0011001001100110  # A is 6.299805
    B = 0b0100100011110110  # B is 9.120117
    alpha_one_position = 11 
    await use_division_mode(dut, tqv, A, B, alpha_one_position, tol_mode="rel", tol=0.01)


    A = 0b0100000000000000  # A is 8.000000
    B = 0b0101100111000011  # B is 11.220215 
    alpha_one_position = 11 
    await use_division_mode(dut, tqv, A, B, alpha_one_position, tol_mode="rel", tol=0.01)