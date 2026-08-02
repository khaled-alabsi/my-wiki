### **5. Adding Animations in Skia**
Animations in Skia are simple and highly efficient, as they bypass React Native’s layout engine and directly modify properties at the GPU level. Skia provides hooks like `useValue` and `runTiming` for declarative and smooth animations.

---

### **Key Concepts**

1. **`useValue`**:
   - A hook for defining animated values.
   - Acts like a `useState` for Skia, but optimized for performance.
   - Example:
     ```tsx
     const radius = useValue(50); // Initialize the radius
     ```

2. **`runTiming`**:
   - Animates a value over time using easing functions.
   - Example:
     ```tsx
     useEffect(() => {
       runTiming(radius, 100, { duration: 2000, easing: Easing.inOut(Easing.cubic) });
     }, []);
     ```

3. **Easing**:
   - Functions that define how the animation progresses.
   - Common easing functions: `linear`, `cubic`, `bounce`, `elastic`.

---

### **Examples**

#### **1. Simple Circle Animation (Radius)**
Animate the radius of a circle.

```tsx
import React, { useEffect } from 'react';
import { Canvas, Circle, useValue, runTiming, Easing } from '@shopify/react-native-skia';

const AnimatedCircle = () => {
  const radius = useValue(50); // Initialize animated value

  useEffect(() => {
    runTiming(radius, 100, { duration: 2000, easing: Easing.inOut(Easing.cubic) });
  }, []);

  return (
    <Canvas style={{ flex: 1 }}>
      <Circle cx={150} cy={150} r={radius} color="blue" />
    </Canvas>
  );
};

export default AnimatedCircle;
```

- **Result**: The circle’s radius animates from 50 to 100 over 2 seconds.

---

#### **2. Line Chart Animation**
Animate the drawing of a line graph.

```tsx
import React, { useEffect } from 'react';
import { Skia, Path, Canvas, useValue, runTiming, Easing } from '@shopify/react-native-skia';

const AnimatedLineChart = () => {
  const progress = useValue(0); // Progress of the line (0 to 1)
  
  const stockData = [
    { x: 50, y: 200 },
    { x: 100, y: 150 },
    { x: 150, y: 180 },
    { x: 200, y: 120 },
    { x: 250, y: 170 },
  ];
  
  const path = Skia.Path.Make();
  stockData.forEach((point, index) => {
    if (index === 0) {
      path.moveTo(point.x, point.y);
    } else {
      path.lineTo(point.x, point.y);
    }
  });

  useEffect(() => {
    runTiming(progress, 1, { duration: 2000, easing: Easing.inOut(Easing.cubic) });
  }, []);

  return (
    <Canvas style={{ flex: 1 }}>
      <Path path={path} color="blue" style="stroke" strokeWidth={2} progress={progress} />
    </Canvas>
  );
};

export default AnimatedLineChart;
```

- **Key Feature**: The `progress` property animates the path drawing.

---

#### **3. Multi-Property Animation**
Animate both position and size of a rectangle.

```tsx
import React, { useEffect } from 'react';
import { Canvas, Rect, useValue, runTiming, Easing } from '@shopify/react-native-skia';

const AnimatedRect = () => {
  const rectX = useValue(50);
  const rectWidth = useValue(100);

  useEffect(() => {
    runTiming(rectX, 200, { duration: 1500, easing: Easing.bounce });
    runTiming(rectWidth, 200, { duration: 1500, easing: Easing.inOut(Easing.cubic) });
  }, []);

  return (
    <Canvas style={{ flex: 1 }}>
      <Rect x={rectX} y={100} width={rectWidth} height={50} color="red" />
    </Canvas>
  );
};

export default AnimatedRect;
```

- **Result**: The rectangle moves from `x=50` to `x=200` and its width increases from `100` to `200`.

---

#### **4. Animated Bézier Curve**
Use `runTiming` to animate control points of a Bézier curve.

```tsx
import React, { useEffect } from 'react';
import { Skia, Path, Canvas, useValue, runTiming, Easing } from '@shopify/react-native-skia';

const AnimatedBezier = () => {
  const controlX = useValue(100);
  const controlY = useValue(50);

  useEffect(() => {
    runTiming(controlX, 200, { duration: 2000, easing: Easing.inOut(Easing.cubic) });
    runTiming(controlY, 150, { duration: 2000, easing: Easing.inOut(Easing.cubic) });
  }, []);

  const path = Skia.Path.Make();
  path.moveTo(50, 150); // Start point
  path.quadTo(controlX.current, controlY.current, 250, 150); // Quadratic curve

  return (
    <Canvas style={{ flex: 1 }}>
      <Path path={path} color="green" style="stroke" strokeWidth={3} />
    </Canvas>
  );
};

export default AnimatedBezier;
```

- **Result**: The Bézier curve's control point animates smoothly.

---

### **Easing Functions**

Use `Easing` to control the animation’s progression:
- `Easing.linear`: Uniform motion.
- `Easing.inOut(Easing.cubic)`: Smooth acceleration and deceleration.
- `Easing.bounce`: Adds a bounce effect at the end.
- `Easing.elastic(1)`: Creates an elastic spring effect.

---

### **Applications for TradeChampion**

1. **Animated Stock Charts**:
   - Animate the drawing of stock price trends over time.
   - Highlight significant data points with pulsating circles or bouncing markers.

