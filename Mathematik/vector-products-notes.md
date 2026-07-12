# Vector and Matrix Multiplication Notes

## Table of Contents

- [[#1. Three Common Vector Products|1. Three Common Vector Products]]
- [[#2. Dot Product: Two Vectors Produce One Number|2. Dot Product: Two Vectors Produce One Number]]
- [[#3. Cross Product: Two 3D Vectors Produce a Perpendicular Vector|3. Cross Product: Two 3D Vectors Produce a Perpendicular Vector]]
- [[#4. Outer Product: Two Vectors Produce a Matrix|4. Outer Product: Two Vectors Produce a Matrix]]
- [[#5. Matrix Times Vector: Scale Columns, Then Add|5. Matrix Times Vector: Scale Columns, Then Add]]
- [[#6. Scaling Matrix Columns Separately Without Adding|6. Scaling Matrix Columns Separately Without Adding]]
- [[#7. Matrix Times Matrix: Many Matrix-Vector Multiplications|7. Matrix Times Matrix: Many Matrix-Vector Multiplications]]
- [[#8. Diagonal Matrix Versus Full Matrix|8. Diagonal Matrix Versus Full Matrix]]
- [[#9. Row Scaling Versus Column Scaling|9. Row Scaling Versus Column Scaling]]
- [[#10. Matrix Transpose Products: Comparing One Vector Against Many Vectors|10. Matrix Transpose Products: Comparing One Vector Against Many Vectors]]
- [[#11. The Universal Shape Rule|11. The Universal Shape Rule]]
- [[#12. The Universal Sum Rule|12. The Universal Sum Rule]]
- [[#13. Final Comparison|13. Final Comparison]]
- [[#14. Final Mental Model|14. Final Mental Model]]

---

This note builds the intuition from vectors first, then matrices.

The main idea:

> A vector is a list of numbers.  
> A matrix can be viewed as a group of vectors.  
> Matrix multiplication is a rule for combining those vectors.

We will use these vectors often:

$$
\color{#2563eb}{
a =
\begin{bmatrix}
1 \\
2 \\
3
\end{bmatrix}
}
\qquad
\color{#16a34a}{
b =
\begin{bmatrix}
4 \\
5 \\
6
\end{bmatrix}
}
$$

---

## 1. Three Common Vector Products

There is not only one kind of “vector multiplication.”

With two 3-component vectors, the common products are:

| Product | Expression | Result |
|---|---:|---:|
| Dot product | $a^Tb$ or $a \cdot b$ | scalar |
| Cross product | $a \times b$ | vector |
| Outer product | $ab^T$ | matrix |

Each one means something different.

---

## 2. Dot Product: Two Vectors Produce One Number

The dot product is:

$$
a \cdot b = a_xb_x + a_yb_y + a_zb_z
$$

Using:

$$
a =
\begin{bmatrix}
1 \\
2 \\
3
\end{bmatrix},
\qquad
b =
\begin{bmatrix}
4 \\
5 \\
6
\end{bmatrix}
$$

we get:

$$
a \cdot b
=
1 \cdot 4 + 2 \cdot 5 + 3 \cdot 6
$$

$$
= 4 + 10 + 18
$$

$$
= 32
$$

So:

$$
\boxed{
\color{#dc2626}{
a \cdot b = 32
}
}
$$

The result is one number.

### Intuition

The dot product measures alignment.

$$
a \cdot b = \|a\|\|b\|\cos(\theta)
$$

where $\theta$ is the angle between the vectors.

If:

$$
a \cdot b > 0
$$

the vectors point generally in the same direction.

If:

$$
a \cdot b = 0
$$

the vectors are perpendicular.

If:

$$
a \cdot b < 0
$$

the vectors point generally in opposite directions.

> **Memory hook:**  
> Dot product asks:  
> **How much do these two vectors point in the same direction?**

---

## 3. Cross Product: Two 3D Vectors Produce a Perpendicular Vector

The cross product is:

$$
a \times b =
\begin{bmatrix}
a_yb_z - a_zb_y \\
a_zb_x - a_xb_z \\
a_xb_y - a_yb_x
\end{bmatrix}
$$

Using:

$$
a =
\begin{bmatrix}
1 \\
2 \\
3
\end{bmatrix},
\qquad
b =
\begin{bmatrix}
4 \\
5 \\
6
\end{bmatrix}
$$

we have:

$$
a_x = 1,\quad a_y = 2,\quad a_z = 3
$$

$$
b_x = 4,\quad b_y = 5,\quad b_z = 6
$$

So:

$$
a \times b =
\begin{bmatrix}
2 \cdot 6 - 3 \cdot 5 \\
3 \cdot 4 - 1 \cdot 6 \\
1 \cdot 5 - 2 \cdot 4
\end{bmatrix}
$$

$$
=
\begin{bmatrix}
12 - 15 \\
12 - 6 \\
5 - 8
\end{bmatrix}
$$

$$
=
\begin{bmatrix}
-3 \\
6 \\
-3
\end{bmatrix}
$$

So:

$$
\boxed{
\color{#dc2626}{
a \times b =
\begin{bmatrix}
-3 \\
6 \\
-3
\end{bmatrix}
}
}
$$

### Easy Memory Pattern

The axes rotate like this:

$$
x \rightarrow y \rightarrow z \rightarrow x
$$

The pattern is:

$$
\boxed{
\color{#dc2626}{
x = yz - zy
}
}
$$

$$
\boxed{
\color{#dc2626}{
y = zx - xz
}
}
$$

$$
\boxed{
\color{#dc2626}{
z = xy - yx
}
}
$$

More explicitly:

$$
(a \times b)_x = a_yb_z - a_zb_y
$$

$$
(a \times b)_y = a_zb_x - a_xb_z
$$

$$
(a \times b)_z = a_xb_y - a_yb_x
$$

> **Important:**  
> Order matters.  
> $$
> b \times a = -(a \times b)
> $$

### Intuition

The cross product gives a vector perpendicular to both original vectors.

For our result:

$$
a \times b =
\begin{bmatrix}
-3 \\
6 \\
-3
\end{bmatrix}
$$

Check perpendicularity with dot products:

$$
a \cdot (a \times b)
=
1(-3) + 2(6) + 3(-3)
=
-3 + 12 - 9
=
0
$$

and:

$$
b \cdot (a \times b)
=
4(-3) + 5(6) + 6(-3)
=
-12 + 30 - 18
=
0
$$

Both dot products are zero, so the cross product is perpendicular to both $a$ and $b$.

The length of the cross product is the area of the parallelogram formed by the two vectors:

$$
\|a \times b\| = \|a\|\|b\|\sin(\theta)
$$

For this example:

$$
\|a \times b\|
=
\sqrt{(-3)^2 + 6^2 + (-3)^2}
=
\sqrt{54}
=
3\sqrt{6}
\approx 7.35
$$
![[Cross-product.png]]

> **Memory hook:**  
> Cross product asks:  
> **What perpendicular vector represents the area and orientation between these two vectors?**

---

## 4. Outer Product: Two Vectors Produce a Matrix

The outer product multiplies a column vector by a row vector.

$$
ab^T
$$

Using:

$$
a =
\begin{bmatrix}
1 \\
2 \\
3
\end{bmatrix}
$$

and:

$$
b^T =
\begin{bmatrix}
4 & 5 & 6
\end{bmatrix}
$$

we get:

$$
ab^T =
\begin{bmatrix}
1 \\
2 \\
3
\end{bmatrix}
\begin{bmatrix}
4 & 5 & 6
\end{bmatrix}
$$

$$
=
\begin{bmatrix}
1 \cdot 4 & 1 \cdot 5 & 1 \cdot 6 \\
2 \cdot 4 & 2 \cdot 5 & 2 \cdot 6 \\
3 \cdot 4 & 3 \cdot 5 & 3 \cdot 6
\end{bmatrix}
$$

$$
=
\begin{bmatrix}
4 & 5 & 6 \\
8 & 10 & 12 \\
12 & 15 & 18
\end{bmatrix}
$$

So:

$$
\boxed{
\color{#dc2626}{
ab^T =
\begin{bmatrix}
4 & 5 & 6 \\
8 & 10 & 12 \\
12 & 15 & 18
\end{bmatrix}
}
}
$$

### Intuition

Each row is $b^T$ scaled by one component of $a$.

$$
ab^T =
\begin{bmatrix}
1b^T \\
2b^T \\
3b^T
\end{bmatrix}
$$

> **Memory hook:**  
> Outer product asks:  
> **What matrix do I get by multiplying every component of one vector with every component of another?**

---

# Matrix Multiplication as Groups of Vectors

Now we move from vectors to matrices.

The useful mental model is:

> A matrix is a group of vectors.

For example:

$$
A =
\begin{bmatrix}
1 & 4 \\
2 & 5 \\
3 & 6
\end{bmatrix}
$$

can be read as two column vectors:

$$
A =
\begin{bmatrix}
a_1 & a_2
\end{bmatrix}
$$

where:

$$
a_1 =
\begin{bmatrix}
1 \\
2 \\
3
\end{bmatrix}
\qquad
a_2 =
\begin{bmatrix}
4 \\
5 \\
6
\end{bmatrix}
$$

So:

$$
A =
\begin{bmatrix}
| & | \\
a_1 & a_2 \\
| & |
\end{bmatrix}
$$

This is the model to keep in mind.

---

## 5. Matrix Times Vector: Scale Columns, Then Add

Let:

$$
A =
\begin{bmatrix}
1 & 4 \\
2 & 5 \\
3 & 6
\end{bmatrix}
=
\begin{bmatrix}
a_1 & a_2
\end{bmatrix}
$$

and:

$$
x =
\begin{bmatrix}
3 \\
4
\end{bmatrix}
$$

Then:

$$
Ax =
\begin{bmatrix}
1 & 4 \\
2 & 5 \\
3 & 6
\end{bmatrix}
\begin{bmatrix}
3 \\
4
\end{bmatrix}
$$

The shape is:

$$
(3 \times 2)(2 \times 1) = 3 \times 1
$$

So the result is one 3-component vector.

Calculate:

$$
Ax =
\begin{bmatrix}
1 \cdot 3 + 4 \cdot 4 \\
2 \cdot 3 + 5 \cdot 4 \\
3 \cdot 3 + 6 \cdot 4
\end{bmatrix}
$$

$$
=
\begin{bmatrix}
3 + 16 \\
6 + 20 \\
9 + 24
\end{bmatrix}
$$

$$
=
\begin{bmatrix}
19 \\
26 \\
33
\end{bmatrix}
$$

So:

$$
\boxed{
\color{#dc2626}{
Ax =
\begin{bmatrix}
19 \\
26 \\
33
\end{bmatrix}
}
}
$$

### Vector-Group Intuition

Because:

$$
A =
\begin{bmatrix}
a_1 & a_2
\end{bmatrix}
$$

and:

$$
x =
\begin{bmatrix}
3 \\
4
\end{bmatrix}
$$

we get:

$$
\boxed{
\color{#dc2626}{
Ax = 3a_1 + 4a_2
}
}
$$

That means:

$$
Ax =
3
\begin{bmatrix}
1 \\
2 \\
3
\end{bmatrix}
+
4
\begin{bmatrix}
4 \\
5 \\
6
\end{bmatrix}
$$

$$
=
\begin{bmatrix}
3 \\
6 \\
9
\end{bmatrix}
+
\begin{bmatrix}
16 \\
20 \\
24
\end{bmatrix}
$$

$$
=
\begin{bmatrix}
19 \\
26 \\
33
\end{bmatrix}
$$

> **Important:**  
> Matrix-vector multiplication does not keep the scaled vectors separate.  
> It scales them and then adds them.

So:

$$
A
\begin{bmatrix}
3 \\
4
\end{bmatrix}
=
3a_1 + 4a_2
$$

The output is one vector.

---

## 6. Scaling Matrix Columns Separately Without Adding

Now suppose you want this:

$$
a_1 \text{ multiplied by } 3
$$

and:

$$
a_2 \text{ multiplied by } 4
$$

but you do **not** want to add them.

You want two output vectors:

$$
\begin{bmatrix}
3a_1 & 4a_2
\end{bmatrix}
$$

Using:

$$
a_1 =
\begin{bmatrix}
1 \\
2 \\
3
\end{bmatrix}
\qquad
a_2 =
\begin{bmatrix}
4 \\
5 \\
6
\end{bmatrix}
$$

we get:

$$
3a_1 =
\begin{bmatrix}
3 \\
6 \\
9
\end{bmatrix}
$$

and:

$$
4a_2 =
\begin{bmatrix}
16 \\
20 \\
24
\end{bmatrix}
$$

So the result should be:

$$
\begin{bmatrix}
3a_1 & 4a_2
\end{bmatrix}
=
\begin{bmatrix}
3 & 16 \\
6 & 20 \\
9 & 24
\end{bmatrix}
$$

To express this with matrix multiplication, use a diagonal matrix:

$$
D =
\begin{bmatrix}
3 & 0 \\
0 & 4
\end{bmatrix}
$$

Then:

$$
AD =
\begin{bmatrix}
1 & 4 \\
2 & 5 \\
3 & 6
\end{bmatrix}
\begin{bmatrix}
3 & 0 \\
0 & 4
\end{bmatrix}
$$

$$
=
\begin{bmatrix}
1 \cdot 3 + 4 \cdot 0 & 1 \cdot 0 + 4 \cdot 4 \\
2 \cdot 3 + 5 \cdot 0 & 2 \cdot 0 + 5 \cdot 4 \\
3 \cdot 3 + 6 \cdot 0 & 3 \cdot 0 + 6 \cdot 4
\end{bmatrix}
$$

$$
=
\begin{bmatrix}
3 & 16 \\
6 & 20 \\
9 & 24
\end{bmatrix}
$$

So:

$$
\boxed{
\color{#dc2626}{
AD =
\begin{bmatrix}
3a_1 & 4a_2
\end{bmatrix}
=
\begin{bmatrix}
3 & 16 \\
6 & 20 \\
9 & 24
\end{bmatrix}
}
}
$$

### Why the Diagonal Matrix Works

The diagonal matrix is:

$$
D =
\begin{bmatrix}
3 & 0 \\
0 & 4
\end{bmatrix}
$$

Its first column is:

$$
\begin{bmatrix}
3 \\
0
\end{bmatrix}
$$

So the first output vector is:

$$
3a_1 + 0a_2 = 3a_1
$$

Its second column is:

$$
\begin{bmatrix}
0 \\
4
\end{bmatrix}
$$

So the second output vector is:

$$
0a_1 + 4a_2 = 4a_2
$$

Therefore:

$$
AD =
\begin{bmatrix}
3a_1 & 4a_2
\end{bmatrix}
$$

> **Important distinction:**  
> $$
> A
> \begin{bmatrix}
> 3 \\
> 4
> \end{bmatrix}
> =
> 3a_1 + 4a_2
> $$
>
> This gives one vector.
>
> $$
> A
> \begin{bmatrix}
> 3 & 0 \\
> 0 & 4
> \end{bmatrix}
> =
> \begin{bmatrix}
> 3a_1 & 4a_2
> \end{bmatrix}
> $$
>
> This gives two vectors.

---

## 7. Matrix Times Matrix: Many Matrix-Vector Multiplications

Now suppose both sides are matrices.

Let:

$$
A =
\begin{bmatrix}
1 & 4 \\
2 & 5 \\
3 & 6
\end{bmatrix}
=
\begin{bmatrix}
a_1 & a_2
\end{bmatrix}
$$

and:

$$
B =
\begin{bmatrix}
3 & 10 \\
4 & 20
\end{bmatrix}
$$

Think of $B$ as two instruction vectors:

$$
B =
\begin{bmatrix}
b_1 & b_2
\end{bmatrix}
$$

where:

$$
b_1 =
\begin{bmatrix}
3 \\
4
\end{bmatrix}
\qquad
b_2 =
\begin{bmatrix}
10 \\
20
\end{bmatrix}
$$

Then:

$$
AB =
\begin{bmatrix}
Ab_1 & Ab_2
\end{bmatrix}
$$

That is the core idea:

> Matrix-matrix multiplication means applying the left matrix to every column of the right matrix.

### First Output Column

$$
Ab_1 =
A
\begin{bmatrix}
3 \\
4
\end{bmatrix}
=
3a_1 + 4a_2
$$

We already calculated:

$$
Ab_1 =
\begin{bmatrix}
19 \\
26 \\
33
\end{bmatrix}
$$

### Second Output Column

$$
Ab_2 =
A
\begin{bmatrix}
10 \\
20
\end{bmatrix}
=
10a_1 + 20a_2
$$

Calculate:

$$
10a_1 =
\begin{bmatrix}
10 \\
20 \\
30
\end{bmatrix}
$$

and:

$$
20a_2 =
\begin{bmatrix}
80 \\
100 \\
120
\end{bmatrix}
$$

Then:

$$
Ab_2 =
\begin{bmatrix}
10 \\
20 \\
30
\end{bmatrix}
+
\begin{bmatrix}
80 \\
100 \\
120
\end{bmatrix}
=
\begin{bmatrix}
90 \\
120 \\
150
\end{bmatrix}
$$

Therefore:

$$
AB =
\begin{bmatrix}
Ab_1 & Ab_2
\end{bmatrix}
$$

$$
=
\begin{bmatrix}
19 & 90 \\
26 & 120 \\
33 & 150
\end{bmatrix}
$$

So:

$$
\boxed{
\color{#dc2626}{
AB =
\begin{bmatrix}
19 & 90 \\
26 & 120 \\
33 & 150
\end{bmatrix}
}
}
$$

### Matrix-Group Intuition

Because:

$$
A =
\begin{bmatrix}
a_1 & a_2
\end{bmatrix}
$$

and:

$$
B =
\begin{bmatrix}
3 & 10 \\
4 & 20
\end{bmatrix}
$$

we can read $AB$ as:

$$
AB =
\begin{bmatrix}
3a_1 + 4a_2 & 10a_1 + 20a_2
\end{bmatrix}
$$

So each column of $B$ gives one instruction for mixing the columns of $A$.

> **Memory hook:**  
> The right matrix tells the left matrix how to mix its columns.

---

## 8. Diagonal Matrix Versus Full Matrix

This is the important distinction.

### Diagonal Matrix: Scale Separately

If:

$$
D =
\begin{bmatrix}
3 & 0 \\
0 & 4
\end{bmatrix}
$$

then:

$$
AD =
\begin{bmatrix}
3a_1 & 4a_2
\end{bmatrix}
$$

No mixing happens because the off-diagonal entries are zero.

### Full Matrix: Mix Columns

If:

$$
B =
\begin{bmatrix}
3 & 10 \\
4 & 20
\end{bmatrix}
$$

then:

$$
AB =
\begin{bmatrix}
3a_1 + 4a_2 & 10a_1 + 20a_2
\end{bmatrix}
$$

Mixing happens because the columns of $B$ contain multiple nonzero coefficients.

### General Form

If:

$$
A =
\begin{bmatrix}
a_1 & a_2
\end{bmatrix}
$$

and:

$$
C =
\begin{bmatrix}
c_{11} & c_{12} \\
c_{21} & c_{22}
\end{bmatrix}
$$

then:

$$
AC =
\begin{bmatrix}
c_{11}a_1 + c_{21}a_2
&
c_{12}a_1 + c_{22}a_2
\end{bmatrix}
$$

So every column of $C$ creates one output vector.

---

## 9. Row Scaling Versus Column Scaling

Diagonal matrices can scale rows or columns, depending on which side they are on.

### Diagonal Matrix on the Right: Scales Columns

Let:

$$
A =
\begin{bmatrix}
1 & 4 \\
2 & 5 \\
3 & 6
\end{bmatrix}
$$

and:

$$
D =
\begin{bmatrix}
3 & 0 \\
0 & 4
\end{bmatrix}
$$

Then:

$$
AD =
\begin{bmatrix}
3 & 16 \\
6 & 20 \\
9 & 24
\end{bmatrix}
$$

This scales the columns:

$$
AD =
\begin{bmatrix}
3a_1 & 4a_2
\end{bmatrix}
$$

### Diagonal Matrix on the Left: Scales Rows

Let:

$$
R =
\begin{bmatrix}
10 & 0 & 0 \\
0 & 20 & 0 \\
0 & 0 & 30
\end{bmatrix}
$$

Then:

$$
RA =
\begin{bmatrix}
10 & 0 & 0 \\
0 & 20 & 0 \\
0 & 0 & 30
\end{bmatrix}
\begin{bmatrix}
1 & 4 \\
2 & 5 \\
3 & 6
\end{bmatrix}
$$

$$
=
\begin{bmatrix}
10 & 40 \\
40 & 100 \\
90 & 180
\end{bmatrix}
$$

This scales the rows:

- row 1 by $10$
- row 2 by $20$
- row 3 by $30$

So:

$$
\boxed{
\text{diagonal on the right scales columns}
}
$$

$$
\boxed{
\text{diagonal on the left scales rows}
}
$$

---

## 10. Matrix Transpose Products: Comparing One Vector Against Many Vectors

Now return to another common case.

Suppose we have one vector:

$$
a =
\begin{bmatrix}
1 \\
2 \\
3
\end{bmatrix}
$$

and a matrix $B$ containing two 3-component vectors:

$$
B =
\begin{bmatrix}
4 & 7 \\
5 & 8 \\
6 & 9
\end{bmatrix}
=
\begin{bmatrix}
b_1 & b_2
\end{bmatrix}
$$

where:

$$
b_1 =
\begin{bmatrix}
4 \\
5 \\
6
\end{bmatrix}
\qquad
b_2 =
\begin{bmatrix}
7 \\
8 \\
9
\end{bmatrix}
$$

Now transpose $B$:

$$
B^T =
\begin{bmatrix}
4 & 5 & 6 \\
7 & 8 & 9
\end{bmatrix}
$$

Then:

$$
B^Ta =
\begin{bmatrix}
4 & 5 & 6 \\
7 & 8 & 9
\end{bmatrix}
\begin{bmatrix}
1 \\
2 \\
3
\end{bmatrix}
$$

$$
=
\begin{bmatrix}
4 \cdot 1 + 5 \cdot 2 + 6 \cdot 3 \\
7 \cdot 1 + 8 \cdot 2 + 9 \cdot 3
\end{bmatrix}
$$

$$
=
\begin{bmatrix}
32 \\
50
\end{bmatrix}
$$

So:

$$
\boxed{
\color{#dc2626}{
B^Ta =
\begin{bmatrix}
32 \\
50
\end{bmatrix}
}
}
$$

### Intuition

This result contains dot products:

$$
B^Ta =
\begin{bmatrix}
b_1 \cdot a \\
b_2 \cdot a
\end{bmatrix}
$$

So $B^Ta$ compares $a$ against every vector inside $B$.

> **Memory hook:**  
> $B^Ta$ asks:  
> **How aligned is $a$ with each column vector inside $B$?**

The related row-vector version is:

$$
a^TB =
\begin{bmatrix}
32 & 50
\end{bmatrix}
$$

Same numbers, different orientation:

$$
a^TB = (B^Ta)^T
$$

---

## 11. The Universal Shape Rule

Matrix multiplication is only valid when the inner dimensions match.

If:

$$
A \in \mathbb{R}^{m \times n}
$$

and:

$$
B \in \mathbb{R}^{n \times p}
$$

then:

$$
AB \in \mathbb{R}^{m \times p}
$$

In short:

$$
\boxed{
\color{#dc2626}{
(m \times n)(n \times p) = (m \times p)
}
}
$$

The inside dimensions must match:

$$
n = n
$$

The outside dimensions become the result:

$$
m \times p
$$

### Examples

Matrix times vector:

$$
(3 \times 2)(2 \times 1) = (3 \times 1)
$$

Matrix times matrix:

$$
(3 \times 2)(2 \times 2) = (3 \times 2)
$$

Row vector times column vector:

$$
(1 \times 3)(3 \times 1) = (1 \times 1)
$$

Column vector times row vector:

$$
(3 \times 1)(1 \times 3) = (3 \times 3)
$$

Invalid product:

$$
(3 \times 1)(3 \times 1)
$$

because:

$$
1 \neq 3
$$

So two column vectors cannot be directly multiplied using ordinary matrix multiplication unless one of them is transposed.

---

## 12. The Universal Sum Rule

Every entry of a matrix product is a sum of multiplications.

If:

$$
C = AB
$$

then:

$$
\boxed{
\color{#dc2626}{
C_{ij}
=
\sum_{k=1}^{n} A_{ik}B_{kj}
}
}
$$

This means:

> Entry $(i,j)$ of the result equals row $i$ of $A$ dotted with column $j$ of $B$.

So matrix multiplication is always:

$$
\text{row from left matrix}
\quad
\cdot
\quad
\text{column from right matrix}
$$

with:

$$
\text{multiply matching entries, then add}
$$

### Example

Let:

$$
A =
\begin{bmatrix}
1 & 4 \\
2 & 5 \\
3 & 6
\end{bmatrix}
$$

and:

$$
B =
\begin{bmatrix}
3 & 10 \\
4 & 20
\end{bmatrix}
$$

Then:

$$
AB =
\begin{bmatrix}
1 & 4 \\
2 & 5 \\
3 & 6
\end{bmatrix}
\begin{bmatrix}
3 & 10 \\
4 & 20
\end{bmatrix}
$$

The first entry is:

$$
(AB)_{11}
=
1 \cdot 3 + 4 \cdot 4
=
3 + 16
=
19
$$

The second entry in the first row is:

$$
(AB)_{12}
=
1 \cdot 10 + 4 \cdot 20
=
10 + 80
=
90
$$

The whole result is:

$$
AB =
\begin{bmatrix}
19 & 90 \\
26 & 120 \\
33 & 150
\end{bmatrix}
$$

### Why This Also Explains Vectors

A vector is just a special matrix.

A column vector has shape:

$$
n \times 1
$$

A row vector has shape:

$$
1 \times n
$$

So the same rule applies.

Dot product:

$$
a^Tb
=
(1 \times 3)(3 \times 1)
=
1 \times 1
$$

Outer product:

$$
ab^T
=
(3 \times 1)(1 \times 3)
=
3 \times 3
$$

Matrix-vector product:

$$
Ax
=
(3 \times 2)(2 \times 1)
=
3 \times 1
$$

Matrix-matrix product:

$$
AB
=
(3 \times 2)(2 \times 2)
=
3 \times 2
$$

> **Important:**  
> The same multiplication rule works for vectors and matrices.  
> Vectors are just matrices with either one row or one column.

---

## 13. Final Comparison

| Operation | Expression | Result | Intuition |
|---|---:|---:|---|
| Dot product | $a^Tb$ | scalar | compare two vectors |
| Cross product | $a \times b$ | vector | perpendicular vector and area |
| Outer product | $ab^T$ | matrix | all pairwise component products |
| Matrix-vector product | $Ax$ | vector | scale columns, then add |
| Separate column scaling | $AD$ where $D$ is diagonal | matrix | scale columns without adding |
| Matrix-matrix product | $AB$ | matrix | many matrix-vector products |
| Transposed matrix times vector | $B^Ta$ | vector | compare one vector against many vectors |
| Left diagonal multiplication | $RA$ | matrix | scale rows |

---

## 14. Final Mental Model

Think of a matrix as a group of vectors:

$$
A =
\begin{bmatrix}
a_1 & a_2
\end{bmatrix}
$$

Then:

$$
A
\begin{bmatrix}
3 \\
4
\end{bmatrix}
=
3a_1 + 4a_2
$$

This scales and adds, giving one vector.

But:

$$
A
\begin{bmatrix}
3 & 0 \\
0 & 4
\end{bmatrix}
=
\begin{bmatrix}
3a_1 & 4a_2
\end{bmatrix}
$$

This scales columns separately, giving two vectors.

And:

$$
A
\begin{bmatrix}
3 & 10 \\
4 & 20
\end{bmatrix}
=
\begin{bmatrix}
3a_1 + 4a_2 & 10a_1 + 20a_2
\end{bmatrix}
$$

This creates multiple mixed output vectors.

The right side tells the left matrix how to combine its columns.

The universal rule is:

$$
\boxed{
\color{#dc2626}{
(m \times n)(n \times p) = (m \times p)
}
}
$$

and each output entry is:

$$
\boxed{
\color{#dc2626}{
C_{ij}
=
\sum_{k=1}^{n} A_{ik}B_{kj}
}
}
$$

In plain words:

> Take a row from the left.  
> Take a column from the right.  
> Multiply matching numbers.  
> Add them.  
> That gives one cell of the result.
