# SPDX-FileCopyrightText: © 2025 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

from tqv import TinyQV
from fixed_point import *
import math 
import numpy as np
from pathlib import Path

import os
import matplotlib
import matplotlib.pyplot as plt

from test_utils import test_sin_cos

matplotlib.use("Agg")  # headless backend


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



@cocotb.test()
async def test_trigonometric_sweep_and_vis(dut):
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
 

    # first test : compute the sin(30 degrees) and cos(30 degrees)

    # the input to circular mode in rotating, is only angle, stored as radians, fixed point 
    # arithmetic in signed 1.14 bits format ( for FIXED WIDTH = 16, in general case, in signed 1.{FIXED_WIDTH-2} format )
    # 30 degrees = pi / 6 = 0.52359877 \approx (in fixed point) b00100001_10000011
    sines, cosines = [], []

    linspace = np.linspace(-90, 90, 180)
    sines_true = np.sin(linspace * np.pi / 180.)
    cosines_true = np.cos(linspace * np.pi / 180.)


    for angle in linspace:
        out1, out2 = await test_sin_cos(dut, tqv, angle=angle, tol_mode="abs", tol=0.025)
        cosines.append(fixed_to_float(out1, 16, 2))
        sines.append(fixed_to_float(out2, 16, 2))  # sin is in out2

    # Compute the Mean Absolute Error (MAE) for the current sweep
    MAE_sin = np.mean(np.abs(sines - sines_true))
    MAE_cos = np.mean(np.abs(cosines - cosines_true))
    dut._log.info(f"MAE for angle sweep: for sin = {MAE_sin:.5f}, for cos = {MAE_cos:.5f}")
    
    
    # Make plots for visualization
    OUTDIR = Path(os.getenv("CORDIC_PLOTS_DIR", os.getenv("GITHUB_WORKSPACE", "."))) / "artifacts/cordic"
    OUTDIR.mkdir(parents=True, exist_ok=True)
    
    plt.figure(figsize=(14, 4))
    plt.subplot(1, 2, 1)
    plt.title(f"Sine Sweep : MAE = {MAE_sin:.5f}")
    plt.plot(linspace, sines_true, label='True Sine', color='blue')
    plt.plot(linspace, sines, label='Sine from hardware block', linestyle='--', color='red')
    plt.xlabel("Angle (in degrees)")
    plt.ylabel("Sin(x) value")
    plt.xticks([-90, -75, -60, -45, -30, -15, 0, 15, 30, 45, 60, 75, 90])
    plt.legend()

    plt.subplot(1, 2, 2)
    plt.plot(linspace, sines_true - sines, label='residue (true - predicted)', color='red')
    plt.legend()
    plt.xlabel("Angle (in degrees)")
    plt.ylabel("Residue : true - predicted")
    plt.xticks([-90, -75, -60, -45, -30, -15, 0, 15, 30, 45, 60, 75, 90])
    plt.savefig(os.path.join(OUTDIR, "sine.png"),  dpi=180, bbox_inches="tight")
    plt.close()


    plt.figure(figsize=(14, 4))
    plt.subplot(1, 2, 1)
    plt.title(f"Cosine Sweep : MAE = {MAE_cos:.5f}")
    plt.plot(linspace, cosines_true, label='True Cosine', color='blue')
    plt.plot(linspace, cosines, label='Cosine from hardware block', linestyle='--', color='red')
    plt.xlabel("Angle (in degrees)")
    plt.ylabel("Cos(x) value")
    plt.xticks([-90, -75, -60, -45, -30, -15, 0, 15, 30, 45, 60, 75, 90])
    plt.legend()

    plt.subplot(1, 2, 2)
    plt.plot(linspace, cosines_true - cosines, label='residue (true - predicted)', color='red')
    plt.legend()
    plt.xlabel("Angle (in degrees)")
    plt.ylabel("Residue : true - predicted")
    plt.xticks([-90, -75, -60, -45, -30, -15, 0, 15, 30, 45, 60, 75, 90])
    plt.savefig(os.path.join(OUTDIR, "cosine.png"), dpi=180, bbox_inches="tight")
    plt.close()
    
    # (optional) also stash numeric data for later:
    np.savetxt(os.path.join(OUTDIR, "sine_vs_true.csv"),
            np.c_[linspace, sines_true, sines],
            delimiter=",", header="deg,true_sin,cordic_sin", comments="")
    np.savetxt(os.path.join(OUTDIR, "cosine_vs_true.csv"),
            np.c_[linspace, cosines_true, cosines],
            delimiter=",", header="deg,true_cos,cordic_cos", comments="")
        
    assert MAE_cos < 0.01, "Mean absolute error for cosine should be less then 0.01"
    assert MAE_sin < 0.01, "Mean absolute error for sine should be less then 0.01"


    
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
