### **7. Using Shaders and Filters in Skia**

Skia provides powerful tools for creating visually rich effects through **shaders** and **filters**. These include gradients, blurs, and custom shaders for dynamic visuals. Here’s how you can use them.

---

### **1. Gradients**

Gradients allow for smooth color transitions, often used for backgrounds, fills, or highlights.

#### **Types of Gradients**
- **Linear Gradient**: Color transition along a straight line.
- **Radial Gradient**: Circular color transition radiating from a center.
- **Sweep Gradient**: Circular color transition around a center (like a clock face).

---

#### **Linear Gradient**

**Example: Fill a Rectangle with a Linear Gradient**
```tsx
import { Canvas, Rect, LinearGradient } from '@shopify/react-native-skia';

<Canvas style={{ flex: 1 }}>
  <Rect
    x={50}
    y={50}
    width={200}
    height={100}
    color={
      <LinearGradient
        colors={["blue", "cyan"]}
        start={{ x: 50, y: 50 }}
        end={{ x: 250, y: 50 }}
      />
    }
  />
</Canvas>;
```

- **Result**: A rectangle transitioning from blue to cyan horizontally.

---

#### **Radial Gradient**

**Example: Circle with a Radial Gradient**
```tsx
import { Canvas, Circle, RadialGradient } from '@shopify/react-native-skia';

<Canvas style={{ flex: 1 }}>
  <Circle
    cx={150}
    cy={150}
    r={75}
    color={
      <RadialGradient
        colors={["red", "yellow", "green"]}
        center={{ x: 150, y: 150 }}
        radius={75}
      />
    }
  />
</Canvas>;
```

- **Result**: A circle transitioning from red at the center to green at the edge.

---

#### **Sweep Gradient**

**Example: Sweep Gradient for Circular Progress**
```tsx
import { Canvas, Circle, SweepGradient } from '@shopify/react-native-skia';

<Canvas style={{ flex: 1 }}>
  <Circle
    cx={150}
    cy={150}
    r={75}
    color={
      <SweepGradient
        colors={["red", "yellow", "green", "blue"]}
        center={{ x: 150, y: 150 }}
      />
    }
  />
</Canvas>;
```

- **Result**: A circular gradient transitioning through multiple colors.

---

### **2. Blur Effects**

Blur effects create soft, out-of-focus visuals, useful for backgrounds or highlighting focus areas.

#### **Gaussian Blur**
Applies a smooth blur effect.

**Example: Blur a Rectangle**
```tsx
import { Canvas, Rect, Blur } from '@shopify/react-native-skia';

<Canvas style={{ flex: 1 }}>
  <Rect x={50} y={50} width={200} height={100} color="blue" blur={Blur(10, 10)} />
</Canvas>;
```

- **Result**: A blurred rectangle with a 10px blur radius.

#### **Animating Blur**
You can animate blur values using `useValue`.

**Example: Animated Blur**
```tsx
import { Canvas, Rect, useValue, runTiming, Easing } from '@shopify/react-native-skia';

const AnimatedBlur = () => {
  const blurRadius = useValue(0);

  useEffect(() => {
    runTiming(blurRadius, 20, { duration: 2000, easing: Easing.inOut(Easing.cubic) });
  }, []);

  return (
    <Canvas style={{ flex: 1 }}>
      <Rect
        x={50}
        y={50}
        width={200}
        height={100}
        color="blue"
        blur={Blur(blurRadius, blurRadius)}
      />
    </Canvas>
  );
};
```

- **Result**: The rectangle’s blur radius animates from 0 to 20.

---

### **3. Custom Shaders**

Custom shaders give you full control over rendering, allowing for unique visual effects. You can define custom GLSL-like code to manipulate pixels.

#### **Basic Custom Shader**

**Example: Wave Shader**
```tsx
import { Canvas, Rect, Shaders, Shader } from '@shopify/react-native-skia';

const waveShader = Shaders.create(`
  uniform vec2 u_resolution;
  uniform float u_time;

  vec4 main(vec2 fragCoord) {
    vec2 uv = fragCoord / u_resolution;
    float wave = sin(uv.x * 10.0 + u_time) * 0.5 + 0.5;
    return vec4(wave, wave, 1.0, 1.0);
  }
`);

<Canvas style={{ flex: 1 }}>
  <Rect
    x={0}
    y={0}
    width={300}
    height={300}
    color={Shader(waveShader, {
      u_resolution: [300, 300],
      u_time: performance.now() / 1000,
    })}
  />
</Canvas>;
```

- **Result**: A dynamic wave pattern that changes over time.

