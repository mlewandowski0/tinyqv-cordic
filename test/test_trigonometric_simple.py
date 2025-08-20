# SPDX-FileCopyrightText: © 2025 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

from tqv import TinyQV
from fixed_point import *
import math 
from test_utils import test_sin_cos

# When submitting your design, change this to the peripheral number
# in peripherals.v.  e.g. if your design is i_user_peri05, set this to 5.
# The peripheral number is not used by the test harness.
PERIPHERAL_NUM = 0

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
    await test_sin_cos(dut, tqv, angle=30, tol_mode="rel",)

    await test_sin_cos(dut, tqv, angle=45, tol_mode="rel",)
    await test_sin_cos(dut, tqv, angle=60, tol_mode="rel",)
    
    # 75 degrees and 15 degrees is different by 1 percent
    await test_sin_cos(dut, tqv, angle=75, tol_mode="rel", tol=0.025)
    await test_sin_cos(dut, tqv, angle=15, tol_mode="rel", tol=0.025)

    # test the negatives
    await test_sin_cos(dut, tqv, angle=-15, tol_mode="rel", tol=0.025)
    await test_sin_cos(dut, tqv, angle=-30, tol_mode="rel", tol=0.025)
    await test_sin_cos(dut, tqv, angle=-45, tol_mode="rel", tol=0.025)
    await test_sin_cos(dut, tqv, angle=-60, tol_mode="rel", tol=0.025)
    await test_sin_cos(dut, tqv, angle=-75, tol_mode="rel", tol=0.025)

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
