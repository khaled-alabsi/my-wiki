### **14. Skia with `react-native-gesture-handler` and `react-native-reanimated`**

Combining **Skia**, **`react-native-gesture-handler`**, and **`react-native-reanimated`** allows for smooth, interactive, and performant gesture-driven animations. This integration is particularly useful for building dynamic UIs with seamless touch interactions and fluid animations.

---

### **1. Key Roles of Each Library**

- **Skia**: Renders graphics and animations directly on the GPU.
- **`react-native-gesture-handler`**: Captures and handles complex gestures (e.g., pan, pinch, tap).
- **`react-native-reanimated`**: Animates properties smoothly with optimized frame updates.

---

### **2. Setting Up Dependencies**

Install the required packages:
```bash
npm install @shopify/react-native-skia react-native-gesture-handler react-native-reanimated
```

Configure `react-native-gesture-handler` in `index.js`:
```tsx
import 'react-native-gesture-handler';
```

Configure `react-native-reanimated`: ***explantion for this step are at the end of this Text***
Add this at the top of your `babel.config.js`:
```js
module.exports = {
  presets: ['module:metro-react-native-babel-preset'],
  plugins: ['react-native-reanimated/plugin'],
};
```

---

### **3. Examples**

#### **a. Gesture-Driven Animation: Dragging a Circle**

**Feature**: Drag a circle across the canvas, with smooth updates from `react-native-reanimated`.

**Implementation**:
```tsx
import React from 'react';
import { Canvas, Circle } from '@shopify/react-native-skia';
import { GestureDetector, GestureHandlerRootView, PanGestureHandler } from 'react-native-gesture-handler';
import Animated, {
  useSharedValue,
  useAnimatedGestureHandler,
  useAnimatedProps,
} from 'react-native-reanimated';

const DraggableCircle = () => {
  const x = useSharedValue(150);
  const y = useSharedValue(150);

  const gestureHandler = useAnimatedGestureHandler({
    onStart: (_, ctx) => {
      ctx.startX = x.value;
      ctx.startY = y.value;
    },
    onActive: (event, ctx) => {
      x.value = ctx.startX + event.translationX;
      y.value = ctx.startY + event.translationY;
    },
  });

  const animatedProps = useAnimatedProps(() => ({
    cx: x.value,
    cy: y.value,
  }));

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <PanGestureHandler onGestureEvent={gestureHandler}>
        <Canvas style={{ flex: 1 }}>
          <Animated.Circle r={50} color="blue" animatedProps={animatedProps} />
        </Canvas>
      </PanGestureHandler>
    </GestureHandlerRootView>
  );
};

export default DraggableCircle;
```

**How It Works**:
1. **`useSharedValue`**:
   - Tracks the circle’s position (`x`, `y`) across frames.
2. **`useAnimatedGestureHandler`**:
   - Updates the position based on drag gestures.
3. **`useAnimatedProps`**:
   - Links Skia’s `Circle` properties (`cx`, `cy`) to `react-native-reanimated`’s animated values.

---

#### **b. Pinch to Zoom**

**Feature**: Use pinch gestures to scale an element.

**Implementation**:
```tsx
import React from 'react';
import { Canvas, Rect } from '@shopify/react-native-skia';
import { GestureDetector, GestureHandlerRootView, PinchGestureHandler } from 'react-native-gesture-handler';
import Animated, {
  useSharedValue,
  useAnimatedGestureHandler,
  useAnimatedProps,
} from 'react-native-reanimated';

const PinchToZoom = () => {
  const scale = useSharedValue(1);

  const gestureHandler = useAnimatedGestureHandler({
    onActive: (event) => {
      scale.value = event.scale;
    },
    onEnd: () => {
      scale.value = 1; // Reset scale on gesture end
    },
  });

  const animatedProps = useAnimatedProps(() => ({
    transform: [{ scale: scale.value }],
  }));

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <PinchGestureHandler onGestureEvent={gestureHandler}>
        <Canvas style={{ flex: 1 }}>
          <Animated.Rect x={100} y={100} width={100} height={100} color="red" animatedProps={animatedProps} />
        </Canvas>
      </PinchGestureHandler>
    </GestureHandlerRootView>
  );
};

export default PinchToZoom;
```

