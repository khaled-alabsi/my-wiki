### **Shapes in Skia: Circle, Rect, Line, and Path**

In Skia, shapes are the building blocks for drawing visuals on the canvas. These primitives allow you to create various 2D graphics, each with unique properties and use cases.

---

### **1. Circle**

The `Circle` component draws a circular shape.

#### **Key Properties:**
- `cx`: x-coordinate of the center.
- `cy`: y-coordinate of the center.
- `r`: Radius of the circle.
- `color`: Fill color of the circle.
- `style`: `"fill"` (default) or `"stroke"`.
- `strokeWidth`: Width of the stroke when `style="stroke"`.

#### **Example:**
```tsx
<Canvas style={{ flex: 1 }}>
  <Circle cx={100} cy={100} r={50} color="blue" />
  <Circle cx={200} cy={200} r={30} color="red" style="stroke" strokeWidth={5} />
</Canvas>
```

---

### **2. Rect**

The `Rect` component draws a rectangular shape.

#### **Key Properties:**
- `x`: x-coordinate of the top-left corner.
- `y`: y-coordinate of the top-left corner.
- `width`: Width of the rectangle.
- `height`: Height of the rectangle.
- `color`: Fill color of the rectangle.
- `style`: `"fill"` (default) or `"stroke"`.
- `strokeWidth`: Width of the stroke when `style="stroke"`.

#### **Example:**
```tsx
<Canvas style={{ flex: 1 }}>
  <Rect x={50} y={50} width={100} height={100} color="green" />
  <Rect x={200} y={200} width={80} height={40} color="purple" style="stroke" strokeWidth={4} />
</Canvas>
```

---

### **3. Line**

The `Line` component is used to draw straight lines between two points.

#### **Key Properties:**
- `p1`: Starting point of the line as `{ x: number, y: number }`.
- `p2`: Ending point of the line as `{ x: number, y: number }`.
- `color`: Color of the line.
- `strokeWidth`: Width of the line.

#### **Example:**
```tsx
<Canvas style={{ flex: 1 }}>
  <Line p1={{ x: 50, y: 50 }} p2={{ x: 200, y: 200 }} color="black" strokeWidth={2} />
  <Line p1={{ x: 100, y: 50 }} p2={{ x: 100, y: 200 }} color="red" strokeWidth={5} />
</Canvas>
```

---

### **4. Path**

The `Path` component allows you to draw custom shapes and complex lines, such as curves and polygons.

#### **Key Properties:**
- `path`: A Skia `Path` object that defines the shape.
- `color`: Fill or stroke color for the path.
- `style`: `"fill"` (default) or `"stroke"`.
- `strokeWidth`: Width of the stroke when `style="stroke"`.

#### **Creating a Path:**
Use the `Skia.Path.Make()` function to create and manipulate paths.

#### **Example:**
```tsx
import { Skia } from '@shopify/react-native-skia';

const path = Skia.Path.Make();
path.moveTo(50, 50); // Start at (50, 50)
path.lineTo(150, 50); // Draw a line to (150, 50)
path.lineTo(100, 150); // Draw a line to (100, 150)
path.close(); // Close the path to create a triangle

<Canvas style={{ flex: 1 }}>
  <Path path={path} color="blue" style="fill" />
</Canvas>
```

---

### **Combining Shapes**

You can mix and match shapes to create more complex visuals:

#### **Example:**
```tsx
<Canvas style={{ flex: 1 }}>
  <Circle cx={100} cy={100} r={50} color="blue" />
  <Rect x={50} y={200} width={100} height={50} color="green" />
  <Line p1={{ x: 200, y: 50 }} p2={{ x: 200, y:200 }} color="red" strokeWidth={3} />
</Canvas>
```

---

### **Paint and Color in Skia**

In Skia, the `Paint` object controls the **appearance** of shapes, such as their color, gradient, stroke width, and style. Skia offers great flexibility for customizing visuals.

---

### **Key Concepts**

1. **`color`**:
   - The most basic property for filling or stroking shapes.
   - Accepts:
     - **HEX codes**: e.g., `"#FF0000"` for red.
     - **Color names**: e.g., `"blue"`, `"green"`.
     - **RGBA values**: e.g., `"rgba(255, 0, 0, 0.5)"` for semi-transparent red.

