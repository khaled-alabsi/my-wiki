#### **1. Create the Interactive Chart**

**Code**:
```tsx
import React, { useState } from 'react';
import { Canvas, Path, Circle, Skia, Text } from '@shopify/react-native-skia';
import { GestureDetector, GestureHandlerRootView, PanGestureHandlerGestureEvent } from 'react-native-gesture-handler';
import Animated, { useSharedValue, useAnimatedGestureHandler } from 'react-native-reanimated';

const stockData = [
  { x: 50, y: 200, value: 100 },
  { x: 100, y: 150, value: 110 },
  { x: 150, y: 180, value: 115 },
  { x: 200, y: 120, value: 105 },
  { x: 250, y: 170, value: 108 },
];

const InteractiveStockChart = () => {
  const [currentValue, setCurrentValue] = useState(null);

  const markerX = useSharedValue(0);
  const markerY = useSharedValue(0);

  // Gesture handler to track finger movement
  const gestureHandler = useAnimatedGestureHandler({
    onActive: (event) => {
      // Find the closest point on the curve
      const closestPoint = stockData.reduce((prev, curr) => {
        const prevDist = Math.abs(prev.x - event.x);
        const currDist = Math.abs(curr.x - event.x);
        return currDist < prevDist ? curr : prev;
      });

      markerX.value = closestPoint.x;
      markerY.value = closestPoint.y;

      // Update the displayed value (React state for text)
      runOnJS(setCurrentValue)(closestPoint.value);
    },
  });

  // Generate the curve
  const path = Skia.Path.Make();
  stockData.forEach((point, index) => {
    if (index === 0) {
      path.moveTo(point.x, point.y);
    } else {
      path.lineTo(point.x, point.y);
    }
  });

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <GestureDetector onGestureEvent={gestureHandler}>
        <Canvas style={{ flex: 1 }}>
          {/* Draw the curve */}
          <Path path={path} color="blue" style="stroke" strokeWidth={2} />

          {/* Draw the moving marker */}
          <Circle cx={markerX.value} cy={markerY.value} r={5} color="red" />

          {/* Display the current value as text */}
          {currentValue && (
            <Text
              x={markerX.value}
              y={markerY.value - 20}
              text={`$${currentValue}`}
              color="black"
              font={Skia.Font(Skia.Typeface.MakeDefault(), 16)}
            />
          )}
        </Canvas>
      </GestureDetector>
    </GestureHandlerRootView>
  );
};

export default InteractiveStockChart;
```

---

### **How It Works**

1. **Gesture Tracking**:
   - The `gestureHandler` uses `react-native-reanimated` to capture touch gestures.
   - It calculates the closest data point on the curve based on the user’s touch position (`event.x`).

2. **Marker Movement**:
   - The `markerX` and `markerY` values are updated dynamically with the closest data point’s coordinates.

3. **Value Display**:
   - React state (`currentValue`) is updated with the `runOnJS` helper to trigger a re-render for the displayed text.

4. **Curve Rendering**:
   - The Skia `Path` object represents the stock chart curve.

5. **Marker Display**:
   - A `Circle` marker is positioned at the closest point on the curve.

---

### **Extensions and Enhancements**

#### **1. Smooth Marker Movement**
- Use animations like `withSpring` in `react-native-reanimated` for smoother marker transitions.

**Example**:
```tsx
import { withSpring } from 'react-native-reanimated';

onActive: (event) => {
  const closestPoint = ...; // Same logic as above
  markerX.value = withSpring(closestPoint.x);
  markerY.value = withSpring(closestPoint.y);
};
```

---

#### **2. Highlight Curve Segment**
- Highlight the curve segment closest to the user’s touch position by splitting the path dynamically.

#### **3. Zoom and Pan**
- Add pinch-to-zoom and pan gestures to navigate the chart.

---

### **Why This Solution Works Well**

1. **Responsiveness**:
   - Gesture updates (`useAnimatedGestureHandler`) are computed directly on the **UI thread**, ensuring smooth interactivity.

2. **Seamless Integration**:
   - Skia’s rendering capabilities are combined with `react-native-reanimated`’s gesture handling and animation tools.

3. **Flexibility**:
   - This approach can be extended for features like zooming, panning, or highlighting specific data points.

---