**How It Works**:
1. **`useSharedValue`**:
   - Tracks the current scaling factor.
2. **`useAnimatedGestureHandler`**:
   - Updates the scale value during pinch gestures.
3. **Reset Logic**:
   - Resets the scale to `1` when the gesture ends.

---

#### **c. Combine Drag and Pinch Gestures**

**Feature**: Drag and resize a circle simultaneously.

**Implementation**:
```tsx
import React from 'react';
import { Canvas, Circle } from '@shopify/react-native-skia';
import { GestureDetector, GestureHandlerRootView, PanGestureHandler, PinchGestureHandler } from 'react-native-gesture-handler';
import Animated, {
  useSharedValue,
  useAnimatedGestureHandler,
  useAnimatedProps,
} from 'react-native-reanimated';

const InteractiveCircle = () => {
  const x = useSharedValue(150);
  const y = useSharedValue(150);
  const scale = useSharedValue(1);

  const panHandler = useAnimatedGestureHandler({
    onStart: (_, ctx) => {
      ctx.startX = x.value;
      ctx.startY = y.value;
    },
    onActive: (event, ctx) => {
      x.value = ctx.startX + event.translationX;
      y.value = ctx.startY + event.translationY;
    },
  });

  const pinchHandler = useAnimatedGestureHandler({
    onActive: (event) => {
      scale.value = event.scale;
    },
    onEnd: () => {
      scale.value = 1; // Reset scale on gesture end
    },
  });

  const animatedProps = useAnimatedProps(() => ({
    cx: x.value,
    cy: y.value,
    transform: [{ scale: scale.value }],
  }));

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <PanGestureHandler onGestureEvent={panHandler}>
        <PinchGestureHandler onGestureEvent={pinchHandler}>
          <Canvas style={{ flex: 1 }}>
            <Animated.Circle r={50} color="blue" animatedProps={animatedProps} />
          </Canvas>
        </PinchGestureHandler>
      </PanGestureHandler>
    </GestureHandlerRootView>
  );
};

export default InteractiveCircle;
```

**How It Works**:
1. **`PanGestureHandler`**:
   - Updates the circle’s position (`cx`, `cy`).
2. **`PinchGestureHandler`**:
   - Updates the circle’s scale.
3. **Combined Gestures**:
   - Both gesture handlers work simultaneously without conflicts.

---

### **Best Practices**

1. **Optimize Animations**:
   - Use `react-native-reanimated`’s `useSharedValue` and `useAnimatedProps` for high-performance updates.

2. **Avoid React State for Animation-Intensive Tasks**:
   - Shared values (`useSharedValue`) ensure smooth updates without triggering React’s re-render cycle.

3. **Combine Gestures**:
   - Nest `PanGestureHandler` and `PinchGestureHandler` for advanced interactions.
   - Use `simultaneousHandlers` or `waitFor` to manage gesture conflicts.

4. **Test for Performance**:
   - Profile the app on real devices to ensure smooth rendering and responsiveness.

---

### **Applications in TradeChampion**

1. **Stock Chart Navigation**:
   - **Drag**: Pan across the chart.
   - **Pinch**: Zoom into specific time ranges.

2. **Interactive Portfolio Visualization**:
   - **Resize**: Adjust the size of pie chart slices.
   - **Drag**: Reposition slices for better focus.

3. **Dynamic News Highlights**:
   - **Tap and Drag**: Reorder or explore specific news stories.

---

### **Explanation of the Babel Configuration**

