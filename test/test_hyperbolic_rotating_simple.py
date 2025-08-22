# SPDX-FileCopyrightText: © 2025 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

from tqv import TinyQV
from fixed_point import *
import math 
from test_utils import test_sinh_cosh
import numpy as np 

# When submitting your design, change this to the peripheral number
# in peripherals.v.  e.g. if your design is i_user_peri05, set this to 5.
# The peripheral number is not used by the test harness.
PERIPHERAL_NUM = 0

@cocotb.test()
async def test_hyperbolic_basic(dut):
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
 
    # test few well known values
    x = 0.0
    out1, out2 = await test_sinh_cosh(dut, tqv, x=x, tol_mode="abs", tol=0.001)

    # ln(2)
    x = math.log(2)
    out1, out2 = await test_sinh_cosh(dut, tqv, x=x, tol_mode="abs", tol=0.001)

    # -ln(2)
    x = -math.log(2)
    out1, out2 = await test_sinh_cosh(dut, tqv, x=x, tol_mode="abs", tol=0.001)

    x = 1.0
    out1, out2 = await test_sinh_cosh(dut, tqv, x=x, tol_mode="abs", tol=0.001)

    x = -1.0
    out1, out2 = await test_sinh_cosh(dut, tqv, x=x, tol_mode="abs", tol=0.001)

    x = math.log(3)
    out1, out2 = await test_sinh_cosh(dut, tqv, x=x, tol_mode="abs", tol=0.001)

    x = -math.log(3)
    out1, out2 = await test_sinh_cosh(dut, tqv, x=x, tol_mode="abs", tol=0.001)