To implement an **interactive stock chart** where clicking or dragging along the curve displays the value at the current finger position, we can combine **Skia**, **react-native-gesture-handler**, and **react-native-reanimated**. Here’s a detailed solution.

---

### **Key Features**
1. **Curve Interaction**:
   - When the user taps or drags on the chart, determine the closest point on the curve.
   - Display the value corresponding to the nearest data point.

2. **Point Tracking**:
   - Show a marker (e.g., a circle) that moves along the curve following the user's finger.

3. **Dynamic Updates**:
   - Continuously update the displayed value and marker position as the user drags.

---

### **Should We Use `react-native-reanimated`, `runTiming`, or Both?**

- **`react-native-reanimated`**:
  - Handles gesture tracking (e.g., determining the user's touch position).
  - Manages animations of the marker and updates to its position.
- **Skia's `runTiming`**:
  - Not needed here since the marker position and updates are controlled dynamically via gestures.

Thus, **`react-native-reanimated`** and **Skia** are sufficient for this use case.

---

### **Implementation**

#### **1. Create the Interactive Chart**

**Code**:
```tsx
import React, { useState } from 'react';
import { Canvas, Path, Circle, Skia, Text } from '@shopify/react-native-skia';
import { GestureDetector, GestureHandlerRootView, PanGestureHandlerGestureEvent } from 'react-native-gesture-handler';
import Animated, { useSharedValue, useAnimatedGestureHandler } from 'react-native-reanimated';

const stockData = [
  { x: 50, y: 200, value: 100 },
  { x: 100, y: 150, value: 110 },
  { x: 150, y: 180, value: 115 },
  { x: 200, y: 120, value: 105 },
  { x: 250, y: 170, value: 108 },
];

const InteractiveStockChart = () => {
  const [currentValue, setCurrentValue] = useState(null);

  const markerX = useSharedValue(0);
  const markerY = useSharedValue(0);

  // Gesture handler to track finger movement
  const gestureHandler = useAnimatedGestureHandler({
    onActive: (event) => {
      // Find the closest point on the curve
      const closestPoint = stockData.reduce((prev, curr) => {
        const prevDist = Math.abs(prev.x - event.x);
        const currDist = Math.abs(curr.x - event.x);
        return currDist < prevDist ? curr : prev;
      });

      markerX.value = closestPoint.x;
      markerY.value = closestPoint.y;

      // Update the displayed value (React state for text)
      runOnJS(setCurrentValue)(closestPoint.value);
    },
  });

  // Generate the curve
  const path = Skia.Path.Make();
  stockData.forEach((point, index) => {
    if (index === 0) {
      path.moveTo(point.x, point.y);
    } else {
      path.lineTo(point.x, point.y);
    }
  });

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <GestureDetector onGestureEvent={gestureHandler}>
        <Canvas style={{ flex: 1 }}>
          {/* Draw the curve */}
          <Path path={path} color="blue" style="stroke" strokeWidth={2} />

          {/* Draw the moving marker */}
          <Circle cx={markerX.value} cy={markerY.value} r={5} color="red" />

          {/* Display the current value as text */}
          {currentValue && (
            <Text
              x={markerX.value}
              y={markerY.value - 20}
              text={`$${currentValue}`}
              color="black"
              font={Skia.Font(Skia.Typeface.MakeDefault(), 16)}
            />
          )}
        </Canvas>
      </GestureDetector>
    </GestureHandlerRootView>
  );
};

export default InteractiveStockChart;
```

---

### **How It Works**

1. **Gesture Tracking**:
   - The `gestureHandler` uses `react-native-reanimated` to capture touch gestures.
   - It calculates the closest data point on the curve based on the user’s touch position (`event.x`).

2. **Marker Movement**:
   - The `markerX` and `markerY` values are updated dynamically with the closest data point’s coordinates.

3. **Value Display**:
   - React state (`currentValue`) is updated with the `runOnJS` helper to trigger a re-render for the displayed text.

4. **Curve Rendering**:
   - The Skia `Path` object represents the stock chart curve.

5. **Marker Display**:
   - A `Circle` marker is positioned at the closest point on the curve.

---

### **Extensions and Enhancements**

#### **1. Smooth Marker Movement**
- Use animations like `withSpring` in `react-native-reanimated` for smoother marker transitions.

**Example**:
```tsx
import { withSpring } from 'react-native-reanimated';

onActive: (event) => {
  const closestPoint = ...; // Same logic as above
  markerX.value = withSpring(closestPoint.x);
  markerY.value = withSpring(closestPoint.y);
};
```

---

#### **2. Highlight Curve Segment**
- Highlight the curve segment closest to the user’s touch position by splitting the path dynamically.

#### **3. Zoom and Pan**
- Add pinch-to-zoom and pan gestures to navigate the chart.

---

### **Why This Solution Works Well**

1. **Responsiveness**:
   - Gesture updates (`useAnimatedGestureHandler`) are computed directly on the **UI thread**, ensuring smooth interactivity.

2. **Seamless Integration**:
   - Skia’s rendering capabilities are combined with `react-native-reanimated`’s gesture handling and animation tools.

3. **Flexibility**:
   - This approach can be extended for features like zooming, panning, or highlighting specific data points.

---
### **Adding Pinch-to-Zoom to the Interactive Stock Chart**

Pinch-to-zoom allows users to zoom in and out of the chart for a more detailed view. We’ll use **react-native-gesture-handler** for pinch gestures and **react-native-reanimated** to manage the zoom scale dynamically.

---

### **Implementation: Pinch-to-Zoom for the Chart**

**Code**:
```tsx
import React, { useState } from 'react';
import { Canvas, Path, Circle, Skia, Text } from '@shopify/react-native-skia';
import { GestureHandlerRootView, PinchGestureHandler, PanGestureHandlerGestureEvent } from 'react-native-gesture-handler';
import Animated, { useSharedValue, useAnimatedGestureHandler, useAnimatedStyle, withTiming } from 'react-native-reanimated';

const stockData = [
  { x: 50, y: 200, value: 100 },
  { x: 100, y: 150, value: 110 },
  { x: 150, y: 180, value: 115 },
  { x: 200, y: 120, value: 105 },
  { x: 250, y: 170, value: 108 },
];

const PinchZoomStockChart = () => {
  const [currentValue, setCurrentValue] = useState(null);

  const markerX = useSharedValue(0);
  const markerY = useSharedValue(0);
  const scale = useSharedValue(1);

  // Pinch gesture handler
  const pinchGestureHandler = useAnimatedGestureHandler({
    onActive: (event) => {
      scale.value = withTiming(event.scale, { duration: 50 }); // Dynamically update scale
    },
    onEnd: () => {
      scale.value = withTiming(1, { duration: 300 }); // Reset scale on gesture end
    },
  });

  // Gesture handler for dragging along the curve
  const panGestureHandler = useAnimatedGestureHandler({
    onActive: (event) => {
      const closestPoint = stockData.reduce((prev, curr) => {
        const prevDist = Math.abs(prev.x - event.x);
        const currDist = Math.abs(curr.x - event.x);
        return currDist < prevDist ? curr : prev;
      });

      markerX.value = closestPoint.x;
      markerY.value = closestPoint.y;
      runOnJS(setCurrentValue)(closestPoint.value);
    },
  });

  // Animated style for the canvas
  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
  }));

  // Generate the curve
  const path = Skia.Path.Make();
  stockData.forEach((point, index) => {
    if (index === 0) {
      path.moveTo(point.x, point.y);
    } else {
      path.lineTo(point.x, point.y);
    }
  });

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <PinchGestureHandler onGestureEvent={pinchGestureHandler}>
        <Animated.View style={[{ flex: 1 }, animatedStyle]}>
          <Canvas style={{ flex: 1 }}>
            {/* Draw the curve */}
            <Path path={path} color="blue" style="stroke" strokeWidth={2} />

            {/* Draw the moving marker */}
            <Circle cx={markerX.value} cy={markerY.value} r={5} color="red" />

            {/* Display the current value */}
            {currentValue && (
              <Text
                x={markerX.value}
                y={markerY.value - 20}
                text={`$${currentValue}`}
                color="black"
                font={Skia.Font(Skia.Typeface.MakeDefault(), 16)}
              />
            )}
          </Canvas>
        </Animated.View>
      </PinchGestureHandler>
    </GestureHandlerRootView>
  );
};

export default PinchZoomStockChart;
```

---

### **Explanation**

1. **Pinch Gesture Handling**:
   - The `PinchGestureHandler` listens for pinch gestures and updates the `scale` shared value dynamically during the gesture.
   - The scale smoothly resets to `1` when the gesture ends.

2. **Canvas Scaling**:
   - The `Animated.View` wraps the `Canvas` and applies the `scale` transformation to zoom in and out.

3. **Drag Gesture for Marker**:
   - The `PanGestureHandler` tracks the finger's position along the curve and updates the marker position and displayed value.

4. **Smooth Transitions**:
   - `withTiming` ensures smooth scaling transitions during and after the pinch gesture.

---

### **Enhancement: Highlighting Curve Segments**

Highlighting specific curve segments based on user interactions or data can make charts more informative and visually engaging.

---

### **Implementation: Highlight Curve Segment**

**Code**:
```tsx
import React, { useState } from 'react';
import { Canvas, Path, Skia, Circle, Text } from '@shopify/react-native-skia';
import { GestureHandlerRootView, PanGestureHandler } from 'react-native-gesture-handler';
import Animated, { useSharedValue, useAnimatedGestureHandler } from 'react-native-reanimated';

const stockData = [
  { x: 50, y: 200, value: 100 },
  { x: 100, y: 150, value: 110 },
  { x: 150, y: 180, value: 115 },
  { x: 200, y: 120, value: 105 },
  { x: 250, y: 170, value: 108 },
];

const HighlightCurveSegment = () => {
  const [currentValue, setCurrentValue] = useState(null);
  const [highlightSegment, setHighlightSegment] = useState(null);

  const markerX = useSharedValue(0);
  const markerY = useSharedValue(0);

  const panGestureHandler = useAnimatedGestureHandler({
    onActive: (event) => {
      const closestIndex = stockData.reduce((prevIndex, _, currIndex) => {
        const prevDist = Math.abs(stockData[prevIndex].x - event.x);
        const currDist = Math.abs(stockData[currIndex].x - event.x);
        return currDist < prevDist ? currIndex : prevIndex;
      }, 0);

      const closestPoint = stockData[closestIndex];
      const nextPoint = stockData[closestIndex + 1];

      markerX.value = closestPoint.x;
      markerY.value = closestPoint.y;

      runOnJS(setCurrentValue)(closestPoint.value);

      if (nextPoint) {
        runOnJS(setHighlightSegment)([closestPoint, nextPoint]);
      } else {
        runOnJS(setHighlightSegment)(null);
      }
    },
  });

  const path = Skia.Path.Make();
  stockData.forEach((point, index) => {
    if (index === 0) {
      path.moveTo(point.x, point.y);
    } else {
      path.lineTo(point.x, point.y);
    }
  });

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <PanGestureHandler onGestureEvent={panGestureHandler}>
        <Canvas style={{ flex: 1 }}>
          {/* Draw the curve */}
          <Path path={path} color="blue" style="stroke" strokeWidth={2} />

          {/* Highlighted segment */}
          {highlightSegment && (
            <Path
              path={() => {
                const segmentPath = Skia.Path.Make();
                segmentPath.moveTo(highlightSegment[0].x, highlightSegment[0].y);
                segmentPath.lineTo(highlightSegment[1].x, highlightSegment[1].y);
                return segmentPath;
              }}
              color="red"
              style="stroke"
              strokeWidth={4}
            />
          )}

          {/* Marker */}
          <Circle cx={markerX.value} cy={markerY.value} r={5} color="red" />

          {/* Display current value */}
          {currentValue && (
            <Text
              x={markerX.value}
              y={markerY.value - 20}
              text={`$${currentValue}`}
              color="black"
              font={Skia.Font(Skia.Typeface.MakeDefault(), 16)}
            />
          )}
        </Canvas>
      </PanGestureHandler>
    </GestureHandlerRootView>
  );
};

export default HighlightCurveSegment;
```

---

### **Explanation**

1. **Highlight Logic**:
   - Identify the segment between the closest point and the next point on the curve.
   - Highlight that segment by creating a new `Path` for just that segment.

2. **Dynamic Segment Updates**:
   - The highlighted segment updates dynamically as the user drags along the curve.

3. **Integration with Marker**:
   - The marker shows the closest point, and the highlighted segment provides additional visual feedback.

---

