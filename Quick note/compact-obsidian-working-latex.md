# Compact Obsidian LaTeX That Works

Use this as a quick double-check sheet for the LaTeX / MathJax syntax that rendered correctly in your Obsidian setup.

---

## 1. Inline Math

Inline formula: $E = mc^2$

Inline fraction: $\frac{a+b}{c+d}$

Inline root: $\sqrt{x^2 + y^2}$

Inline Greek letters: $\alpha, \beta, \gamma, \theta, \lambda, \pi, \sigma, \omega$

Inline superscript/subscript: $x_i^2 + y_{n+1}^{k-1}$

Inline set notation: $x \in \mathbb{R}$

Inline logic: $P \Rightarrow Q$

---

## 2. Block Math

$$
E = mc^2
$$

$$
x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
$$

$$
e^{i\pi} + 1 = 0
$$

---

## 3. Fractions, Roots, Powers

$$
\frac{x^2 + 2x + 1}{x - 1}
$$

$$
\sqrt{x^2 + y^2}
$$

$$
\sqrt[n]{x}
$$

$$
x_i^j,\quad x_{i+1}^{j-1}
$$

---

## 4. Greek Letters and Common Symbols

$$
\alpha \beta \gamma \delta \epsilon \theta \lambda \mu \pi \rho \sigma \phi \omega
$$

$$
\Gamma \Delta \Theta \Lambda \Pi \Sigma \Phi \Omega
$$

$$
\infty,\quad \partial,\quad \nabla,\quad \emptyset
$$

$$
\mathbb{N},\quad \mathbb{Z},\quad \mathbb{Q},\quad \mathbb{R},\quad \mathbb{C}
$$

---

## 5. Operators and Relations

$$
a + b - c \times d \div e \cdot f
$$

$$
a \ne b,\quad a \le b,\quad a \ge b,\quad a \approx b,\quad a \equiv b
$$

$$
P \land Q,\quad P \lor Q,\quad \neg P,\quad P \Rightarrow Q,\quad P \Leftrightarrow Q
$$

$$
\forall x \in X,\quad \exists y \in Y
$$

---

## 6. Sets

$$
A \subseteq B,\quad A \cup B,\quad A \cap B,\quad A \setminus B
$$

$$
\{x \in \mathbb{R} \mid x > 0\}
$$

$$
\left\{ x \in \mathbb{R} : x^2 < 1 \right\}
$$

---

## 7. Arrows

$$
a \to b,\quad a \leftarrow b,\quad a \mapsto b
$$

$$
A \longrightarrow B,\quad A \Longrightarrow B
$$

$$
P \Rightarrow Q,\quad P \Leftrightarrow Q
$$

---

## 8. Calculus

$$
\frac{dy}{dx}
$$

$$
\frac{\partial f}{\partial x}
$$

$$
\lim_{x \to 0} \frac{\sin x}{x} = 1
$$

$$
\int_a^b f(x)\,dx
$$

$$
\sum_{i=1}^{n} i = \frac{n(n+1)}{2}
$$

$$
\prod_{i=1}^{n} i = n!
$$

---

## 9. Brackets and Delimiters

$$
\left( \frac{a+b}{c+d} \right)
$$

$$
\left[ \frac{a+b}{c+d} \right]
$$

$$
\left\{ \frac{a+b}{c+d} \right\}
$$

$$
\langle x, y \rangle
$$

$$
\left\lVert x \right\rVert_2
$$

$$
\left| \frac{x}{y} \right|
$$

---

## 10. Matrices

$$
A =
\begin{bmatrix}
1 & 2 \\
3 & 4
\end{bmatrix}
$$

$$
B =
\begin{pmatrix}
a & b \\
c & d
\end{pmatrix}
$$

$$
\det(A) =
\begin{vmatrix}
a & b \\
c & d
\end{vmatrix}
= ad - bc
$$