2. **`strokeWidth`**:
   - Defines the thickness of a shape’s border when using the `"stroke"` style.
   - Applies to `Circle`, `Rect`, `Line`, and `Path`.

3. **`style`**:
   - Determines whether the shape is **filled** or only **stroked** (outlined).
   - Options:
     - `"fill"`: Fills the interior of the shape (default).
     - `"stroke"`: Draws only the outline of the shape.

4. **`blendMode`**:
   - Defines how the colors of overlapping shapes blend.
   - Example modes:
     - `"source-over"`: Default, shapes overlap normally.
     - `"multiply"`: Multiplies the colors of overlapping shapes.
     - `"screen"`: Creates a lighter effect for overlapping colors.

5. **Gradients and Shaders**:
   - Apply advanced fills like linear and radial gradients.

---

### **Examples of Paint Properties**

#### **1. Simple Color**
Each shape can have its own color:

```tsx
<Canvas style={{ flex: 1 }}>
  <Circle cx={100} cy={100} r={50} color="blue" />
  <Rect x={200} y={100} width={100} height={50} color="#FF5722" />
</Canvas>
```

---

#### **2. Stroke Width and Style**

```tsx
<Canvas style={{ flex: 1 }}>
  <Circle cx={100} cy={100} r={50} color="green" style="stroke" strokeWidth={5} />
  <Rect x={200} y={100} width={100} height={50} color="red" style="stroke" strokeWidth={8} />
</Canvas>
```

---

#### **3. Gradients**

Skia allows you to use gradients for filling shapes.

- **Linear Gradient**:
  ```tsx
  import { LinearGradient, Rect } from '@shopify/react-native-skia';

  <Canvas style={{ flex: 1 }}>
    <Rect
      x={50}
      y={50}
      width={200}
      height={100}
      color={
        <LinearGradient
          colors={["blue", "green"]}
          start={{ x: 50, y: 50 }}
          end={{ x: 250, y: 50 }}
        />
      }
    />
  </Canvas>
  ```

- **Radial Gradient**:
  ```tsx
  import { RadialGradient, Circle } from '@shopify/react-native-skia';

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
  </Canvas>
  ```

---

#### **4. Blend Modes**

Blend modes define how colors interact when shapes overlap:

```tsx
import { Paint, Rect } from '@shopify/react-native-skia';

<Canvas style={{ flex: 1 }}>
  <Rect x={50} y={50} width={100} height={100} color="blue" />
  <Rect
    x={100}
    y={100}
    width={100}
    height={100}
    color="red"
    paint={Paint({ blendMode: "multiply" })}
  />
</Canvas>
```

Here, the overlapping part of the blue and red rectangles will have a purple hue due to the `"multiply"` blend mode.

---

#### **5. Transparency (Opacity)**

Use RGBA values or a color name with an alpha channel:

```tsx
<Canvas style={{ flex: 1 }}>
  <Circle cx={100} cy={100} r={50} color="rgba(0, 0, 255, 0.5)" />
  <Rect x={200} y={100} width={100} height={50} color="#FF572280" />
</Canvas>
```

---

### **Combining Paint with Shapes**

You can attach custom `Paint` objects for more advanced visual effects. For example:

```tsx
import { Paint, Circle } from '@shopify/react-native-skia';

const myPaint = Paint({
  color: "blue",
  strokeWidth: 10,
  style: "stroke",
});

<Canvas style={{ flex: 1 }}>
  <Circle cx={150} cy={150} r={100} paint={myPaint} />
</Canvas>
```

---

### **Custom Shaders and Compositing Multiple Shapes in Skia**

#### **1. Custom Shaders**

Shaders allow you to create advanced visual effects, such as textured fills, complex gradients, and procedural patterns. Skia supports built-in shaders and custom GLSL-like shaders for ultimate flexibility.

---

##### **Types of Shaders**

1. **Gradient Shaders**:
   - Linear and radial gradients, as seen earlier.
2. **Image Shaders**:
   - Use images to fill shapes.
3. **Custom GLSL-Like Shaders**:
   - Write custom fragment shaders for advanced effects.

---