The provided `babel.config.js` file is part of a React Native project setup. Babel is a JavaScript compiler that transforms modern JavaScript (e.g., ES6+) into a version compatible with older environments, such as older browsers or mobile devices. In this configuration, the `presets` and `plugins` fields enable features required for the React Native framework and its libraries.

---

### **Key Components of the Configuration**

#### **1. `presets`**
- **Definition**: A preset is a collection of Babel plugins used to transform specific types of JavaScript code.
- **Purpose in React Native**:
  - The `metro-react-native-babel-preset` preset is specific to React Native.
  - It enables Babel to understand and compile modern JavaScript and React Native features, such as JSX, class properties, and TypeScript.

**Snippet**:
```javascript
presets: ['module:metro-react-native-babel-preset'],
```

**What it does**:
- Transforms JSX syntax (`<View></View>`) into JavaScript that the JavaScript runtime can execute.
- Transforms ES6+ syntax (e.g., arrow functions, async/await) into ES5.
- Ensures compatibility with the Metro bundler, the default bundler for React Native projects.

**Without this preset**:
- React Native code won't compile correctly, leading to syntax errors during the build.

---

#### **2. `plugins`**
- **Definition**: Plugins are smaller, more focused Babel extensions that add specific transformations or capabilities.
- **Purpose**:
  - In this configuration, the `react-native-reanimated/plugin` is added to handle the optimization of animations in `react-native-reanimated`.

**Snippet**:
```javascript
plugins: ['react-native-reanimated/plugin'],
```

**What it does**:
- Enables support for **worklets** in `react-native-reanimated`.
  - Worklets are JavaScript functions that run on the **UI thread** instead of the JavaScript thread.
  - This ensures smoother animations by reducing the dependency on the JavaScript thread, which may be busy handling other tasks (e.g., network requests or UI updates).
- Transforms functions marked with `worklet` into a format suitable for execution on the UI thread.

**Example Worklet**:
```javascript
import { useSharedValue, withSpring } from 'react-native-reanimated';

const sharedValue = useSharedValue(0);

const handlePress = () => {
  'worklet'; // Marks this function for execution on the UI thread
  sharedValue.value = withSpring(100);
};
```

**Without this plugin**:
- Worklets would fail to compile, causing errors like `Unknown worklet function`.
- Animations may run inefficiently on the JavaScript thread, leading to laggy performance.

---

### **How It Works Together**

1. **Metro React Native Babel Preset**:
   - Ensures the entire React Native codebase, including JSX, ES6+, and React Native-specific syntax, is properly compiled.

2. **Reanimated Plugin**:
   - Adds support for the worklet architecture of `react-native-reanimated`, enabling highly performant animations.

When Babel processes your project files:
- The `presets` first apply generic React Native and JavaScript transformations.
- The `plugins` then apply specific transformations, such as converting worklets for `react-native-reanimated`.

---

### **Deep Dive: Why Worklets Are Important**

#### **Problem with JavaScript Thread Animations**
In React Native, animations are traditionally calculated on the **JavaScript thread**. However:
- The JavaScript thread might be busy with other tasks (e.g., processing API calls, updating state), causing animation stutters.
- This can lead to a poor user experience, especially during complex interactions like dragging or swiping.

#### **Worklets as a Solution**
Worklets in `react-native-reanimated`:
- Run directly on the **UI thread**, ensuring animations remain smooth regardless of JavaScript thread activity.
- Handle gesture-driven animations (e.g., drag, pinch, swipe) with minimal delay.

**How the Plugin Enables Worklets**:
- It converts worklet functions into serialized strings and transfers them to the UI thread.
- These serialized functions are executed independently, bypassing the JavaScript thread.

---

### **Example Usage**

#### **Before Adding the Plugin**
```javascript
import { useSharedValue } from 'react-native-reanimated';

const sharedValue = useSharedValue(0);

const handlePress = () => {
  sharedValue.value = 100; // Runs on JavaScript thread, may cause lag
};
```

