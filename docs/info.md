<!---

This file is used to generate your project datasheet. Please fill in the information below and delete any unused
sections.

The peripheral index is the number TinyQV will use to select your peripheral.  You will pick a free
slot when raising the pull request against the main TinyQV repository, and can fill this in then.  You
also need to set this value as the PERIPHERAL_NUM in your test script.

You can also include images in this folder and reference them in the markdown. Each image must be less than
512 kb in size, and the combined size of all images must be less than 1 MB.
-->

# tiny CORDIC

Author: Maciej Lewandowski

Peripheral index: n7

## What it does

This repository implements a coordinate rotation digital computer (CORDIC) algorithm, which allows to compute multiple mathematic functions, like $sin(x)$, $cos(x)$, $sinh(x)$, $cosh(x)$, square root, fixed point multiplication and division in few clock cycles.


## Brief introduction to CORDIC 

Trigonometric functions, Multiplication, division are fundamental operations, often required in engineering. They can be often encountarerd in digital signal processing or control. While it is possible to store the trigonometric functions in memory as lookup tables and interpolate, this might require large amount of memories. There exists however a elegant solution of computing these values quite fast, using only additions, subtractions and shifts with a tiny memory footprint. This solution is coordinate rotation digital computer (CORDIC), proposed by Jack E. Volder in 1959 [1] and it can be found in a range of real world microcontrollers for low power, like STM32L031 [2], STM32F031 [2] or other [3]. 

The idea behind the CORDIC algorithm is quite simple and powerful, which allows to compute many different functions like : $sin(x)$, $cos(x)$, $sinh(x)$, $cos(x)$, $\sqrt{x}$, $exp(x)$, $ln(x)$, $a \cdot b$ and $\frac{a}{b}$ using the same hardware. This algorithm is often coverted in standard textbooks and notes [4, 5], therefore only a brief description, to understand how to interact with the underlying hardware with some visualization, to understand it intuitively.

CORDIC is iterative algorithm (in this implementation it takes 12 iterations/clock cycles to compute any function ), and in most general, unified form, this algorithm and designed hardware solves a following set of equations : 

\begin{equation}
x[i+1]  = x[i] - m \cdot \sigma_{j} \cdot y[i]    
\end{equation}

\begin{equation}
y[i+1]  = y[i] + m \sigma_{j} \cdot x[i]
\end{equation}

\begin{equation}
z[i+1]  \begin{cases} z[j] - \sigma_{j} tan^{-1}(2^{-j}) \quad \text{if m = 1} \\ 
z[j] - \sigma_{j} tanh^{-1}(2^{-j}) \quad \text{if m = -1} \\ 
z[j] - \sigma_{j}(2^{-j}) \quad \text{if m = 0}
\end{cases}
\end{equation}