---

#### **Shader with Animations**

**Example: Animated Time Uniform**
```tsx
import { useValue, runTiming, Easing } from '@shopify/react-native-skia';

const time = useValue(0);

useEffect(() => {
  runTiming(time, 10, { duration: 5000, easing: Easing.linear });
}, []);

<Canvas style={{ flex: 1 }}>
  <Rect
    x={0}
    y={0}
    width={300}
    height={300}
    color={Shader(waveShader, {
      u_resolution: [300, 300],
      u_time: time.current,
    })}
  />
</Canvas>;
```

- **Result**: The wave pattern evolves over 5 seconds.

---

### **Applications for TradeChampion**

1. **Gradients for Charts**:
   - Use linear gradients for stock trend backgrounds.
   - Apply radial gradients to highlight key data points.

2. **Blur Effects for Focus Areas**:
   - Blur non-essential parts of the screen to draw focus to key metrics or charts.

3. **Custom Shaders for Advanced Visuals**:
   - Implement real-time stock price heatmaps with dynamic color changes.
   - Create unique visualizations for news highlights or portfolio distribution.

---

### **Real-World Implementations of Shaders and Filters in TradeChampion**

Here are some practical use cases for gradients, blur effects, and custom shaders in your app, along with implementation examples.

---

### **1. Gradients for Stock Charts**

#### **Use Case**: Add a gradient background to a stock chart to enhance visual appeal.

**Implementation**:
```tsx
import { Canvas, Rect, Path, LinearGradient } from '@shopify/react-native-skia';
import { Skia } from '@shopify/react-native-skia';

const stockData = [
  { x: 0, y: 200 },
  { x: 50, y: 150 },
  { x: 100, y: 180 },
  { x: 150, y: 120 },
  { x: 200, y: 170 },
];

const path = Skia.Path.Make();
stockData.forEach((point, index) => {
  if (index === 0) path.moveTo(point.x, point.y);
  else path.lineTo(point.x, point.y);
});

<Canvas style={{ flex: 1 }}>
  {/* Gradient Background */}
  <Rect
    x={0}
    y={0}
    width={300}
    height={300}
    color={
      <LinearGradient
        colors={["#1e3a8a", "#2563eb"]}
        start={{ x: 0, y: 0 }}
        end={{ x: 300, y: 300 }}
      />
    }
  />
  {/* Stock Path */}
  <Path path={path} color="white" style="stroke" strokeWidth={2} />
</Canvas>;
```

- **Result**: A stock chart with a gradient background transitioning from dark blue to light blue.

---

### **2. Blur Effects for Focus Areas**

#### **Use Case**: Blur the background when a user selects a specific stock, drawing attention to the stock details.

**Implementation**:
```tsx
import { Canvas, Rect, Blur } from '@shopify/react-native-skia';

const StockBlur = () => {
  return (
    <Canvas style={{ flex: 1 }}>
      {/* Blurred Background */}
      <Rect x={0} y={0} width={300} height={300} color="gray" blur={Blur(10, 10)} />
      {/* Focused Detail */}
      <Rect x={100} y={100} width={100} height={50} color="blue" />
    </Canvas>
  );
};

export default StockBlur;
```

- **Result**: The entire background is blurred except for a specific detail rectangle.

---

### **3. Custom Shader for Heatmaps**

#### **Use Case**: Display a heatmap for stock price movements with dynamic colors based on performance.

**Implementation**:
```tsx
import { Canvas, Rect, Shaders, Shader } from '@shopify/react-native-skia';

const heatmapShader = Shaders.create(`
  uniform vec2 u_resolution;
  uniform vec2 u_mouse;
  uniform float u_intensity;

  vec4 main(vec2 fragCoord) {
    vec2 uv = fragCoord / u_resolution;
    float dist = distance(uv, u_mouse);
    float intensity = smoothstep(0.3, 0.0, dist) * u_intensity;
    return vec4(intensity, 0.0, 1.0 - intensity, 1.0);
  }
`);

<Canvas style={{ flex: 1 }}>
  <Rect
    x={0}
    y={0}
    width={300}
    height={300}
    color={Shader(heatmapShader, {
      u_resolution: [300, 300],
      u_mouse: [0.5, 0.5], // Simulated stock location
      u_intensity: 1.0,
    })}
  />
</Canvas>;
```

- **Result**: A heatmap effect where colors dynamically change intensity around a specified point.

---

### **4. Radial Gradient for Pie Chart Highlights**

#### **Use Case**: Highlight a specific sector in a portfolio pie chart.