- Animations may stutter if the JavaScript thread is busy.

#### **After Adding the Plugin**
```javascript
import { useSharedValue } from 'react-native-reanimated';

const sharedValue = useSharedValue(0);

const handlePress = () => {
  'worklet'; // Executes on UI thread
  sharedValue.value = 100; // Smooth animation
};
```

- The `react-native-reanimated/plugin` ensures `handlePress` is serialized and executed on the UI thread, leading to better performance.

---

### **Summary**

1. **`presets`**:
   - Compile React Native and modern JavaScript features for compatibility with Metro bundler.
   - Required for JSX, ES6+, and other React Native-specific syntax.

2. **`plugins`**:
   - Add support for worklets in `react-native-reanimated`.
   - Enables animations to run on the UI thread, improving performance and reducing lag.

3. **Why Both Are Necessary**:
   - `metro-react-native-babel-preset` ensures the app compiles and runs.
   - `react-native-reanimated/plugin` optimizes animations for smooth, UI-thread-driven execution.

---

### **Difference Between `react-native-reanimated` and `runTiming` with Skia**

Both **`react-native-reanimated`** and **Skia's `runTiming`** are animation tools, but they are designed for different purposes and operate differently. Here’s a detailed comparison to help you understand when and why to use each:

---

### **1. Overview**

| Feature                        | `react-native-reanimated`                    | Skia's `runTiming`                           |
|--------------------------------|---------------------------------------------|---------------------------------------------|
| **Purpose**                    | General-purpose animations for React Native UI elements. | Specialized animations for Skia-rendered graphics. |
| **Thread Execution**           | Animations run on the **UI thread** via **worklets**. | Animations are directly tied to Skia’s rendering pipeline. |
| **Scope**                      | Can animate any React Native components (e.g., `View`, `Text`). | Only animates Skia graphics (e.g., `Circle`, `Path`). |
| **Integration**                | Works seamlessly with gestures from `react-native-gesture-handler`. | Works primarily with Skia’s drawing primitives. |
| **Performance**                | Optimized for smooth animations across the React Native UI. | Extremely performant for GPU-rendered graphics. |
| **Ease of Use**                | Requires setup for shared values, worklets, and gesture handlers. | Simpler for Skia-specific animations; no extra setup needed. |

---

### **2. Execution Model**

#### **`react-native-reanimated`**
- Animations are calculated on the **UI thread** using **worklets**, independent of the JavaScript thread.
- Useful for animating React Native components (`View`, `Image`, etc.).
- Supports gesture-driven animations with tools like `useAnimatedGestureHandler`.

**Example**:
```tsx
import Animated, { useSharedValue, withSpring } from 'react-native-reanimated';

const Example = () => {
  const translateX = useSharedValue(0);

  const animatedStyle = useAnimatedStyle(() => ({
    transform: [{ translateX: translateX.value }],
  }));

  const onPress = () => {
    translateX.value = withSpring(100);
  };

  return (
    <Animated.View style={[styles.box, animatedStyle]} onTouchStart={onPress} />
  );
};
```

- **Flow**:
  - A `sharedValue` tracks the animation state.
  - `useAnimatedStyle` connects the `sharedValue` to the component’s style.
  - `withSpring` drives the animation.

---

#### **Skia's `runTiming`**
- Animations are tightly coupled to Skia’s rendering pipeline and work directly on GPU-rendered elements.
- Provides smooth, frame-perfect animations for Skia elements like `Circle`, `Path`, and `Rect`.
- No interaction with React Native UI components.

**Example**:
```tsx
import { Canvas, Circle, useValue, runTiming, Easing } from '@shopify/react-native-skia';

const Example = () => {
  const radius = useValue(50);

  useEffect(() => {
    runTiming(radius, 100, { duration: 2000, easing: Easing.inOut(Easing.cubic) });
  }, []);

  return (
    <Canvas style={{ flex: 1 }}>
      <Circle cx={150} cy={150} r={radius} color="blue" />
    </Canvas>
  );
};
```

