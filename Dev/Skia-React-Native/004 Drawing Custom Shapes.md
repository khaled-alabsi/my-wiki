### **4. Drawing Custom Shapes with Paths and Polygons in Skia**

The `Path` component in Skia allows you to create complex shapes and custom designs, such as polygons, curves, and free-form drawings. Unlike primitive shapes like `Circle` or `Rect`, a `Path` gives you full control over the drawing process.

---

### **Key Concepts for Paths**

1. **Path Creation**:
   - Use `Skia.Path.Make()` to initialize a path.
   - Add drawing commands (e.g., `moveTo`, `lineTo`, `arcTo`) to define the path.

2. **Path Commands**:
   - `moveTo(x, y)`: Moves the cursor to a new position without drawing.
   - `lineTo(x, y)`: Draws a straight line from the current position to `(x, y)`.
   - `arcTo(x1, y1, x2, y2, radius)`: Draws an arc between two points.
   - `close()`: Closes the current subpath, connecting the last point to the starting point.

3. **Fill and Stroke**:
   - Use the `style` property to define whether the path is filled or stroked.
   - Combine with `strokeWidth` to customize outlines.

---

### **Examples**

#### **1. Basic Path (Triangle)**
Create a simple triangle using `moveTo` and `lineTo`.

```tsx
import { Skia, Path, Canvas } from '@shopify/react-native-skia';

const trianglePath = Skia.Path.Make();
trianglePath.moveTo(100, 50);  // Move to the top vertex
trianglePath.lineTo(50, 150); // Draw a line to the bottom-left vertex
trianglePath.lineTo(150, 150); // Draw a line to the bottom-right vertex
trianglePath.close();         // Close the path (connect back to the top)

<Canvas style={{ flex: 1 }}>
  <Path path={trianglePath} color="blue" style="fill" />
</Canvas>
```

---

#### **2. Polygon**
Create a pentagon by calculating the vertices programmatically.

```tsx
const createPolygonPath = (cx, cy, radius, sides) => {
  const path = Skia.Path.Make();
  const angleStep = (2 * Math.PI) / sides;

  for (let i = 0; i < sides; i++) {
    const x = cx + radius * Math.cos(i * angleStep);
    const y = cy + radius * Math.sin(i * angleStep);
    if (i === 0) {
      path.moveTo(x, y);
    } else {
      path.lineTo(x, y);
    }
  }

  path.close();
  return path;
};

const pentagonPath = createPolygonPath(150, 150, 100, 5);

<Canvas style={{ flex: 1 }}>
  <Path path={pentagonPath} color="green" style="fill" />
</Canvas>
```

---

#### **3. Curved Path**
Draw a path with curves using `arcTo` or `quadTo` (quadratic curves).

```tsx
const curvedPath = Skia.Path.Make();
curvedPath.moveTo(50, 50);     // Start point
curvedPath.arcTo(50, 50, 150, 150, 100); // Arc between two points
curvedPath.lineTo(200, 50);   // Straight line

<Canvas style={{ flex: 1 }}>
  <Path path={curvedPath} color="red" style="stroke" strokeWidth={5} />
</Canvas>
```

---

#### **4. Combining Shapes in a Path**
Paths allow you to combine multiple sub-shapes.

```tsx
const combinedPath = Skia.Path.Make();
combinedPath.addCircle(100, 100, 50); // Add a circle
combinedPath.addRect(150, 50, 100, 100); // Add a rectangle

<Canvas style={{ flex: 1 }}>
  <Path path={combinedPath} color="purple" style="fill" />
</Canvas>
```

---

#### **5. Free-Form Drawing**
Allow users to draw custom shapes with gestures.

```tsx
import { useState } from 'react';
import { Canvas, Path, Skia } from '@shopify/react-native-skia';
import { PanResponder } from 'react-native';

const FreeFormDrawing = () => {
  const [path, setPath] = useState(() => Skia.Path.Make());

  const panResponder = PanResponder.create({
    onStartShouldSetPanResponder: () => true,
    onPanResponderMove: (e, gestureState) => {
      path.lineTo(gestureState.moveX, gestureState.moveY);
      setPath(path.copy());
    },
  });

  return (
    <Canvas style={{ flex: 1 }} {...panResponder.panHandlers}>
      <Path path={path} color="black" style="stroke" strokeWidth={2} />
    </Canvas>
  );
};
```

---

### **Advanced Features**

1. **Path Transformations**:
   - You can apply scaling, rotation, or translation to a path.
   - Example:
     ```tsx
     path.transform([{ rotate: Math.PI / 4 }, { translateX: 50 }]);
     ```

2. **Clipping**:
   - Use a path as a clipping region to constrain drawing.
   - Example:
     ```tsx
     canvas.clipPath(path);
     ```

3. **Path Effects**:
   - Add effects like dashed lines to a path.
   - Example:
     ```tsx
     const paint = Skia.Paint();
     paint.setPathEffect(Skia.PathEffect.MakeDash([10, 5], 0));
     ```

