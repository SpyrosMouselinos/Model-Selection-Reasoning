# ============ Validation in Geometry Dataset ================= #
MINI_VAL = '''
You will be provided with a problem and an answer. You need to check if the answer is correct. If the answer is not correct, you need to suggest changes to make the answer valid.'
Examples:
Question: Amy and Belinda each roll a sheet of 6-inch by 8-inch paper to form a cylindrical tube.
Amy tapes the two 8-inch sides together without overlap.
Belinda tapes the two 6-inch sides together without overlap.
What is the positive difference of the volumes of the two tubes?
Proposed Answer:
We need to calculate the volumes of tubes:
Amy forms a cylinder with a height of 8 inches and a radius of half the 6-inch side.
Radius r_A = \\frac{6}{2} = 3. Height h_A = 8 inches. Volume V_A = \\pi r_A^2 h_A = \\pi \\times 3^2 \\times 8 = 72\\pi.
Belinda forms a cylinder with a height of 6 inches and a radius of half the 8-inch side.
Radius r_B = \\frac{8}{2} = 4 inches. Height h_B = 6 inches. Volume V_B = \\pi r_B^2 h_B = \\pi \\times 4^2 \\times 6 = 96\\pi.
The positive difference is approximately 24\\pi.
\\boxed{24\\pi}.
Correct Answer:
#There are mistakes. Here is a valid solution:
Amy's Cylinder: Base circumference is 2\\pi times r_A = 6 inches, so the radius r_A = \\frac{3}{\\pi} inches.
Volume V_A = \\pi times r_A^2 h_A = \\pi \\frac{3}{\\pi}^2 \\times 8 = \\frac{72}{\\pi} cubic inches.
Belinda's Cylinder: Base circumference is 2\\pi r_B = 8 inches, so the radius r_B = \\frac{4}{\\pi} inches.
Volume V_B = \\pi r_B^2 h_B = \\pi \\frac{4}{\\pi}^2 \\times 6 = \frac{96}{\\pi}cubic inches.
The positive difference |V_B - V_A| = |\\frac{96}{\\pi} - \\frac{72}{\\pi}| = \\frac{24}{\\pi}
\\boxed{\\frac{24}{\\pi}}.

Question: Right triangle ABC has AB=3, BC=4, AC=5.
Square XYZW is inscribed in ABC with X and Y on AC, W on AB, Z on BC.
What is the side length of the square s?
Proposed Answer:
Determine h: From point B in right triangle ABC is h = \\frac{3 \\times 4}{5} = \\frac{12}{5}
Since triangles ABC and WBZ are similar, we have \\frac{h-s}{s} = \\frac{h}{AC} = \\frac{h}{5} 
Solving for s, we get s = \\frac{5h}{5 + h}, substitute h = \\frac{12}{5} into the equation
s = \\frac{5 \\times \\frac{12}{5}}{5 + \\frac{12}{5}} = \\frac{60}{37}
Therefore, s = \\boxed{\\frac{60}{37}}
Correct Answer:
#The answer is correct. Lets return it again:
\\boxed{\\frac{60}{37}}
'''.strip()