- **Flow**:
  - A Skia `useValue` tracks the animation state.
  - `runTiming` interpolates the value over time.
  - The `Circle` component reads the animated value directly.

---

### **3. When to Use `react-native-reanimated`**

#### **Best for:**
- Animating React Native components (e.g., `View`, `Text`, `Image`).
- Gesture-driven UI interactions (e.g., drag, swipe, pinch).
- Cross-screen animations (e.g., transitions between screens).
- Combining animations with gesture handlers for non-Skia elements.

#### **Strengths**:
- Broad scope: Works across the entire React Native UI.
- Rich API: Includes easing functions like `withSpring`, `withTiming`, and gesture handlers.
- Reusable: Can animate multiple properties or components simultaneously.

#### **Limitations**:
- Indirect control of Skia-rendered graphics.
- Slightly more complex to set up compared to Skia's built-in tools.

---

### **4. When to Use Skia's `runTiming`**

#### **Best for:**
- Animating Skia-rendered elements (e.g., `Circle`, `Path`, `Rect`).
- High-performance, GPU-bound animations (e.g., stock charts, graphs).
- Custom visuals like gradients, dynamic paths, or real-time updates.
- Animating graphics within Skia `Canvas`.

#### **Strengths**:
- Simple setup: Built into Skia’s animation pipeline.
- Extremely efficient for graphics: Tied directly to Skia’s GPU rendering.
- Seamless integration with Skia components (no React Native components needed).

#### **Limitations**:
- Limited scope: Can’t animate standard React Native components.
- Doesn’t integrate directly with gesture-driven animations (you need `react-native-gesture-handler` for that).

---

### **5. Combining `react-native-reanimated` and Skia**

For advanced use cases, you can combine both tools:
- Use `react-native-reanimated` for gesture detection and shared values.
- Use Skia's `runTiming` for animating Skia-specific properties.

**Example: Drag and Scale a Circle**
```tsx
import { Canvas, Circle, useValue } from '@shopify/react-native-skia';
import { GestureDetector, GestureHandlerRootView, PanGestureHandler } from 'react-native-gesture-handler';
import Animated, { useSharedValue, useAnimatedGestureHandler, useAnimatedProps } from 'react-native-reanimated';

const CombinedExample = () => {
  const x = useSharedValue(150);
  const y = useSharedValue(150);
  const radius = useValue(50);

  const gestureHandler = useAnimatedGestureHandler({
    onActive: (event) => {
      x.value = event.translationX + 150;
      y.value = event.translationY + 150;
    },
  });

  const animatedProps = useAnimatedProps(() => ({
    cx: x.value,
    cy: y.value,
  }));

  useEffect(() => {
    runTiming(radius, 100, { duration: 2000 });
  }, []);

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <PanGestureHandler onGestureEvent={gestureHandler}>
        <Canvas style={{ flex: 1 }}>
          <Animated.Circle r={radius} color="blue" animatedProps={animatedProps} />
        </Canvas>
      </PanGestureHandler>
    </GestureHandlerRootView>
  );
};

export default CombinedExample;
```

---

### **Key Takeaways**

| Use Case                                 | `react-native-reanimated`                          | Skia's `runTiming`                             |
|------------------------------------------|--------------------------------------------------|-----------------------------------------------|
| Animating UI components                  |  Yes                                           | ❌ No                                         |
| Animating Skia-rendered graphics         | ⚠️ Indirectly, via props                        |  Yes                                         |
| Gesture-driven animations                |  Yes                                           | ⚠️ Requires `react-native-gesture-handler`   |
| Real-time GPU-bound graphics             | ❌ No                                            |  Yes                                         |
| Combining gestures and animations        |  Yes                                           | ⚠️ Combine with `react-native-reanimated`   |

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
