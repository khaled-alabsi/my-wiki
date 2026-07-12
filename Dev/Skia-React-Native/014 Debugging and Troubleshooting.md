### **13. Debugging and Troubleshooting in Skia**

Debugging Skia-rendered applications involves identifying issues in rendering, animations, performance, or gesture handling. Below, we’ll discuss common issues, their fixes, and techniques for debugging performance and rendering glitches.

---

### **1. Common Issues and Fixes**

#### **a. Blank Canvas**
**Symptoms**:
- The `Canvas` doesn’t display anything.

**Possible Causes**:
1. **Gesture Handler Setup**:
   - Missing `GestureHandlerRootView`.
   - Incorrect import or missing configuration for `react-native-gesture-handler`.

   **Fix**:
   ```tsx
   import 'react-native-gesture-handler';
   ```

2. **Incorrect Canvas Styling**:
   - Canvas `style` doesn’t occupy the screen.

   **Fix**:
   ```tsx
   <Canvas style={{ flex: 1 }} />
   ```

3. **Error in Rendering Components**:
   - Elements (`Circle`, `Path`, etc.) might have invalid or missing properties.

   **Fix**:
   - Verify required properties (e.g., `cx`, `cy`, `color`) are provided.
   - Use `console.log` or debugging tools to check values.

---

#### **b. Flickering Animations**
**Symptoms**:
- Animations appear jittery or unstable.

**Possible Causes**:
1. **Overusing React State**:
   - Frequent React re-renders due to `useState` updates can cause flickering.

   **Fix**:
   - Use `useValue` for Skia animations instead of React state.

   **Example**:
   ```tsx
   const animatedValue = useValue(0);
   useEffect(() => {
     runTiming(animatedValue, 1, { duration: 2000 });
   }, []);
   ```

2. **Excessive Recalculations**:
   - Recomputing paths or elements on every frame.

   **Fix**:
   - Precompute paths outside of animation loops.
   ```tsx
   const path = Skia.Path.Make();
   // Define path once
   ```

---

#### **c. Gesture Issues**
**Symptoms**:
- Gestures (e.g., drag, pinch) don’t work or are unresponsive.

**Possible Causes**:
1. **Missing GestureHandlerRootView**:
   - Gestures require the root view wrapper.

   **Fix**:
   ```tsx
   import { GestureHandlerRootView } from 'react-native-gesture-handler';
   ```

2. **Improper Gesture Handling**:
   - Missing `onGestureEvent` or incorrect binding of event handlers.

   **Fix**:
   - Ensure `GestureDetector` wraps the interactive component:
   ```tsx
   <GestureDetector onGestureEvent={handleGesture}>
   ```

3. **Conflicting Gesture Priority**:
   - Multiple gestures (e.g., scroll + pinch) conflict.

   **Fix**:
   - Adjust gesture priority using `simultaneousHandlers` or `waitFor`.

---

#### **d. Performance Lag**
**Symptoms**:
- Low frame rates or stuttering during animations.

**Possible Causes**:
1. **Excessive Overdraw**:
   - Too many overlapping elements are rendered.

   **Fix**:
   - Use clipping (`clipRect`, `clipPath`) to limit drawing to visible regions.

2. **Inefficient Animations**:
   - Animating too many elements individually.

   **Fix**:
   - Group animations where possible using `Group`:
   ```tsx
   <Group transform={[{ rotate: animatedRotation }]}>
   ```

3. **Unnecessary Updates**:
   - Re-rendering static elements every frame.

   **Fix**:
   - Pre-render static elements as images:
   ```tsx
   const staticImage = Skia.Image.MakeFromEncoded(require('./static-image.png'));
   ```

---

### **2. Debugging Performance and Rendering Glitches**

#### **a. Skia’s Debugging Features**
Skia provides built-in tools for debugging rendering issues.

1. **Debug Overdraw**:
   - Visualize overdraw by enabling Skia's debug overdraw mode.

   **Example**:
   ```tsx
   Skia.setDebugOverdraw(true);
   ```

2. **Profile Render Times**:
   - Use Skia’s profiling tools to measure rendering times for individual components.

#### **b. Debugging Tools in React Native**
1. **Flipper**:
   - Use Flipper’s performance monitoring to track frame rates, memory usage, and more.

   **Setup**:
   - Install Flipper and enable the React Native plugin.

2. **Console Logs for Debugging Properties**:
   - Print the properties of Skia elements to verify values during rendering:
   ```tsx
   console.log(`Circle cx: ${cx}, cy: ${cy}`);
   ```

3. **React DevTools**:
   - Inspect the component tree to verify state and props.

---

#### **c. Debugging Animations**
1. **Track Animation Values**:
   - Log animation values during transitions:
   ```tsx
   useEffect(() => {
     animatedValue.addListener((value) => console.log(value));
   }, []);
   ```

2. **Simplify Animations for Debugging**:
   - Temporarily reduce the complexity of animations to isolate issues:
   ```tsx
   runTiming(animatedValue, 1, { duration: 500 });
   ```

---

#### **d. Debugging Gesture Interactions**
1. **Log Gesture Events**:
   - Print gesture details to verify behavior:
   ```tsx
   const handleGesture = (event) => {
     console.log(event.nativeEvent);
   };
   ```

2. **Verify Gesture Boundaries**:
   - Ensure the interactive area matches user expectations by logging the bounds.

---

### **Applications in TradeChampion**

1. **Debugging Stock Charts**:
   - Use Skia’s debug overdraw mode to optimize rendering for large datasets.
   - Log animation progress to ensure smooth updates.

2. **Interactive Portfolio Views**:
   - Profile gesture interactions to verify responsiveness.
   - Debug clipping regions for efficient rendering of pie charts or bar graphs.

3. **Live Market Updates**:
   - Monitor frame rates during real-time updates.
   - Optimize data flow to minimize unnecessary re-renders.

---

### **Key Takeaways**
1. **Common Issues**:
   - Blank canvas (fix: gesture setup, styling).
   - Flickering animations (fix: use `useValue`, minimize recalculations).
   - Gesture problems (fix: proper setup and conflict resolution).

2. **Debugging Tools**:
   - Use Skia’s `setDebugOverdraw` and Flipper’s performance monitoring.
   - Leverage console logs and React DevTools for state verification.

3. **Performance Optimization**:
   - Reduce overdraw with clipping.
   - Batch animations and pre-render static elements.

