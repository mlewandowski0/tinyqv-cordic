# SPDX-FileCopyrightText: © 2025 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles

from tqv import TinyQV
from fixed_point import *
import math 
from test_utils import test_vectoring_hyperbolic
import numpy as np 
import matplotlib.pyplot as plt
import os 
from pathlib import Path

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
    
    K_m1 = 0.82816
    K = 1 / K_m1
 
    # test few well known values
    s = np.linspace(0.0, 10, 100)
    s_true = 2 * np.sqrt(s)
    s_pred = []
    tanh_pred = []
    
    for val in s:    
        x = val + 1
        y = val - 1
        out1, out1_float, out2, out2_float = await test_vectoring_hyperbolic(dut, tqv, x=x, y=y, tol_mode="abs", tol=0.001,
                                                                            integer_bits=7)
        out1_float = K * out1_float
        s_pred.append(out1_float)
        tanh_pred.append(out2_float)

    
    # Make plots for visualization
    OUTDIR = Path(os.getenv("CORDIC_PLOTS_DIR", os.getenv("GITHUB_WORKSPACE", "."))) / "artifacts/cordic"
    OUTDIR.mkdir(parents=True, exist_ok=True)

    MAE = np.mean(np.abs(s_true - np.array(s_pred)))

    plt.figure(figsize=(14, 10))
    plt.subplot(2, 2, 1)
    plt.title(f"square root : MAE = {MAE:.5f}")
    plt.plot(s, s_true, label='True Square Root', color='blue')
    plt.plot(s, s_pred, label='Square Root from hardware block', linestyle='--', color='red')
    plt.xlabel("input x")
    plt.ylabel("Square Root value")
    plt.legend()

    plt.subplot(2, 2, 2)
    plt.title("Residual : true - predicted")
    plt.plot(s, s_true - s_pred, label='residue (true - predicted)', color='red')
    plt.xlabel("input x")
    plt.ylabel("Residue : true - predicted")
    plt.legend()
    
    plt.subplot(2,2, 3)
    plt.title("tanh computed")
    plt.plot(s, np.array(tanh_pred), label="tanh(x) from hardware block", color="red")
    plt.xlabel("input x")
    plt.ylabel("out 2")
    plt.legend()
    plt.savefig(os.path.join(OUTDIR, "sqrt.png"),  dpi=180, bbox_inches="tight")
    plt.close()