**Implementation**:
```tsx
import { Canvas, Circle, RadialGradient, Group } from '@shopify/react-native-skia';

<Canvas style={{ flex: 1 }}>
  <Group>
    {/* Pie Segment */}
    <Circle
      cx={150}
      cy={150}
      r={75}
      color={
        <RadialGradient
          colors={["#10b981", "#facc15"]}
          center={{ x: 150, y: 150 }}
          radius={75}
        />
      }
    />
    {/* Overlap Another Segment */}
    <Circle cx={150} cy={150} r={60} color="white" />
  </Group>
</Canvas>;
```

- **Result**: The gradient highlights a specific pie chart sector while the others are grayed out.

---

### **5. Animated Shader for Market Volatility**

#### **Use Case**: Represent real-time market volatility with a dynamically evolving background.

**Implementation**:
```tsx
import { Canvas, Rect, Shaders, Shader, useValue, runTiming, Easing } from '@shopify/react-native-skia';

const volatilityShader = Shaders.create(`
  uniform vec2 u_resolution;
  uniform float u_time;

  vec4 main(vec2 fragCoord) {
    vec2 uv = fragCoord / u_resolution;
    float pattern = sin(uv.x * 10.0 + u_time) * sin(uv.y * 10.0 - u_time);
    return vec4(1.0, pattern * 0.5 + 0.5, 0.0, 1.0);
  }
`);

const MarketVolatility = () => {
  const time = useValue(0);

  useEffect(() => {
    runTiming(time, 10, { duration: 5000, easing: Easing.linear });
  }, []);

  return (
    <Canvas style={{ flex: 1 }}>
      <Rect
        x={0}
        y={0}
        width={300}
        height={300}
        color={Shader(volatilityShader, {
          u_resolution: [300, 300],
          u_time: time.current,
        })}
      />
    </Canvas>
  );
};

export default MarketVolatility;
```

- **Result**: The background pattern evolves dynamically to represent market volatility.

---

### **Summary of Use Cases**

1. **Stock Trend Background**:
   - Use linear gradients to enhance stock chart visuals.
2. **Portfolio Focus**:
   - Blur non-essential areas for better focus.
3. **Dynamic Heatmaps**:
   - Implement real-time performance indicators with custom shaders.
4. **Sector Highlights**:
   - Use radial gradients for pie chart highlights.
5. **Market Volatility Indicators**:
   - Animate shader patterns to reflect real-time market conditions.

---
### **Interactivity with Shaders in Skia**

Adding interactivity to shaders allows users to engage dynamically with visuals, such as reacting to touch gestures or responding to data changes. Here’s how you can make shaders interactive in Skia:

---

### **Key Techniques**

1. **Using Touch Gestures**:
   - Capture touch or pan gestures to modify shader properties like position, intensity, or color.
2. **Dynamic Uniforms**:
   - Pass dynamic values (e.g., user input or animation states) to shaders using uniforms.
3. **Data-Driven Shaders**:
   - React to real-time data updates to change shader behavior.

---

### **Examples**

#### **1. Interactive Gradient with Touch Input**

Change the center of a radial gradient based on touch location.

**Implementation**:
```tsx
import React, { useState } from 'react';
import { Canvas, Circle, RadialGradient } from '@shopify/react-native-skia';
import { GestureDetector, GestureHandlerRootView } from 'react-native-gesture-handler';

const InteractiveGradient = () => {
  const [center, setCenter] = useState({ x: 150, y: 150 });

  const handleGesture = GestureDetector.create({
    onStart: (e) => setCenter({ x: e.x, y: e.y }),
    onUpdate: (e) => setCenter({ x: e.x, y: e.y }),
  });

  return (
    <GestureHandlerRootView>
      <Canvas style={{ flex: 1 }}>
        <Circle
          cx={center.x}
          cy={center.y}
          r={100}
          color={
            <RadialGradient
              colors={["red", "yellow", "green"]}
              center={center}
              radius={100}
            />
          }
        />
      </Canvas>
    </GestureHandlerRootView>
  );
};

export default InteractiveGradient;
```

- **Result**: The radial gradient’s center follows the user’s touch.

---

#### **2. Heatmap with Pan Gesture**

Move a heatmap’s hotspot interactively using touch gestures.

