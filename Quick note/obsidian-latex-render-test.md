# Obsidian LaTeX / MathJax Render Test Sheet

This file is meant to be opened directly in Obsidian to see which LaTeX-style math syntax renders in your current setup.

Obsidian supports math through MathJax syntax using:

Inline math:

```md
$E = mc^2$
```

Block math:

```md
$$
E = mc^2
$$
```

Use this file in Reading View or Live Preview. Some items may render differently depending on Obsidian version, installed plugins, theme CSS, and enabled MathJax extensions.

---

## 1. Inline Math

Plain inline expression: $E = mc^2$

Inline Greek letters: $\alpha, \beta, \gamma, \delta, \epsilon, \theta, \lambda, \mu, \pi, \sigma, \omega$

Inline superscript/subscript: $x_i^2 + y_{n+1}^{k-1}$

Inline fraction: $\frac{a+b}{c+d}$

Inline square root: $\sqrt{x^2 + y^2}$

Inline nth root: $\sqrt[3]{8} = 2$

Inline absolute value: $|x-y|$

Inline norm: $\lVert x \rVert_2$

Inline text inside math: $x \text{ is positive}$

Inline escaped dollar sign in text: this costs \$5, while math uses $x=5$.

---

## 2. Display / Block Math

Simple display equation:

$$
E = mc^2
$$

Quadratic formula:

$$
x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
$$

Pythagorean theorem:

$$
a^2 + b^2 = c^2
$$

Euler identity:

$$
e^{i\pi} + 1 = 0
$$

---

## 3. Basic Operators

$$
a + b - c \times d \div e \cdot f
$$

$$
x \pm y \mp z
$$

$$
a \ast b \star c \circ d \bullet e
$$

$$
a \oplus b \otimes c \odot d
$$

---

## 4. Relations

$$
a = b,\quad a \ne b,\quad a \neq b
$$

$$
a < b,\quad a > b,\quad a \le b,\quad a \leq b,\quad a \ge b,\quad a \geq b
$$

$$
a \approx b,\quad a \sim b,\quad a \simeq b,\quad a \equiv b
$$

$$
a \propto b,\quad a \parallel b,\quad a \perp b
$$

---

## 5. Fractions, Roots, Powers, Subscripts

$$
\frac{1}{2}
$$

$$
\frac{x^2 + 2x + 1}{x - 1}
$$

$$
\dfrac{x^2}{y^2}
$$

$$
\tfrac{1}{2}
$$

$$
\sqrt{x}
$$

$$
\sqrt{x^2 + y^2}
$$

$$
\sqrt[n]{x}
$$

$$
x_1,\quad x_{i,j},\quad x^2,\quad x^{n+1},\quad x_i^j,\quad x_{i+1}^{j-1}
$$

---

## 6. Greek Letters

Lowercase:

$$
\alpha \beta \gamma \delta \epsilon \varepsilon \zeta \eta \theta \vartheta \iota \kappa \lambda \mu \nu \xi \omicron \pi \varpi \rho \varrho \sigma \varsigma \tau \upsilon \phi \varphi \chi \psi \omega
$$

Uppercase:

$$
\Gamma \Delta \Theta \Lambda \Xi \Pi \Sigma \Upsilon \Phi \Psi \Omega
$$

---

## 7. Common Constants and Sets

$$
\infty,\quad \partial,\quad \nabla,\quad \emptyset,\quad \varnothing
$$

$$
\mathbb{N},\quad \mathbb{Z},\quad \mathbb{Q},\quad \mathbb{R},\quad \mathbb{C}
$$

$$
\mathcal{A},\quad \mathcal{B},\quad \mathcal{F},\quad \mathcal{L}
$$

$$
\mathfrak{g},\quad \mathfrak{h},\quad \mathfrak{so}(3)
$$

---

## 8. Logic Symbols

$$
P \land Q
$$

$$
P \lor Q
$$

$$
\neg P
$$

$$
P \implies Q
$$

$$
P \Rightarrow Q
$$

$$
P \iff Q
$$

$$
P \Leftrightarrow Q
$$

$$
\forall x \in X,\quad \exists y \in Y
$$

$$
\nexists z \in Z
$$

---

## 9. Set Theory

$$
x \in A,\quad x \notin A
$$