##### **Using Image Shaders**

You can use an image as a fill for a shape.

**Example**:
```tsx
import { ImageShader, Rect } from '@shopify/react-native-skia';
import { Skia } from '@shopify/react-native-skia';

const image = Skia.Image.MakeFromEncoded(require('./assets/texture.png'));

<Canvas style={{ flex: 1 }}>
  <Rect
    x={50}
    y={50}
    width={200}
    height={100}
    color={ImageShader(image, { tx: "repeat", ty: "repeat" })}
  />
</Canvas>
```
- `tx` and `ty`: Define how the image repeats or clamps on the x and y axes.

---

##### **Custom Fragment Shaders**

To write custom shaders, you define GLSL-like code as a string.

**Example: Wave Shader**:
```tsx
import { Shaders, Shader, Rect } from '@shopify/react-native-skia';

const waveShader = Shaders.create(`
  uniform vec2 u_resolution;
  uniform float u_time;

  vec4 main(vec2 fragCoord) {
    vec2 uv = fragCoord / u_resolution;
    float wave = sin(uv.y * 10.0 + u_time) * 0.5 + 0.5;
    return vec4(wave, wave, wave, 1.0);
  }
`);

<Canvas style={{ flex: 1 }}>
  <Rect
    x={0}
    y={0}
    width={300}
    height={300}
    color={Shader(waveShader, { u_resolution: [300, 300], u_time: 0.5 })}
  />
</Canvas>
```

- **Inputs**:
  - `u_resolution`: The dimensions of the shape being drawn.
  - `u_time`: A time-based uniform for animations.

---

#### **2. Compositing Multiple Shapes**

Compositing involves combining multiple shapes or layers into a single visual element. Skia provides `Group` and blending modes for this purpose.

---

##### **Using Group**

The `Group` component allows you to combine multiple shapes and apply transformations, opacity, or effects to the entire group.

**Example: Transforming a Group**:
```tsx
import { Canvas, Group, Circle, Rect } from '@shopify/react-native-skia';

<Canvas style={{ flex: 1 }}>
  <Group transform={[{ rotate: Math.PI / 4 }, { translateX: 50 }]}>
    <Circle cx={100} cy={100} r={50} color="blue" />
    <Rect x={150} y={100} width={100} height={50} color="red" />
  </Group>
</Canvas>
```
- The entire group is rotated by 45° and translated by 50 units.

---

##### **Using Blend Modes**

Blend modes allow you to define how overlapping shapes interact visually.

**Example: Overlaying Circles with Blend Modes**:
```tsx
import { Canvas, Circle, Group } from '@shopify/react-native-skia';

<Canvas style={{ flex: 1 }}>
  <Group blendMode="screen">
    <Circle cx={100} cy={100} r={50} color="blue" />
    <Circle cx={150} cy={100} r={50} color="red" />
    <Circle cx={125} cy={150} r={50} color="green" />
  </Group>
</Canvas>
```
- **Blend Mode**: `"screen"` creates a lighter color for overlapping areas.

---

##### **Combining Group and Shaders**

You can mix compositing techniques with shaders for complex visuals.

**Example: Group with Gradient Shader**:
```tsx
import { Canvas, Group, Circle, LinearGradient } from '@shopify/react-native-skia';

<Canvas style={{ flex: 1 }}>
  <Group>
    <Circle
      cx={100}
      cy={100}
      r={75}
      color={
        <LinearGradient
          colors={["blue", "cyan"]}
          start={{ x: 50, y: 50 }}
          end={{ x: 150, y: 150 }}
        />
      }
    />
    <Circle
      cx={200}
      cy={200}
      r={75}
      color="rgba(255, 0, 0, 0.5)"
    />
  </Group>
</Canvas>
```

---

### **Applications for TradeChampion**

1. **Custom Stock Charts**:
   - Use shaders for visually appealing backgrounds or chart highlights.
   - Compose paths and shapes for candlestick charts.

2. **Wealth Tab Visuals**:
   - Group pie chart segments with shared transformations (e.g., rotating to highlight a slice).
   - Use image shaders for portfolio textures or themes.

3. **Dynamic News Overlays**:
   - Blend headlines with background visuals using compositing and shaders.

---
