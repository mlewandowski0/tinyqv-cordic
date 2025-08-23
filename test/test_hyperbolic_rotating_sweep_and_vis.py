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
import matplotlib.pyplot as plt 
import os 
from pathlib import Path


# When submitting your design, change this to the peripheral number
# in peripherals.v.  e.g. if your design is i_user_peri05, set this to 5.
# The peripheral number is not used by the test harness.
PERIPHERAL_NUM = 0

@cocotb.test()
async def test_hyperbolic_sweep_and_vis(dut):
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
    sinhs, cosinhs = [], []

    linspace = np.linspace(-1.1161, 1.1161, 200)
    sinhs_true = np.sinh(linspace)
    cosinhs_true = np.cosh(linspace)


    for x in linspace:
        out1, out2 = await test_sinh_cosh(dut, tqv, x=x, tol_mode="abs", tol=0.025)
        cosinhs.append(fixed_to_float(out1, 16, 2))
        sinhs.append(fixed_to_float(out2, 16, 2))  # sin is in out2

    # Compute the Mean Absolute Error (MAE) for the current sweep
    MAE_sinh = np.mean(np.abs(sinhs - sinhs_true))
    MAE_cosh = np.mean(np.abs(cosinhs - cosinhs_true))
    dut._log.info(f"MAE for angle sweep: for sinh = {MAE_sinh:.5f}, for cosh = {MAE_cosh:.5f}")


    # Make plots for visualization
    OUTDIR = Path(os.getenv("CORDIC_PLOTS_DIR", os.getenv("GITHUB_WORKSPACE", "."))) / "artifacts/cordic"
    OUTDIR.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(14, 4))
    plt.subplot(1, 2, 1)
    plt.title(f"Sinh Sweep : MAE = {MAE_sinh:.5f}")
    plt.plot(linspace, sinhs_true, label='True Sinh', color='blue')
    plt.plot(linspace, sinhs, label='Sinh from hardware block', linestyle='--', color='red')
    plt.xlabel("input x")
    plt.ylabel("Sinh(x) value")
    plt.legend()

    plt.subplot(1, 2, 2)
    plt.plot(linspace, sinhs_true - sinhs, label='residue (true - predicted)', color='red')
    plt.legend()
    plt.xlabel("input x")
    plt.ylabel("Residue : true - predicted")
    plt.savefig(os.path.join(OUTDIR, "sinh.png"),  dpi=180, bbox_inches="tight")
    plt.close()


    plt.figure(figsize=(14, 4))
    plt.subplot(1, 2, 1)
    plt.title(f"Cosine Sweep : MAE = {MAE_cosh:.5f}")
    plt.plot(linspace, cosinhs_true, label='True Cosh', color='blue')
    plt.plot(linspace, cosinhs, label='Cosh from hardware block', linestyle='--', color='red')
    plt.xlabel("input x")
    plt.ylabel("cosh(x) value")
    plt.legend()

    plt.subplot(1, 2, 2)
    plt.plot(linspace, cosinhs_true - cosinhs, label='residue (true - predicted)', color='red')
    plt.legend()
    plt.xlabel("input x")
    plt.ylabel("Residue : true - predicted")
    plt.savefig(os.path.join(OUTDIR, "cosh.png"), dpi=180, bbox_inches="tight")
    plt.close()
    
    # (optional) also stash numeric data for later:
    np.savetxt(os.path.join(OUTDIR, "sinh_vs_true.csv"),
            np.c_[linspace, sinhs_true, sinhs],
            delimiter=",", header="inp,true_sinh,cordic_sinh", comments="")
    np.savetxt(os.path.join(OUTDIR, "cosh_vs_true.csv"),
            np.c_[linspace, cosinhs_true, cosinhs],
            delimiter=",", header="inp,true_cosh,cordic_cosh", comments="")

    assert MAE_cosh < 0.001, "Mean absolute error for cosh should be less then 0.001"
    assert MAE_sinh < 0.001, "Mean absolute error for sinh should be less then 0.001"