$$
\begin{bmatrix}
a_{11} & a_{12} & \cdots & a_{1n} \\
a_{21} & a_{22} & \cdots & a_{2n} \\
\vdots & \vdots & \ddots & \vdots \\
a_{m1} & a_{m2} & \cdots & a_{mn}
\end{bmatrix}
$$

---

## 11. Cases

$$
f(x) =
\begin{cases}
x^2, & x \ge 0 \\
-x, & x < 0
\end{cases}
$$

$$
P(X=x) =
\begin{cases}
p, & x=1 \\
1-p, & x=0 \\
0, & \text{otherwise}
\end{cases}
$$

---

## 12. Aligned Equations

$$
\begin{aligned}
(a+b)^2 &= (a+b)(a+b) \\
&= a^2 + 2ab + b^2
\end{aligned}
$$

$$
\begin{aligned}
\frac{d}{dx}x^n
&= n x^{n-1}
\end{aligned}
$$

---

## 13. Text Inside Math

$$
f(x) = 0 \quad \text{for all } x < 0
$$

$$
P(X=x) = 0 \quad \text{otherwise}
$$

---

## 14. Named Operators

$$
\sin x,\quad \cos x,\quad \tan x
$$

$$
\log x,\quad \ln x,\quad \exp x
$$

$$
\operatorname{softmax}(z)_i =
\frac{e^{z_i}}{\sum_{j=1}^{K} e^{z_j}}
$$

$$
\operatorname{Var}(X) = \mathbb{E}[X^2] - \mathbb{E}[X]^2
$$

---

## 15. Probability and Statistics

$$
P(A \mid B) = \frac{P(B \mid A)P(A)}{P(B)}
$$

$$
\mathbb{E}[X] = \sum_x xP(X=x)
$$

$$
X \sim \mathcal{N}(\mu, \sigma^2)
$$

$$
D_{\mathrm{KL}}(P \parallel Q)
=
\sum_x P(x)\log\frac{P(x)}{Q(x)}
$$

---

## 16. Linear Algebra

$$
\mathbf{x} =
\begin{bmatrix}
x_1 \\
x_2 \\
x_3
\end{bmatrix}
$$

$$
\mathbf{x}^\top \mathbf{y}
=
\sum_{i=1}^{n} x_i y_i
$$

$$
A\mathbf{v} = \lambda \mathbf{v}
$$

$$
A^{-1}A = I
$$

---

## 17. Machine Learning

$$
\mathcal{L}(\theta)
=
-\sum_{i=1}^{n} y_i \log \hat{y}_i
$$

$$
\theta_{t+1}
=
\theta_t - \eta \nabla_\theta \mathcal{L}(\theta_t)
$$

$$
\operatorname{Attention}(Q,K,V)
=
\operatorname{softmax}
\left(
\frac{QK^\top}{\sqrt{d_k}}
\right)V
$$

---

## 18. Chemistry With `mhchem`

Water:

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

Isotope:

$$
\ce{^{14}C}
$$

---

## 19. Colors

$$
\color{red}{x + y}
$$

$$
{\color{blue} A} + {\color{green} B}
$$

$$
\color{purple}{\frac{x^2 + 1}{x - 1}}
$$

---

## 20. Callout With Math

> [!note]
> Inline math inside callout: $E = mc^2$
>
> $$
> \int_0^1 x^2\,dx = \frac{1}{3}
> $$

> [!tip]
> Colored math inside callout:
>
> $$
> \color{blue}{a^2 + b^2 = c^2}
> $$

---

## 21. Practical Templates

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

Aligned:

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

Chemistry:

```md
$$
\ce{2H2 + O2 -> 2H2O}
$$
```

Color:

```md
$$
\color{red}{x + y}
$$
```

Callout:

```md
> [!note]
> $$
> E = mc^2
> $$
```

---

## 22. Avoid in Obsidian

These did not work or are not reliable in your setup:

```latex
\chemfig{...}
```

```latex
\begin{tikzpicture}
...
\end{tikzpicture}
```

```latex
\documentclass{article}
\begin{document}
...
\end{document}
```

```latex
\usepackage{...}
```