---

### **Applications for TradeChampion**

1. **Custom Graphs**:
   - Use paths to create custom charts like trend lines or candlesticks.
   - Add interactivity with gestures.

2. **Polygons for Portfolio Visualization**:
   - Represent asset distribution using polygons with areas proportional to investment.

3. **Interactive Drawing Features**:
   - Enable users to annotate graphs or highlight news on the fly.

---
### **Working with Bézier Curves in Skia**

Bézier curves are essential for creating smooth and precise curves in graphics. Skia provides tools for both **quadratic** and **cubic Bézier curves**, allowing for a wide range of custom shapes.

---

### **Key Types of Bézier Curves**

1. **Quadratic Bézier Curve** (`quadTo`):
   - Defined by three points:
     - **Start Point (implicit)**: The current position of the path.
     - **Control Point**: The point that determines the curve's "pull."
     - **End Point**: The final point of the curve.

2. **Cubic Bézier Curve** (`cubicTo`):
   - Defined by four points:
     - **Start Point (implicit)**: The current position of the path.
     - **Control Point 1**: Influences the curve's start.
     - **Control Point 2**: Influences the curve's end.
     - **End Point**: The final point of the curve.

---

### **Quadratic Bézier Curve**

#### **Syntax**:
```tsx
path.quadTo(controlX, controlY, endX, endY);
```

#### **Example: Drawing a Single Quadratic Bézier Curve**:
```tsx
import { Skia, Path, Canvas } from '@shopify/react-native-skia';

const path = Skia.Path.Make();
path.moveTo(50, 150);       // Start point
path.quadTo(150, 50, 250, 150); // Control point (150, 50), End point (250, 150)

<Canvas style={{ flex: 1 }}>
  <Path path={path} color="blue" style="stroke" strokeWidth={3} />
</Canvas>
```

- The curve starts at `(50, 150)`, bends towards `(150, 50)`, and ends at `(250, 150)`.

---

### **Cubic Bézier Curve**

#### **Syntax**:
```tsx
path.cubicTo(control1X, control1Y, control2X, control2Y, endX, endY);
```

#### **Example: Drawing a Single Cubic Bézier Curve**:
```tsx
const path = Skia.Path.Make();
path.moveTo(50, 150);       // Start point
path.cubicTo(100, 50, 200, 250, 300, 150); // Control points and end point

<Canvas style={{ flex: 1 }}>
  <Path path={path} color="red" style="stroke" strokeWidth={3} />
</Canvas>
```

- The curve starts at `(50, 150)`, pulls towards `(100, 50)` and `(200, 250)`, and ends at `(300, 150)`.

---

### **Visualizing Bézier Curves with Control Points**

To better understand Bézier curves, draw lines to visualize the control points.

#### **Example: Quadratic Curve with Control Points**:
```tsx
const path = Skia.Path.Make();
path.moveTo(50, 150);
path.quadTo(150, 50, 250, 150);

<Canvas style={{ flex: 1 }}>
  <Path path={path} color="blue" style="stroke" strokeWidth={3} />
  {/* Visualize Control Points */}
  <Line p1={{ x: 50, y: 150 }} p2={{ x: 150, y: 50 }} color="gray" strokeWidth={1} />
  <Line p1={{ x: 150, y: 50 }} p2={{ x: 250, y: 150 }} color="gray" strokeWidth={1} />
</Canvas>
```

---

#### **Example: Cubic Curve with Control Points**:
```tsx
const path = Skia.Path.Make();
path.moveTo(50, 150);
path.cubicTo(100, 50, 200, 250, 300, 150);

<Canvas style={{ flex: 1 }}>
  <Path path={path} color="red" style="stroke" strokeWidth={3} />
  {/* Visualize Control Points */}
  <Line p1={{ x: 50, y: 150 }} p2={{ x: 100, y: 50 }} color="gray" strokeWidth={1} />
  <Line p1={{ x: 200, y: 250 }} p2={{ x: 300, y: 150 }} color="gray" strokeWidth={1} />
</Canvas>
```

---

### **Animating Bézier Curves**

You can animate the control points or endpoints to create dynamic curves.

#### **Example: Animated Quadratic Curve**:
```tsx
import { useValue, runTiming, Easing } from '@shopify/react-native-skia';

const AnimatedCurve = () => {
  const controlX = useValue(150);
  const controlY = useValue(50);

  useEffect(() => {
    runTiming(controlX, 200, { duration: 2000, easing: Easing.inOut(Easing.cubic) });
    runTiming(controlY, 100, { duration: 2000, easing: Easing.inOut(Easing.cubic) });
  }, []);

  const path = Skia.Path.Make();
  path.moveTo(50, 150);
  path.quadTo(controlX.current, controlY.current, 250, 150);

  return (
    <Canvas style={{ flex: 1 }}>
      <Path path={path} color="blue" style="stroke" strokeWidth={3} />
    </Canvas>
  );
};
```

