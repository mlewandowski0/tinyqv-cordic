<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

The peripheral index is the number TinyQV will use to select your peripheral.  You will pick a free
slot when raising the pull request against the main TinyQV repository, and can fill this in then.  You
also need to set this value as the PERIPHERAL_NUM in your test script.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

# Your project title

Author: Maciej Lewandowski

Peripheral index: n7

## What it does

This repository implements a coordinate rotation digital computer (CORDIC) algorithm, which allows to compute 


## Brief introduction to CORDIC 


## Visualization 

## Register map

Document the registers that are used to interact with your peripheral

| Address | Name  | Access | Description                                                         |
|---------|-------|--------|---------------------------------------------------------------------|
| 0x00    | RUN config  | R/W    | 4 bits corresponding to mode of the CORDIC.  It is stored in following format {is_rotating, mode, start} with is_rotating being one bit, mode being 2 bits denoting mode of operation (0 = CIRCULAR, 1 = LINEAR, 2 = HYPERBOLIC) and start denotes a single bit( which wil be cleared) that if set to 1, will start the computation given the inputs.                                                    |
| 0x01    | input A  | W    | for CIRCULAR mode this denotes angle represented as radian in signed fixed point format. For 16 bit mode, this corresponds to  Q2.14 value.  |

## How to test
This section explains how to test and use this peripheral with examples. 
### trigonetric function (sin and cos)
CORDIC allow you to get sin and cosine value from ~ -99. to 99 degrees [] simulataneously. The input is an angle. An example use of getting sin and cosine of 30 degrees (which is pi/6 \approx 0.52359877, which corresponds to b00100001_10000011 ).

```
// convert angle to fixed point value to angle

// set the angle of the cordic
write_to_register(1, angle)

// configuration : set the mode to CIRCULAR, ROTATING, RUNNING
write_to_register(0,                      0b00_1_1)

// wait few clock cycles : either check the status register 6 or wait for interrupt, or for 10 clock cycles
while (read_the_register(6) == 1) // 1 denotes BUSY, 2 denotes ONE
{}

// read the result 
cosine_of_angle = read_the_register(4)
sine_of_angle = read_the_register(5)
```

## External hardware

List external hardware used in your project (e.g. PMOD, LED display, etc), if any