- [1] [J. E. Volder, "The CORDIC Trigonometric Computing Technique," in IRE Transactions on Electronic Computers, vol. EC-8, no. 3, pp. 330-334, Sept. 1959, doi: 10.1109/TEC.1959.5222693.](https://ieeexplore.ieee.org/document/5222693)
- [2] [STM32 DT0085 application note : Coordinate rotation digital computer algoritm (CORIDIC)](https://www.st.com/resource/en/design_tip/dt0085-coordinate-rotation-digital-computer-algorithm-cordic-to-compute-trigonometric-and-hyperbolic-functions-stmicroelectronics.pdf)
- [3] [Application note AN5325 : How to use the CORDIC to perform mathematical functions on STM32 MCUs](https://www.st.com/content/ccc/resource/technical/document/application_note/group1/50/31/98/a8/b5/da/4e/a4/DM00614795/files/DM00614795.pdf/jcr:content/translations/en.DM00614795.pdf)
- [4] [CORDIC ALGORITHM AND IMPLEMENTATIONS](https://web.cs.ucla.edu/digital_arithmetic/files/ch11.pdf) 
- [5] [Chapter 24 : CORDIC Algorithms and Architectures](https://people.eecs.berkeley.edu/~newton/Classes/EE290sp99/lectures/ee290aSp996_1/cordic_chap24.pdf)

## Visualization 


## Register map

Document the registers that are used to interact with your peripheral

| Address | Name         | Access | Description |
|--------:|--------------|:------:|-------------|
| 0x00    | config       |  R/W   | Control bits {is_rot, mode[1:0], en}. See §Config (0x00). |
| 0x01    | input A      |   W    | Operand A (per-mode; see details). |
| 0x02    | input B      |   W    | Operand B (per-mode; see details). |
| 0x03    | 1.0 position |   W    | Q-format selector (e.g., 11 ⇒ Q5.11; 14 ⇒ Q2.14). |
| 0x04    | output 1     |   R    | Primary result. |
| 0x05    | output 2     |   R    | Secondary result / diagnostic. |
| 0x06    | status       |   R    | 0=ready, 1=busy, 2=done. |



## Detailed description of the registers

### Config (0x00)
| Bits  | Name   | Meaning                               |
|:-----:|--------|----------------------------------------|
| [3]   | is_rot | 1 = Rotating, 0 = Vectoring            |
| [2:1] | mode   | 00=CIRCULAR, 01=LINEAR, 10=HYPERBOLIC |
| [0]   | start  | Write 1 to start; auto-clears          |

### input A (0x01)
- __Circular and Rotating mode__ : angle represented as radian in signed fixed point format. For 16 bit mode, this corresponds to  Q2.14 value.
- __Circular and Vectoring mode__: denotes first input, for which we will compute the magnitude and atan, which is $\sqrt{a^2 + b^2}$. This is represented as a Q2.14 value.
-  __Linear and Rotating mode__: A represents first multiplicand in variable fixed point format. To control on where the position of 1.0 is, register 0x03 has to be used. To given an example,  if register 0x03 is set to 11, this input (A) and input (B) represent value in Q5.11 format.
- __Linear and Vectoring mode__: A represents denominator ($\frac{B}{A}$) in variable fixed point format : to control on where the position of 1.0 is. To given an example,  if register 0x03 is set to 11, this input (A) and input (B) represent value in Q5.11 format. 
- __Hyperbolic and Rotating mode__ : the value for which we will compute the sinh(A) and cos(A) represented in Q2.14 fixed point representation. An important limitation here is range : due to lack of resources, the input has to be in range[-1.1161, 1.1161]. It is possible to extend this range using some hyperbolic identities (more clock cycles required though). 
- __Hyperbolic and Vectoring mode__ :  first input A for hyperbolic mode. The output here can represent any fixed point __as long as it is greater then second input B__ ($\sqrt{A^2 -B^2}$ becomes undefined then), because the output is __not scaled__ (not multiplied by $K_{1}$ due to resource limitations). It is up to user to either multiply by $K_{1}\approx \frac{1}{0.82816} \approx 1.207496$ or use it the computed value of $K_{1} \sqrt{A^{2} - B^{2}}$. <br>

### input B (0x02)
- __Circular and Rotating mode__ : not used. 
- __Circular and Vectoring mode__: denotes second input, for which we will compute the magnitude and atan, which is $\sqrt{a^2 + b^2}$. This is represented as a Q2.14 value. 
- __Linear and Rotating mode__: A represents second multiplicand in variable fixed point format  : to control on where the position of 1.0 is. To given an example,  if register 0x03 is set to 11, this input (A) and input (B) represent value in Q5.11 format.
- __Linear and Vectoring mode__: B represents nominator ($\frac{B}{A}$) in variable fixed point format. To control on where the position of 1.0 is, register 0x03 has to be used. To given an example,  if register 0x03 is set to 11, this input (A) and input (B) represent value in Q5.11 format. 
- __Hyperbolic and Rotating mode__ not used. 
- __Hyperbolic and Vectoring mode__ :  Second value B for hyperbolic mode. __this value has to be smaller then A, otherwise result will be incorrect__. The output here can represent any fixed point. The output is __not scaled__ (not multiplied by $K_{1}$ due to resource limitations). It is up to user to either multiply by $K_{1}\approx \frac{1}{0.82816} \approx 1.207496$ or use it the computed value of $K_{1} \sqrt{A^{2} - B^{2}}$.

### Output 1 (0x04)
 - __Circular and Rotating mode__ : returns cos(A), stored in Q2.14 format. 
 -  __Circular and Vectoring mode__: returns $K_{C} \cdot \sqrt{A^2 + B^2}$ where $K_{C} = 1.64676$.
 -  __Linear and Rotating mode__: returns $A \cdot B$ in a fixed float format configured by the register 0x03. <br> - __Linear and Vectoring mode__: returns $\frac{B}{A}$ in a fixed float format by the register 0x03. 
 - __Hyperbolic and Rotating mode__ : returns cosh(A) stored in Q2.14 format. 
 - __Hyperbolic and Vectoring mode__ :  returns $K_{H} \cdot \sqrt{A^2 - B^2}$ where $K_{H} \approx 0.82816$. The output is not scaled : this means that it is up to programmer and software to interpret this value (with consistent format of A, B and $K_H$ its possible to get wide range of fixed points) <br>

### Output 2 (0x05)
- __Circular and Rotating mode__ : returns sin(A), stored in Q2.14 format. 
- __Circular and Vectoring mode__: returns $tan^{-1}(\frac{B}{A})$ 
- __Linear and Rotating mode__: In the unified CORDIC this returned value corresponds to final value of $z$ (z after N iterations). This value is quite difficult to interpret, but it is somehow dependent on the error. In ideal case this should be 0 (in which case the output 1 corresponds to correct value). Large magnitude values can indicate that the conversion was unsuccessful. 
- __Linear and Vectoring mode__: In the unified CORDIC this returned value corresponds to final value of $y$ (y after N iterations). This value is quite difficult to interpret, but it is somehow dependent on the error. In ideal case this should be 0 (in which case the output 1 corresponds to correct value). Large magnitude values can indicate that the conversion was unsuccessful. 
- __Hyperbolic and Rotating mode__ : returns sinh(A) stored in Q2.14 format.
- __Hyperbolic and Vectoring mode__ :  returns $tanh^{-1}(\frac{y}{x})$ stored in Q2.14 format <br>

### Status (0x06)
| Value | Meaning |
|:----:|---------|
| 0    | ready   |
| 1    | busy    |
| 2    | done    |

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

- None required this is mainly extension for core, to allow computing of trigonometric functions , multiplication, division, hyperbolic and square root. This can have many applications in audio ( generating sine values or cose values) or in control (in motor control). 