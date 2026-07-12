### **9. Building Interactive Elements in Skia**

Interactive elements allow users to engage with your Skia visuals through gestures (e.g., taps, drags, or zooms) and dynamic user input. React Native Gesture Handler and Skia’s rendering pipeline enable seamless integration of gestures and animations.

---

### **Key Concepts**

1. **Handling Gestures in Skia**:
   - Use `GestureDetector` or `PanGestureHandler` from React Native Gesture Handler.
   - Capture user interactions like taps, drags, or pinches.
   - Update Skia’s `useValue` or React state to reflect changes in the canvas.

2. **Responding to User Input**:
   - Dynamically modify shapes, colors, or positions based on user actions.
   - Combine gestures with Skia animations for smooth transitions.

---

### **1. Handling Gestures**

#### **a. Tap to Change Color**

**Example: Tap to Change Circle’s Color**
```tsx
import React, { useState } from 'react';
import { Canvas, Circle } from '@shopify/react-native-skia';
import { GestureDetector, GestureHandlerRootView } from 'react-native-gesture-handler';

const TapCircle = () => {
  const [color, setColor] = useState("blue");

  const handleTap = () => {
    const newColor = color === "blue" ? "red" : "blue";
    setColor(newColor);
  };

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <GestureDetector onGestureEvent={handleTap}>
        <Canvas style={{ flex: 1 }}>
          <Circle cx={150} cy={150} r={50} color={color} />
        </Canvas>
      </GestureDetector>
    </GestureHandlerRootView>
  );
};

export default TapCircle;
```

- **Flow**:
  - The `GestureDetector` listens for taps.
  - The `handleTap` function toggles the circle’s color between blue and red by updating React state.

---

#### **b. Drag to Move an Element**

**Example: Drag to Move a Circle**
```tsx
import React, { useState } from 'react';
import { Canvas, Circle } from '@shopify/react-native-skia';
import { GestureDetector, GestureHandlerRootView, PanGestureHandlerGestureEvent } from 'react-native-gesture-handler';

const DragCircle = () => {
  const [position, setPosition] = useState({ x: 150, y: 150 });

  const handleDrag = (event: PanGestureHandlerGestureEvent) => {
    const { x, y } = event.nativeEvent;
    setPosition({ x, y });
  };

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <GestureDetector onGestureEvent={handleDrag}>
        <Canvas style={{ flex: 1 }}>
          <Circle cx={position.x} cy={position.y} r={50} color="green" />
        </Canvas>
      </GestureDetector>
    </GestureHandlerRootView>
  );
};

export default DragCircle;
```

- **Flow**:
  - The `GestureDetector` tracks the user’s drag gesture.
  - The `handleDrag` function updates the circle’s position using React state.

---

#### **c. Pinch to Scale an Element**

**Example: Pinch to Resize a Rectangle**
```tsx
import React, { useState } from 'react';
import { Canvas, Rect } from '@shopify/react-native-skia';
import { PinchGestureHandler, GestureHandlerRootView, PinchGestureHandlerGestureEvent } from 'react-native-gesture-handler';

const PinchRect = () => {
  const [scale, setScale] = useState(1);

  const handlePinch = (event: PinchGestureHandlerGestureEvent) => {
    setScale(event.nativeEvent.scale);
  };

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <PinchGestureHandler onGestureEvent={handlePinch}>
        <Canvas style={{ flex: 1 }}>
          <Rect x={100} y={100} width={100 * scale} height={100 * scale} color="purple" />
        </Canvas>
      </PinchGestureHandler>
    </GestureHandlerRootView>
  );
};

export default PinchRect;
```

- **Flow**:
  - The `PinchGestureHandler` listens for pinch gestures.
  - The `handlePinch` function updates the rectangle’s scale based on the gesture.

---

### **2. Responding to User Input**

#### **a. Dynamic Shape Creation**

**Example: Tap to Add Circles**
```tsx
import React, { useState } from 'react';
import { Canvas, Circle } from '@shopify/react-native-skia';
import { GestureDetector, GestureHandlerRootView, TapGestureHandlerGestureEvent } from 'react-native-gesture-handler';

const AddCircles = () => {
  const [circles, setCircles] = useState([]);

  const handleTap = (event: TapGestureHandlerGestureEvent) => {
    const { x, y } = event.nativeEvent;
    setCircles([...circles, { x, y, r: 30, color: "blue" }]);
  };

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <GestureDetector onGestureEvent={handleTap}>
        <Canvas style={{ flex: 1 }}>
          {circles.map((circle, index) => (
            <Circle key={index} cx={circle.x} cy={circle.y} r={circle.r} color={circle.color} />
          ))}
        </Canvas>
      </GestureDetector>
    </GestureHandlerRootView>
  );
};

export default AddCircles;
```

- **Flow**:
  - Each tap adds a new circle at the tap location.
  - Circles are stored in an array managed by React state.

---

#### **b. Interactive Charts**

**Example: Drag to Highlight Stock Data**
```tsx
import React, { useState } from 'react';
import { Canvas, Line, Circle } from '@shopify/react-native-skia';
import { GestureDetector, GestureHandlerRootView, PanGestureHandlerGestureEvent } from 'react-native-gesture-handler';

const StockChart = () => {
  const stockData = [
    { x: 50, y: 200 },
    { x: 100, y: 150 },
    { x: 150, y: 180 },
    { x: 200, y: 120 },
    { x: 250, y: 170 },
  ];

  const [highlight, setHighlight] = useState(null);

  const handleDrag = (event: PanGestureHandlerGestureEvent) => {
    const { x } = event.nativeEvent;
    const closest = stockData.reduce((prev, curr) =>
      Math.abs(curr.x - x) < Math.abs(prev.x - x) ? curr : prev
    );
    setHighlight(closest);
  };

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <GestureDetector onGestureEvent={handleDrag}>
        <Canvas style={{ flex: 1 }}>
          {stockData.map((point, index) => (
            <Circle key={index} cx={point.x} cy={point.y} r={5} color="blue" />
          ))}
          {highlight && (
            <Circle cx={highlight.x} cy={highlight.y} r={10} color="red" />
          )}
        </Canvas>
      </GestureDetector>
    </GestureHandlerRootView>
  );
};

export default StockChart;
```

- **Flow**:
  - The user drags across the chart to highlight the closest data point.
  - The `highlight` state determines the red circle’s position.

---

### **Applications for TradeChampion**

1. **Interactive Stock Charts**:
   - Drag to explore specific data points or time periods.
   - Tap to add annotations or highlights.

2. **Dynamic Portfolio Visualization**:
   - Pinch to zoom into a specific sector.
   - Tap to show details for individual investments.

3. **Interactive News Highlights**:
   - Tap on news items to display additional details.
   - Swipe to reorder or categorize news.