2. **Portfolio Visualization**:
   - Animate portfolio growth with bar charts or radial graphs.

3. **Interactive News Visuals**:
   - Add animations to highlight key stories or trends.

---

### **Dynamic Shape Transformations in Skia**

Dynamic shape transformations involve modifying properties like **position**, **scale**, **rotation**, and **opacity** of shapes in real time. Skia provides hooks and components to enable smooth, dynamic transformations.

---

### **Key Transformations**

1. **Translation**: Move a shape across the canvas.
2. **Rotation**: Rotate a shape around its center or a specific pivot point.
3. **Scaling**: Increase or decrease the size of a shape.
4. **Opacity**: Change the transparency of a shape.

---

### **1. Translation (Movement)**

#### **Example: Move a Circle Horizontally**
```tsx
import React, { useEffect } from 'react';
import { Canvas, Circle, useValue, runTiming, Easing } from '@shopify/react-native-skia';

const MovingCircle = () => {
  const x = useValue(50); // Initial x-coordinate

  useEffect(() => {
    runTiming(x, 250, { duration: 2000, easing: Easing.inOut(Easing.cubic) });
  }, []);

  return (
    <Canvas style={{ flex: 1 }}>
      <Circle cx={x} cy={150} r={50} color="blue" />
    </Canvas>
  );
};

export default MovingCircle;
```

- **Result**: The circle moves horizontally from `x=50` to `x=250`.

---

### **2. Rotation**

#### **Example: Rotate a Rectangle**
```tsx
import React, { useEffect } from 'react';
import { Canvas, Rect, Group, useValue, runTiming, Easing } from '@shopify/react-native-skia';

const RotatingRect = () => {
  const rotation = useValue(0); // Initial rotation angle in radians

  useEffect(() => {
    runTiming(rotation, Math.PI * 2, { duration: 3000, easing: Easing.inOut(Easing.cubic) });
  }, []);

  return (
    <Canvas style={{ flex: 1 }}>
      <Group transform={[{ rotate: rotation }, { translateX: 100, translateY: 100 }]}>
        <Rect x={-50} y={-25} width={100} height={50} color="green" />
      </Group>
    </Canvas>
  );
};

export default RotatingRect;
```

- **Result**: The rectangle rotates 360° around its center.

---

### **3. Scaling**

#### **Example: Scale a Shape Dynamically**
```tsx
import React, { useEffect } from 'react';
import { Canvas, Circle, Group, useValue, runTiming, Easing } from '@shopify/react-native-skia';

const ScalingCircle = () => {
  const scale = useValue(1); // Initial scale

  useEffect(() => {
    runTiming(scale, 2, { duration: 2000, easing: Easing.inOut(Easing.cubic) });
  }, []);

  return (
    <Canvas style={{ flex: 1 }}>
      <Group transform={[{ scale }]}>
        <Circle cx={150} cy={150} r={50} color="red" />
      </Group>
    </Canvas>
  );
};

export default ScalingCircle;
```

- **Result**: The circle grows to twice its original size.

---

### **4. Opacity**

#### **Example: Fade a Shape In and Out**
```tsx
import React, { useEffect } from 'react';
import { Canvas, Circle, useValue, runTiming, Easing } from '@shopify/react-native-skia';

const FadingCircle = () => {
  const opacity = useValue(0); // Initial opacity

  useEffect(() => {
    runTiming(opacity, 1, { duration: 2000, easing: Easing.inOut(Easing.cubic) });
  }, []);

  return (
    <Canvas style={{ flex: 1 }}>
      <Circle cx={150} cy={150} r={50} color={`rgba(255, 0, 0, ${opacity.current})`} />
    </Canvas>
  );
};

export default FadingCircle;
```

- **Result**: The circle fades in from fully transparent to fully opaque.

---

### **5. Combining Transformations**

You can combine multiple transformations using a `Group`.

#### **Example: Rotate and Scale a Shape**
```tsx
import React, { useEffect } from 'react';
import { Canvas, Rect, Group, useValue, runTiming, Easing } from '@shopify/react-native-skia';

const TransformingRect = () => {
  const rotation = useValue(0);
  const scale = useValue(1);

  useEffect(() => {
    runTiming(rotation, Math.PI * 2, { duration: 3000, easing: Easing.inOut(Easing.cubic) });
    runTiming(scale, 1.5, { duration: 3000, easing: Easing.inOut(Easing.cubic) });
  }, []);

  return (
    <Canvas style={{ flex: 1 }}>
      <Group transform={[{ rotate: rotation }, { scale }, { translateX: 100, translateY: 100 }]}>
        <Rect x={-50} y={-25} width={100} height={50} color="purple" />
      </Group>
    </Canvas>
  );
};

export default TransformingRect;
```

- **Result**: The rectangle rotates while scaling up.

---

### **Applications for TradeChampion**

1. **Stock Trend Highlights**:
   - Animate shapes on the chart to indicate significant price movements.
   - Scale or fade markers to highlight specific data points.

2. **Portfolio Growth Visualizations**:
   - Use scaling and translation to dynamically represent asset growth or distribution changes.

3. **Interactive News Highlights**:
   - Combine rotation and fading to draw attention to key news items or sectors.

---


