### **8. Layering and Grouping in Skia**

Layering and grouping allow you to manage the organization and rendering order of multiple elements in Skia. This is useful for compositing complex scenes and controlling the visual stacking of elements.

---

### **Key Concepts**

1. **`Group` for Compositing**:
   - The `Group` component acts as a container for multiple Skia elements.
   - You can apply transformations, opacity, and blend modes to the entire group rather than individual elements.

2. **Managing Z-Index**:
   - In Skia, the drawing order determines the stacking (z-index) of elements.
   - Elements drawn later in the code will appear on top of earlier ones.

---

### **1. Using `Group` for Compositing**

#### **a. Basic Group Example**

```tsx
import { Canvas, Group, Circle, Rect } from '@shopify/react-native-skia';

<Canvas style={{ flex: 1 }}>
  <Group>
    <Rect x={50} y={50} width={100} height={100} color="blue" />
    <Circle cx={100} cy={100} r={50} color="red" />
  </Group>
</Canvas>;
```

- **Result**: A blue rectangle and a red circle are grouped together. Transformations or opacity applied to the `Group` affect both elements.

---

#### **b. Applying Transformations to a Group**

```tsx
<Canvas style={{ flex: 1 }}>
  <Group transform={[{ rotate: Math.PI / 4 }, { translateX: 50 }]}>
    <Rect x={50} y={50} width={100} height={100} color="blue" />
    <Circle cx={100} cy={100} r={50} color="red" />
  </Group>
</Canvas>;
```

- **Transformations**:
  - The entire group is rotated by 45° (π/4 radians).
  - The group is also translated 50 units along the x-axis.

---

#### **c. Group with Opacity**

```tsx
<Canvas style={{ flex: 1 }}>
  <Group opacity={0.5}>
    <Rect x={50} y={50} width={100} height={100} color="green" />
    <Circle cx={100} cy={100} r={50} color="orange" />
  </Group>
</Canvas>;
```

- **Result**: The group’s opacity is reduced to 50%, making both the rectangle and circle semi-transparent.

---

#### **d. Group with Blend Mode**

```tsx
<Canvas style={{ flex: 1 }}>
  <Group blendMode="screen">
    <Circle cx={100} cy={100} r={50} color="blue" />
    <Circle cx={130} cy={100} r={50} color="yellow" />
  </Group>
</Canvas>;
```

- **Blend Mode**: The `"screen"` blend mode creates a lighter color where the two circles overlap.

---

### **2. Managing Z-Index**

In Skia, there is no explicit `z-index` property. Instead, the **drawing order** determines which elements appear on top.

#### **a. Layering by Drawing Order**

```tsx
<Canvas style={{ flex: 1 }}>
  <Circle cx={100} cy={100} r={50} color="blue" />
  <Rect x={75} y={75} width={100} height={100} color="red" />
</Canvas>;
```

- **Result**: The rectangle appears on top of the circle because it is drawn after the circle in the code.

---

#### **b. Using Groups for Layer Management**

You can organize elements into layers by grouping them and arranging the groups in order.

```tsx
<Canvas style={{ flex: 1 }}>
  {/* Background Layer */}
  <Group>
    <Rect x={0} y={0} width={300} height={300} color="lightgray" />
  </Group>

  {/* Foreground Layer */}
  <Group>
    <Circle cx={150} cy={150} r={75} color="blue" />
    <Rect x={125} y={125} width={50} height={50} color="red" />
  </Group>
</Canvas>;
```

- **Result**: The background layer is rendered first, followed by the foreground layer.

---

### **3. Advanced Grouping and Layering**

#### **a. Nested Groups**
You can nest groups for hierarchical transformations.

```tsx
<Canvas style={{ flex: 1 }}>
  <Group transform={[{ translateX: 50 }]}>
    {/* Outer Group */}
    <Group transform={[{ rotate: Math.PI / 6 }]}>
      {/* Inner Group */}
      <Circle cx={100} cy={100} r={50} color="green" />
      <Rect x={75} y={75} width={50} height={50} color="purple" />
    </Group>
  </Group>
</Canvas>;
```

- **Result**: The outer group translates the inner group, and the inner group applies its own rotation.

---

#### **b. Mixing Groups and Blend Modes**

Combine layering with blend modes for complex visuals.

```tsx
<Canvas style={{ flex: 1 }}>
  {/* Layer 1 */}
  <Group blendMode="multiply">
    <Circle cx={100} cy={100} r={75} color="blue" />
  </Group>

  {/* Layer 2 */}
  <Group blendMode="screen">
    <Circle cx={150} cy={150} r={75} color="yellow" />
  </Group>
</Canvas>;
```

- **Result**: The circles blend differently based on their blend modes, creating unique overlap effects.

---

### **Applications for TradeChampion**

1. **Stock Chart Layers**:
   - Use groups for background grids, chart lines, and data points.
   - Apply opacity to layers for a clear focus on trends.

2. **Portfolio Visualization**:
   - Layer pie chart sectors with nested groups for interactive highlights.
   - Add blend modes to emphasize growth areas dynamically.

3. **News Highlights**:
   - Group headlines and images for cohesive visual effects.
   - Apply transformations to move or scale entire sections interactively.