$$
A \subset B,\quad A \subseteq B,\quad A \supset B,\quad A \supseteq B
$$

$$
A \cup B,\quad A \cap B,\quad A \setminus B
$$

$$
A \times B
$$

$$
\{x \in \mathbb{R} \mid x > 0\}
$$

$$
\left\{ x \in \mathbb{R} : x^2 < 1 \right\}
$$

---

## 10. Arrows

$$
a \to b,\quad a \rightarrow b,\quad a \leftarrow b
$$

$$
a \Rightarrow b,\quad a \Leftarrow b,\quad a \Leftrightarrow b
$$

$$
a \mapsto b
$$

$$
A \longrightarrow B,\quad A \Longrightarrow B
$$

$$
x \uparrow y,\quad x \downarrow y,\quad x \updownarrow y
$$

$$
A \hookrightarrow B,\quad A \twoheadrightarrow B
$$

---

## 11. Calculus

Derivative:

$$
\frac{dy}{dx}
$$

Partial derivative:

$$
\frac{\partial f}{\partial x}
$$

Second derivative:

$$
\frac{d^2y}{dx^2}
$$

Gradient:

$$
\nabla f
$$

Divergence:

$$
\nabla \cdot \vec{F}
$$

Curl:

$$
\nabla \times \vec{F}
$$

Limit:

$$
\lim_{x \to 0} \frac{\sin x}{x} = 1
$$

Integral:

$$
\int_a^b f(x)\,dx
$$

Double integral:

$$
\iint_D f(x,y)\,dA
$$

Triple integral:

$$
\iiint_V f(x,y,z)\,dV
$$

Contour integral:

$$
\oint_C \vec{F} \cdot d\vec{r}
$$

---

## 12. Sums, Products, Limits

Sum:

$$
\sum_{i=1}^{n} i = \frac{n(n+1)}{2}
$$

Product:

$$
\prod_{i=1}^{n} i = n!
$$

Union indexed:

$$
\bigcup_{i=1}^{n} A_i
$$

Intersection indexed:

$$
\bigcap_{i=1}^{n} A_i
$$

Limit superior/inferior:

$$
\limsup_{n \to \infty} a_n,\quad \liminf_{n \to \infty} a_n
$$

---

## 13. Brackets and Delimiters

Normal brackets:

$$
(a+b),\quad [a+b],\quad \{a+b\}
$$

Auto-sized brackets:

$$
\left( \frac{a+b}{c+d} \right)
$$

Auto-sized square brackets:

$$
\left[ \frac{a+b}{c+d} \right]
$$

Auto-sized braces:

$$
\left\{ \frac{a+b}{c+d} \right\}
$$

Angle brackets:

$$
\langle x, y \rangle
$$

Floor and ceiling:

$$
\lfloor x \rfloor,\quad \lceil x \rceil
$$

Norm:

$$
\left\lVert x \right\rVert_2
$$

Absolute value:

$$
\left| \frac{x}{y} \right|
$$

---

## 14. Matrices

Plain matrix:

$$
\begin{matrix}
1 & 2 \\
3 & 4
\end{matrix}
$$

Parentheses matrix:

$$
\begin{pmatrix}
1 & 2 \\
3 & 4
\end{pmatrix}
$$

Brackets matrix:

$$
\begin{bmatrix}
1 & 2 \\
3 & 4
\end{bmatrix}
$$

Braces matrix:

$$
\begin{Bmatrix}
1 & 2 \\
3 & 4
\end{Bmatrix}
$$

Vertical bars matrix:

$$
\begin{vmatrix}
a & b \\
c & d
\end{vmatrix}
$$

Double vertical bars matrix:

$$
\begin{Vmatrix}
a & b \\
c & d
\end{Vmatrix}
$$

Augmented matrix:

$$
\left[
\begin{array}{cc|c}
1 & 2 & 3 \\
4 & 5 & 6
\end{array}
\right]
$$

Matrix with dots:

$$
\begin{bmatrix}
a_{11} & a_{12} & \cdots & a_{1n} \\
a_{21} & a_{22} & \cdots & a_{2n} \\
\vdots & \vdots & \ddots & \vdots \\
a_{m1} & a_{m2} & \cdots & a_{mn}
\end{bmatrix}
$$

---

## 15. Arrays

Basic array:

$$
\begin{array}{ccc}
a & b & c \\
d & e & f
\end{array}
$$

Aligned columns:

$$
\begin{array}{rcl}
f(x) & = & x^2 + 2x + 1 \\
     & = & (x+1)^2
\end{array}
$$

Piecewise function using array:

$$
f(x) =
\left\{
\begin{array}{ll}
x^2, & x \ge 0 \\
-x, & x < 0
\end{array}
\right.
$$

---

## 16. Cases

Piecewise function:

$$
f(x) =
\begin{cases}
x^2, & x \ge 0 \\
-x, & x < 0
\end{cases}
$$

Probability distribution:

$$
P(X=x) =
\begin{cases}
p, & x=1 \\
1-p, & x=0 \\
0, & \text{otherwise}
\end{cases}
$$

---

## 17. Alignment Environments

Aligned equations:

$$
\begin{aligned}
(a+b)^2 &= (a+b)(a+b) \\
&= a^2 + 2ab + b^2
\end{aligned}
$$

Aligned derivation:

$$
\begin{aligned}
\frac{d}{dx} x^n
&= \lim_{h \to 0} \frac{(x+h)^n - x^n}{h} \\
&= n x^{n-1}
\end{aligned}
$$

Aligned at multiple points:

$$
\begin{alignedat}{2}
x &= y + z, \quad & a &= b + c \\
m &= n + p, \quad & r &= s + t
\end{alignedat}
$$

Gathered equations:

$$
\begin{gathered}
a = b + c \\
x = y + z
\end{gathered}
$$

---

## 18. Multiline With `split`

This may or may not render depending on MathJax configuration:

$$
\begin{split}
(a+b+c)^2
&= a^2 + b^2 + c^2 \\
&\quad + 2ab + 2ac + 2bc
\end{split}
$$

---

## 19. Numbered Equation Environments

These may render, but numbering support can differ in Obsidian:

$$
\begin{equation}
E = mc^2
\end{equation}
$$

Equation with label/reference often does **not** behave like full LaTeX in plain Obsidian:

$$
\begin{equation}
\label{eq:test}
a^2 + b^2 = c^2
\end{equation}
$$

Reference test: $\ref{eq:test}$

---

## 20. Text Styles Inside Math

Roman:

$$
\mathrm{d}x,\quad \mathrm{sin}
$$

Italic default:

$$
abcxyz
$$

Bold:

$$
\mathbf{x},\quad \boldsymbol{\alpha}
$$

Calligraphic:

$$
\mathcal{F},\quad \mathcal{L}
$$

Blackboard bold:

$$
\mathbb{R},\quad \mathbb{E}
$$

Sans serif:

$$
\mathsf{ABC}
$$

Typewriter:

$$
\mathtt{ABC}
$$

Text inside equation:

$$
f(x) = 0 \quad \text{for all } x < 0
$$

---

## 21. Spacing

No explicit spacing:

$$
abcd
$$

Thin space:

$$
a\,b
$$

Medium space:

$$
a\:b
$$

Thick space:

$$
a\;b
$$

Quad:

$$
a\quad b
$$

Double quad:

$$
a\qquad b
$$

Negative thin space:

$$
a\!b
$$

---

## 22. Decorations

Hat:

$$
\hat{x},\quad \widehat{xyz}
$$

Bar:

$$
\bar{x},\quad \overline{xyz}
$$

Tilde:

$$
\tilde{x},\quad \widetilde{xyz}
$$

Vector:

$$
\vec{x},\quad \overrightarrow{AB}
$$

Dot:

$$
\dot{x},\quad \ddot{x}
$$

Prime:

$$
f'(x),\quad f''(x),\quad f^{(n)}(x)
$$

Underline:

$$
\underline{x+y}
$$

Overbrace:

$$
\overbrace{a+b+c}^{\text{sum}}
$$

Underbrace:

$$
\underbrace{a+b+c}_{\text{sum}}
$$

---

## 23. Accents

$$
\acute{x},\quad \grave{x},\quad \breve{x},\quad \check{x}
$$

$$
\mathring{x},\quad \dot{x},\quad \ddot{x}
$$

---

## 24. Trigonometric and Named Functions

$$
\sin x,\quad \cos x,\quad \tan x
$$

$$
\arcsin x,\quad \arccos x,\quad \arctan x
$$

$$
\sinh x,\quad \cosh x,\quad \tanh x
$$

$$
\log x,\quad \ln x,\quad \exp x
$$

$$
\min(x,y),\quad \max(x,y),\quad \arg\max_x f(x),\quad \arg\min_x f(x)
$$

Custom operator:

$$
\operatorname{softmax}(x)_i = \frac{e^{x_i}}{\sum_j e^{x_j}}
$$

---

## 25. Probability and Statistics

Probability:

$$
P(A \mid B) = \frac{P(B \mid A)P(A)}{P(B)}
$$

Expectation:

$$
\mathbb{E}[X] = \sum_x x P(X=x)
$$

Variance:

$$
\operatorname{Var}(X) = \mathbb{E}[X^2] - \mathbb{E}[X]^2
$$

Covariance:

$$
\operatorname{Cov}(X,Y) = \mathbb{E}[(X-\mu_X)(Y-\mu_Y)]
$$

Normal distribution:

$$
X \sim \mathcal{N}(\mu, \sigma^2)
$$

Gaussian density:

$$
p(x) = \frac{1}{\sqrt{2\pi\sigma^2}} \exp\left(-\frac{(x-\mu)^2}{2\sigma^2}\right)
$$

Indicator:

$$
\mathbf{1}_{\{x > 0\}}
$$

---

## 26. Linear Algebra

Vector:

$$
\mathbf{x} =
\begin{bmatrix}
x_1 \\
x_2 \\
x_3
\end{bmatrix}
$$

Dot product:

$$
\mathbf{x}^\top \mathbf{y} = \sum_{i=1}^{n} x_i y_i
$$

Matrix multiplication:

$$
C_{ij} = \sum_{k=1}^{n} A_{ik}B_{kj}
$$

Determinant:

$$
\det(A) =
\begin{vmatrix}
a & b \\
c & d
\end{vmatrix}
= ad - bc
$$

Inverse:

$$
A^{-1}A = I
$$

Eigenvalue equation:

$$
A\mathbf{v} = \lambda \mathbf{v}
$$

Trace:

$$
\operatorname{tr}(A) = \sum_i A_{ii}
$$

Rank:

$$
\operatorname{rank}(A)
$$

---

## 27. Machine Learning / Deep Learning

Loss function:

$$
\mathcal{L}(\theta) = -\sum_{i=1}^{n} y_i \log \hat{y}_i
$$

Gradient descent:

$$
\theta_{t+1} = \theta_t - \eta \nabla_\theta \mathcal{L}(\theta_t)
$$

Softmax:

$$
\operatorname{softmax}(z)_i = \frac{e^{z_i}}{\sum_{j=1}^{K} e^{z_j}}
$$

Attention:

$$
\operatorname{Attention}(Q,K,V) =
\operatorname{softmax}\left(\frac{QK^\top}{\sqrt{d_k}}\right)V
$$

Layer normalization:

$$
\operatorname{LayerNorm}(x) =
\gamma \odot \frac{x - \mu}{\sqrt{\sigma^2 + \epsilon}} + \beta
$$

Cross entropy:

$$
H(p,q) = -\sum_x p(x)\log q(x)
$$

KL divergence:

$$
D_{\mathrm{KL}}(P \parallel Q) =
\sum_x P(x)\log\frac{P(x)}{Q(x)}
$$

---

## 28. Tensor / Index Notation

Einstein summation style:

$$
y_i = A_{ij}x_j
$$

Tensor element:

$$
T_{ijk}^{\ell m}
$$

Kronecker delta:

$$
\delta_{ij} =
\begin{cases}
1, & i=j \\
0, & i \ne j
\end{cases}
$$

Levi-Civita symbol:

$$
\varepsilon_{ijk}
$$

---

## 29. Combinatorics

Factorial:

$$
n!
$$

Binomial coefficient:

$$
\binom{n}{k}
$$

Permutations:

$$
P(n,k) = \frac{n!}{(n-k)!}
$$

Combinations:

$$
C(n,k) = \binom{n}{k} = \frac{n!}{k!(n-k)!}
$$

Multinomial:

$$
\binom{n}{k_1,k_2,\ldots,k_m}
=
\frac{n!}{k_1!k_2!\cdots k_m!}
$$

---

## 30. Geometry

Angles:

$$
\angle ABC
$$

Degree:

$$
90^\circ
$$

Triangle:

$$
\triangle ABC
$$

Congruent:

$$
\triangle ABC \cong \triangle DEF
$$

Similar:

$$
\triangle ABC \sim \triangle DEF
$$

---

## 31. Modular Arithmetic

$$
a \equiv b \pmod{n}
$$

$$
a \equiv b \mod n
$$

$$
\gcd(a,b),\quad \operatorname{lcm}(a,b)
$$

---

## 32. Complex Numbers

$$
z = a + bi
$$

$$
\bar{z} = a - bi
$$

$$
|z| = \sqrt{a^2 + b^2}
$$

$$
e^{i\theta} = \cos\theta + i\sin\theta
$$

$$
\operatorname{Re}(z),\quad \operatorname{Im}(z)
$$

---

## 33. Physics

Newton's second law:

$$
\mathbf{F} = m\mathbf{a}
$$

Kinetic energy:

$$
K = \frac{1}{2}mv^2
$$

Schrodinger equation:

$$
i\hbar \frac{\partial}{\partial t}\Psi(\mathbf{r},t)
=
\hat{H}\Psi(\mathbf{r},t)
$$

Maxwell equation example:

$$
\nabla \cdot \mathbf{E} = \frac{\rho}{\varepsilon_0}
$$

Lorentz factor:

$$
\gamma = \frac{1}{\sqrt{1 - \frac{v^2}{c^2}}}
$$

---

## 34. Chemistry / mhchem Extension Tests

These depend on whether the MathJax mhchem extension is available in your Obsidian setup.

Chemical equation:

$$
\ce{H2O}
$$

Reaction:

$$
\ce{2H2 + O2 -> 2H2O}
$$

Equilibrium:

$$
\ce{CO2 + C <=> 2CO}
$$

Ions:

$$
\ce{Na+ + Cl- -> NaCl}
$$

Isotopes:

$$
\ce{^{14}C}
$$

Physical unit style:

$$
\pu{9.81 m s-2}
$$

Likely unsupported without extra tooling:

$$
\chemfig{H-C(-[2]H)(-[6]H)-H}
$$

---

## 35. Color Tests

Color support may vary depending on MathJax configuration.

$$
\color{red}{x + y}
$$

$$
{\color{blue} A} + {\color{green} B}
$$

Boxed color may not render everywhere:

$$
\colorbox{yellow}{$x^2$}
$$

---

## 36. Boxes

Boxed equation:

$$
\boxed{E = mc^2}
$$

Cancel may depend on extension support:

$$
\cancel{x} + y
$$

$$
\bcancel{x} + y
$$

$$
\xcancel{x} + y
$$

---

## 37. Tags

Manual tag:

$$
E = mc^2 \tag{1}
$$

Named tag:

$$
a^2 + b^2 = c^2 \tag{Pythagoras}
$$

Tag with alignment:

$$
\begin{aligned}
x + y &= z
\end{aligned}
\tag{A}
$$

---

## 38. Macros / New Commands

Some MathJax setups support `\newcommand`, but behavior in Obsidian can vary.

Inline macro definition and use:

$$
\newcommand{\R}{\mathbb{R}}
x \in \R
$$

Macro with argument:

$$
\newcommand{\norm}[1]{\left\lVert #1 \right\rVert}
\norm{x}
$$

Operator macro:

$$
\newcommand{\E}{\mathbb{E}}
\E[X]
$$

---

## 39. LaTeX Environments That Usually Do Not Work Like Full LaTeX

Full LaTeX documents are not expected to render in Obsidian math blocks:

```latex
\documentclass{article}
\begin{document}
Hello
\end{document}
```

TikZ is usually not supported by default:

$$
\begin{tikzpicture}
\draw (0,0) -- (1,1);
\end{tikzpicture}
$$

Commutative diagrams may require extensions not available by default:

$$
\begin{CD}
A @>f>> B \\
@VgVV @VVhV \\
C @>k>> D
\end{CD}
$$

---

## 40. Markdown Interaction Edge Cases

Inline math inside bold text:

**Bold sentence with inline math $x^2 + y^2 = z^2$ inside.**

Inline math inside italic text:

*Italic sentence with inline math $\alpha + \beta$ inside.*

Block math inside a list:

- Item before math

  $$
  x = y + z
  $$

- Item after math

Block math inside quote:

> $$
> E = mc^2
> $$

Block math inside callout:

> [!note]
> $$
> \int_0^1 x^2\,dx = \frac{1}{3}
> $$

Inline math with underscores near text: $a_b$ should render.
$$
\ce{H2O}
$$
Potential conflict with Markdown emphasis: `$x_y$` should render as math, while plain x_y may not.

---

## 41. Escaping and Literal Tests

Dollar sign as currency: \$100

Literal backslash: `\alpha`

Code span with math syntax: `$x^2$`

Code block with math syntax:

```latex
$$
x^2 + y^2 = z^2
$$
```

---

## 42. Unicode Inside Math

Greek typed directly:

$$
α + β = γ
$$

Math symbols typed directly:

$$
∀x ∈ ℝ, ∃y ∈ ℝ
$$

Mixed Unicode and LaTeX:

$$
∀x \in \mathbb{R},\quad x^2 ≥ 0
$$

---

## 43. Long Equation Stress Test

$$
\begin{aligned}
\mathcal{L}(\theta)
&=
-\frac{1}{N}
\sum_{i=1}^{N}
\sum_{k=1}^{K}
y_{ik}
\log
\left(
\frac{
\exp(z_{ik})
}{
\sum_{j=1}^{K}\exp(z_{ij})
}
\right)
+
\lambda
\left\lVert \theta \right\rVert_2^2
\end{aligned}
$$

---

## 44. Nested Structures

Nested fraction:

$$
\frac{1}{1 + \frac{1}{1 + \frac{1}{x}}}
$$

Nested roots:

$$
\sqrt{1 + \sqrt{1 + \sqrt{x}}}
$$

Nested delimiters:

$$
\left[
\left(
\frac{x+1}{x-1}
\right)^2
+
\left\{
\frac{y+1}{y-1}
\right\}^2
\right]
$$

---

## 45. Render Checklist

Use this section after opening the file in Obsidian.

| Feature | Expected result | Works? |
|---|---|---|
| Inline `$...$` | Renders inside text | |
| Block `$$...$$` | Renders centered/display math | |
| Greek letters | Symbols render | |
| Fractions and roots | Proper stacked layout | |
| Matrices | Matrix environments render | |
| Cases | Piecewise layout renders | |
| Aligned equations | Multi-line alignment renders | |
| Tags | Equation tags render | |
| `\newcommand` | Macro works locally | |
| `\ce{}` | Chemistry renders | |
| `\pu{}` | Physical units render | |
| `\chemfig{}` | Likely fails without plugin/extension | |
| `tikzpicture` | Likely fails | |
| `CD` diagrams | May fail | |
| `\cancel{}` | Depends on extension | |
| Colors | Depends on extension/theme | |

---

## 46. Practical Obsidian-Safe Patterns

These are usually safer than full LaTeX environments.

Inline:

```md
Use $x_i \in \mathbb{R}$ inside a sentence.
```

Block:

```md
$$
x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
$$
```

Aligned derivation:

```md
$$
\begin{aligned}
f(x) &= x^2 + 2x + 1 \\
     &= (x+1)^2
\end{aligned}
$$
```

Cases:

```md
$$
f(x)=
\begin{cases}
x^2, & x \ge 0 \\
-x, & x < 0
\end{cases}
$$
```

Matrix:

```md
$$
A =
\begin{bmatrix}
1 & 2 \\
3 & 4
\end{bmatrix}
$$
```

---

## 47. Notes

Obsidian is not a full LaTeX compiler. It renders math notation through MathJax. That means formulas, symbols, matrices, and many equation environments work, but document-level LaTeX, packages, TikZ diagrams, and some extension-specific commands may not.

For reliable notes, prefer:

- `$...$` for inline math.
- `$$...$$` for display math.
- `aligned`, `cases`, `matrix`, `pmatrix`, `bmatrix`, `array`.
- `\operatorname{...}` for named operators.
- `\text{...}` for words inside equations.

Avoid relying on:

- `\documentclass`, `\usepackage`, `\begin{document}`.
- TikZ.
- Full LaTeX package commands.
- Cross-reference workflows such as `\label` and `\ref`, unless you verify them in your own vault.