**Implementation**:
```tsx
import React, { useState } from 'react';
import { Canvas, Rect, Shaders, Shader } from '@shopify/react-native-skia';
import { GestureDetector, GestureHandlerRootView } from 'react-native-gesture-handler';

const heatmapShader = Shaders.create(`
  uniform vec2 u_resolution;
  uniform vec2 u_mouse;

  vec4 main(vec2 fragCoord) {
    vec2 uv = fragCoord / u_resolution;
    float dist = distance(uv, u_mouse);
    float intensity = smoothstep(0.2, 0.0, dist);
    return vec4(intensity, 0.0, 1.0 - intensity, 1.0);
  }
`);

const InteractiveHeatmap = () => {
  const [mouse, setMouse] = useState({ x: 0.5, y: 0.5 });

  const handleGesture = GestureDetector.create({
    onUpdate: (e) => setMouse({ x: e.x / 300, y: e.y / 300 }),
  });

  return (
    <GestureHandlerRootView>
      <Canvas style={{ flex: 1 }}>
        <Rect
          x={0}
          y={0}
          width={300}
          height={300}
          color={Shader(heatmapShader, {
            u_resolution: [300, 300],
            u_mouse: [mouse.x, mouse.y],
          })}
        />
      </Canvas>
    </GestureHandlerRootView>
  );
};

export default InteractiveHeatmap;
```

- **Result**: The heatmap’s hotspot moves to the user’s touch location.

---

#### **3. Interactive Shader with Dynamic Data**

Change the properties of a shader based on stock data updates.

**Implementation**:
```tsx
import { Canvas, Rect, Shaders, Shader } from '@shopify/react-native-skia';
import { useState, useEffect } from 'react';

const stockShader = Shaders.create(`
  uniform vec2 u_resolution;
  uniform float u_intensity;

  vec4 main(vec2 fragCoord) {
    vec2 uv = fragCoord / u_resolution;
    float color = smoothstep(0.0, 1.0, uv.x) * u_intensity;
    return vec4(color, 0.0, 1.0 - color, 1.0);
  }
`);

const DataDrivenShader = ({ stockData }) => {
  const [intensity, setIntensity] = useState(1);

  useEffect(() => {
    const maxPrice = Math.max(...stockData.map((d) => d.price));
    const minPrice = Math.min(...stockData.map((d) => d.price));
    const currentPrice = stockData[stockData.length - 1].price;
    setIntensity((currentPrice - minPrice) / (maxPrice - minPrice));
  }, [stockData]);

  return (
    <Canvas style={{ flex: 1 }}>
      <Rect
        x={0}
        y={0}
        width={300}
        height={300}
        color={Shader(stockShader, {
          u_resolution: [300, 300],
          u_intensity: intensity,
        })}
      />
    </Canvas>
  );
};

export default DataDrivenShader;
```

- **Result**: The shader’s intensity changes dynamically based on stock price.

---

### **Applications for TradeChampion**

1. **Interactive Stock Trendlines**:
   - Use shaders to highlight specific trends based on user touch.
   - Display gradient effects over selected regions.

2. **Heatmaps for Portfolio Visualization**:
   - Dynamically adjust hotspots based on user input or portfolio performance data.

3. **Data-Driven Visualizations**:
   - Visualize real-time stock market movements or portfolio growth using dynamic shader properties.

---

### **Updated Response: Interactive Shaders with Detailed Explanations**

In this updated response, I’ll explain the role of `GestureDetector` and `GestureHandlerRootView`, walk through the code step by step, and clarify how React state (`useState`) integrates with Skia states (`useValue`).

---

### **Key Components in the Code**

#### **GestureDetector**
- A component from the **React Native Gesture Handler** library.
- Captures gestures like taps, pans, swipes, and pinches.
- Provides event callbacks for gestures (e.g., `onStart`, `onUpdate`, `onEnd`).
- In the examples, `GestureDetector` listens for user input and triggers state updates.

#### **GestureHandlerRootView**
- A wrapper component required by the Gesture Handler library.
- Ensures gesture handling works correctly across platforms.
- All components using gestures (`GestureDetector`) must be nested inside this wrapper.

---

### **Code Breakdown: Interactive Heatmap**

```typescript
import React, { useState } from 'react';
import { Canvas, Rect, Shaders, Shader } from '@shopify/react-native-skia';
import {
  GestureDetector,
  GestureHandlerRootView,
  PanGestureHandlerGestureEvent,
} from 'react-native-gesture-handler';

const heatmapShader = Shaders.create(`
  uniform vec2 u_resolution;
  uniform vec2 u_mouse;

  vec4 main(vec2 fragCoord) {
    vec2 uv = fragCoord / u_resolution;
    float dist = distance(uv, u_mouse);
    float intensity = smoothstep(0.2, 0.0, dist);
    return vec4(intensity, 0.0, 1.0 - intensity, 1.0);
  }