- The control point `(150, 50)` animates to `(200, 100)`.

---

### **Combining Multiple Bézier Curves**

You can chain multiple Bézier curves to create complex shapes.

#### **Example**:
```tsx
const path = Skia.Path.Make();
path.moveTo(50, 150);
path.quadTo(150, 50, 250, 150); // First curve
path.cubicTo(300, 50, 400, 250, 450, 150); // Second curve

<Canvas style={{ flex: 1 }}>
  <Path path={path} color="purple" style="stroke" strokeWidth={3} />
</Canvas>
```

---

### **Applications for TradeChampion**

1. **Custom Graphs**:
   - Use Bézier curves to create smooth trend lines or curved connections between data points.
2. **Interactive Features**:
   - Enable users to draw curved annotations on charts using gestures.
3. **Advanced Visuals**:
   - Add animations to curves to show dynamic stock trends or portfolio performance.

---

Creating a chart for viewing stock data over time using Skia is a powerful approach, as it allows for highly customizable and performant visualizations. You can use Skia’s `Path` and `Canvas` components to draw the chart manually or consider third-party tools built on Skia for ease of implementation. Here’s how to decide and proceed:

---

### **1. Custom Chart Using Skia**
If you want full control over the design, Skia provides the necessary primitives (`Path`, `Line`, `Circle`, etc.) to build stock charts like line graphs, candlestick charts, or bar charts.

#### **Steps to Build a Line Chart with Skia**
1. **Prepare the Data**:
   Ensure stock data is available in a format like:
   ```tsx
   const stockData = [
     { time: 1, value: 100 },
     { time: 2, value: 120 },
     { time: 3, value: 115 },
     { time: 4, value: 130 },
     { time: 5, value: 125 },
   ];
   ```

2. **Normalize the Data**:
   Map the data points to the chart’s coordinate space.

   ```tsx
   const normalizeData = (data, width, height) => {
     const maxX = Math.max(...data.map((d) => d.time));
     const maxY = Math.max(...data.map((d) => d.value));
     return data.map((d) => ({
       x: (d.time / maxX) * width,
       y: height - (d.value / maxY) * height, // Flip y-axis
     }));
   };

   const chartWidth = 300;
   const chartHeight = 200;
   const normalizedData = normalizeData(stockData, chartWidth, chartHeight);
   ```

3. **Draw the Chart**:
   Use a `Path` for the line graph.

   ```tsx
   import { Skia, Path, Canvas } from '@shopify/react-native-skia';

   const path = Skia.Path.Make();
   normalizedData.forEach((point, index) => {
     if (index === 0) {
       path.moveTo(point.x, point.y);
     } else {
       path.lineTo(point.x, point.y);
     }
   });

   <Canvas style={{ width: chartWidth, height: chartHeight }}>
     <Path path={path} color="blue" style="stroke" strokeWidth={2} />
   </Canvas>
   ```

4. **Add Axes and Points**:
   - Use `Line` for axes.
   - Use `Circle` for data points.

   ```tsx
   import { Line, Circle } from '@shopify/react-native-skia';

   <Canvas style={{ width: chartWidth, height: chartHeight }}>
     {/* Axes */}
     <Line p1={{ x: 0, y: chartHeight }} p2={{ x: chartWidth, y: chartHeight }} color="black" />
     <Line p1={{ x: 0, y: 0 }} p2={{ x: 0, y: chartHeight }} color="black" />

     {/* Chart Line */}
     <Path path={path} color="blue" style="stroke" strokeWidth={2} />

     {/* Data Points */}
     {normalizedData.map((point, index) => (
       <Circle key={index} cx={point.x} cy={point.y} r={3} color="red" />
     ))}
   </Canvas>
   ```

---

### **2. Using Skia Libraries for Charts**

If you want pre-built functionality but still leverage Skia, consider:
- **`react-native-skia-charts` (if available)**:
  - A library built on top of Skia for creating charts.
  - Simplifies chart rendering with pre-built components like `LineChart`, `BarChart`, etc.
- **`react-native-chart-kit`**:
  - While not built on Skia, this is another popular charting library for React Native.

---

### **3. Should You Use Another Tool?**

If your primary goal is speed and ease of development, libraries like `react-native-chart-kit` or `victory-native` might be better options because:
- They provide higher-level abstractions for charts.
- They support interactivity (e.g., tooltips) out of the box.

However, **Skia is preferable if you need**:
- Highly customized visuals.
- Optimized performance for animations or real-time updates.
- Integration with other Skia elements (e.g., shaders or advanced blending).

---

### **Example Applications for Stock Chart in TradeChampion**

1. **Dynamic Line Chart**:
   - Show price trends over time.
   - Add animations for line updates using Skia’s `runTiming`.

2. **Interactive Candlestick Chart**:
   - Combine `Rect` for body and `Line` for wicks.
   - Allow gestures to explore specific time periods.

3. **Portfolio Heatmap**:
   - Use a grid of `Rect` with colors representing performance.

---