`);

const InteractiveHeatmap = () => {
  const [mouse, setMouse] = useState({ x: 0.5, y: 0.5 }); // React state to track the touch position

  // Gesture detector configuration
  const handleGesture = (event: PanGestureHandlerGestureEvent) => {
    const { x, y } = event.nativeEvent;
    setMouse({ x: x / 300, y: y / 300 }); // Normalize touch coordinates
  };

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <GestureDetector onGestureEvent={handleGesture}>
        <Canvas style={{ flex: 1 }}>
          <Rect
            x={0}
            y={0}
            width={300}
            height={300}
            color={Shader(heatmapShader, {
              u_resolution: [300, 300],
              u_mouse: [mouse.x, mouse.y], // Pass `mouse` state to the shader as uniform
            })}
          />
        </Canvas>
      </GestureDetector>
    </GestureHandlerRootView>
  );
};

export default InteractiveHeatmap;

```
---

### **Step-by-Step Explanation**

1. **Initializing State**:
   ```tsx
   const [mouse, setMouse] = useState({ x: 0.5, y: 0.5 });
   ```
   - **What it does**:
     - Initializes a React state (`mouse`) with the default position `(0.5, 0.5)`.
     - This represents the normalized x and y coordinates of the user’s touch (relative to the canvas size).

2. **Configuring the Gesture Detector**:
   ```tsx
   const handleGesture = GestureDetector.create({
     onUpdate: (e) => setMouse({ x: e.x / 300, y: e.y / 300 }),
   });
   ```
   - **What it does**:
     - Captures touch events with the `onUpdate` callback.
     - `e.x` and `e.y` are the raw coordinates of the touch within the canvas.
     - The coordinates are normalized to a range of `[0, 1]` by dividing by the canvas size (300 in this case).
     - Updates the `mouse` state whenever the user moves their finger.

3. **Shader Reactivity**:
   ```tsx
   color={Shader(heatmapShader, {
     u_resolution: [300, 300],
     u_mouse: [mouse.x, mouse.y],
   })}
   ```
   - **What it does**:
     - Passes the current state of `mouse` as the `u_mouse` uniform to the shader.
     - `u_mouse` determines the position of the hotspot in the heatmap.
     - Whenever `mouse` changes (via `setMouse`), the shader re-renders with the updated uniform values.

4. **Drawing the Heatmap**:
   ```tsx
   <Rect x={0} y={0} width={300} height={300} color={Shader(...)} />
   ```
   - **What it does**:
     - Draws a rectangle that spans the entire canvas.
     - The rectangle’s `color` is determined by the `heatmapShader`, which calculates intensity based on the distance from `u_mouse`.

---

### **How React State Works with Skia States**

#### **React State (`useState`)**
- Tracks high-level app state and interactions.
- In the example, `useState` is used to track the touch position (`mouse`) in normalized coordinates.
- React re-renders components whenever state changes, which updates the shader.

#### **Skia State (`useValue`)**
- Designed for high-performance updates directly tied to Skia rendering.
- **When to use**:
  - For animations (e.g., `runTiming` or `spring`).
  - For directly manipulating Skia elements without triggering a React re-render.
- **Why React state was used here**:
  - The position (`mouse`) updates are driven by gestures, which are external to Skia.
  - `useState` simplifies managing external data and passing it as uniforms.

#### **When to Prefer Skia State Over React State**
- Use `useValue` for properties that need frequent updates, like animations or continuous motion.
- Example:
  ```tsx
  const mouseX = useValue(0.5);
  const mouseY = useValue(0.5);

  useEffect(() => {
    runTiming(mouseX, 1, { duration: 2000 });
    runTiming(mouseY, 0.5, { duration: 2000 });
  }, []);
  ```

---

### **Key Takeaways**

1. **GestureDetector and GestureHandlerRootView**:
   - Essential for handling gestures in React Native.
   - `GestureDetector` captures gestures and triggers callbacks.
   - `GestureHandlerRootView` ensures gestures are recognized across platforms.

2. **State Updates**:
   - React state (`useState`) integrates seamlessly with Skia when shader uniforms or external properties need to be updated.
   - Use `useValue` for properties requiring high-frequency updates or animations.

3. **Trigger Flow**:
   - **Gesture Event** → **`onUpdate` Callback** → **`setMouse` Update** → **Shader Uniform Update** → **Re-render Canvas**.

4. **Performance**:
   - React state is fine for gestures and occasional updates.
   - For animations or real-time effects, prefer `useValue` for Skia-rendered elements.

---

