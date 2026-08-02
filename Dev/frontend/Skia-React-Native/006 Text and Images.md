### **6. Working with Text and Images in Skia**

Skia provides flexible options for rendering text and images. This includes customizing fonts, aligning text, applying styles, and transforming images (e.g., scaling, rotating, or tiling).

---

### **Rendering Text**

#### **1. Text Basics**

The `Text` component allows you to render text on the canvas.

#### **Key Properties:**
- **`text`**: The content of the text.
- **`x` / `y`**: The position of the text.
- **`fontSize`**: The size of the text.
- **`color`**: The color of the text.
- **`font`**: A custom font created using `Skia.Font`.

#### **Example: Simple Text**
```tsx
import { Canvas, Text, Skia } from '@shopify/react-native-skia';

const MyText = () => {
  const font = Skia.Font(Skia.Typeface.MakeDefault(), 24);

  return (
    <Canvas style={{ flex: 1 }}>
      <Text x={50} y={100} text="Hello, Skia!" font={font} color="blue" />
    </Canvas>
  );
};

export default MyText;
```

---

#### **2. Aligning and Styling Text**
You can adjust text alignment, size, and style.

**Example: Multiple Styles**
```tsx
import { Canvas, Text, Skia } from '@shopify/react-native-skia';

const MyStyledText = () => {
  const font = Skia.Font(Skia.Typeface.MakeDefault(), 32);

  return (
    <Canvas style={{ flex: 1 }}>
      <Text x={50} y={100} text="Bold Text" font={font} color="black" />
      <Text x={50} y={150} text="Red Text" font={font} color="red" />
    </Canvas>
  );
};

export default MyStyledText;
```

---

#### **3. Using Custom Fonts**
To use custom fonts, load a font file.

**Example: Loading a Custom Font**
```tsx
import { Skia, Text, Canvas } from '@shopify/react-native-skia';

const customFont = Skia.Font(
  Skia.Typeface.MakeFromFile(require('./assets/custom-font.ttf')),
  24
);

<Canvas style={{ flex: 1 }}>
  <Text x={50} y={100} text="Custom Font" font={customFont} color="green" />
</Canvas>;
```

---

#### **4. Animated Text**
You can animate text properties such as position or size using `useValue`.

**Example: Animating Text Position**
```tsx
import { Canvas, Text, useValue, runTiming, Easing } from '@shopify/react-native-skia';

const AnimatedText = () => {
  const y = useValue(50);

  useEffect(() => {
    runTiming(y, 200, { duration: 2000, easing: Easing.inOut(Easing.cubic) });
  }, []);

  const font = Skia.Font(Skia.Typeface.MakeDefault(), 24);

  return (
    <Canvas style={{ flex: 1 }}>
      <Text x={100} y={y} text="Moving Text" font={font} color="blue" />
    </Canvas>
  );
};

export default AnimatedText;
```

---

### **Drawing Images**

#### **1. Image Basics**

You can render images using the `Image` component. Images are loaded with `Skia.Image.MakeFromEncoded`.

**Example: Rendering an Image**
```tsx
import { Canvas, Image } from '@shopify/react-native-skia';
import { Skia } from '@shopify/react-native-skia';

const MyImage = () => {
  const image = Skia.Image.MakeFromEncoded(require('./assets/sample.jpg'));

  return (
    <Canvas style={{ flex: 1 }}>
      <Image image={image} x={50} y={50} width={200} height={150} />
    </Canvas>
  );
};

export default MyImage;
```

---

#### **2. Image Transformations**

You can scale, rotate, and position images.

**Example: Scaling an Image**
```tsx
<Canvas style={{ flex: 1 }}>
  <Image
    image={image}
    x={50}
    y={50}
    width={imageWidth * 1.5} // Scale width
    height={imageHeight * 1.5} // Scale height
  />
</Canvas>
```

**Example: Rotating an Image**
```tsx
import { Group, Canvas, Image } from '@shopify/react-native-skia';

<Canvas style={{ flex: 1 }}>
  <Group transform={[{ rotate: Math.PI / 4 }]}>
    <Image image={image} x={100} y={100} width={200} height={150} />
  </Group>
</Canvas>;
```

---

#### **3. Image as a Shader**

Use an image as a shader to fill other shapes.

**Example: Image Shader**
```tsx
import { ImageShader, Rect, Canvas } from '@shopify/react-native-skia';

<Canvas style={{ flex: 1 }}>
  <Rect
    x={50}
    y={50}
    width={300}
    height={200}
    color={ImageShader(image, { tx: "repeat", ty: "repeat" })}
  />
</Canvas>;
```

---

#### **4. Animated Images**
Animate image properties like position or opacity.

**Example: Moving an Image**
```tsx
import { Canvas, Image, useValue, runTiming, Easing } from '@shopify/react-native-skia';

const AnimatedImage = () => {
  const x = useValue(50);

  useEffect(() => {
    runTiming(x, 250, { duration: 2000, easing: Easing.inOut(Easing.cubic) });
  }, []);

  const image = Skia.Image.MakeFromEncoded(require('./assets/sample.jpg'));

  return (
    <Canvas style={{ flex: 1 }}>
      <Image image={image} x={x} y={100} width={200} height={150} />
    </Canvas>
  );
};

export default AnimatedImage;
```

---

### **Applications for TradeChampion**

1. **Stock Labels with Text**:
   - Display stock names, prices, and trends directly on charts.
   - Animate text to highlight significant price changes.

2. **Dynamic News Visuals**:
   - Render headlines and descriptions overlaid with images of companies or sectors.

3. **Portfolio Visualization**:
   - Use images as shaders for custom textures (e.g., fill sectors of a pie chart with relevant company logos).

4. **Interactive Overlays**:
   - Allow users to annotate images or interact with text-based highlights.

---

### **Clipping and Masking with Text and Images in Skia**

Clipping and masking are advanced techniques to constrain or blend visuals. They allow you to:
- Restrict drawing within a specific shape or path (clipping).
- Use one shape (mask) to reveal or hide parts of another (masking).

---

### **1. Clipping in Skia**

Clipping defines a region beyond which rendering is restricted. Anything drawn outside the clipping region is not visible.

#### **Key Methods**
- **`clipRect()`**: Clip to a rectangular region.
- **`clipPath()`**: Clip to a custom path (e.g., circles, polygons).

---

#### **Example: Clipping with a Rectangle**

```tsx
import { Canvas, Rect, Circle, useCanvas } from '@shopify/react-native-skia';

const ClippedDrawing = () => {
  const canvas = useCanvas();

  return (
    <Canvas style={{ flex: 1 }}>
      <Rect x={50} y={50} width={200} height={200} color="lightgray" />

      {/* Apply a clipping rectangle */}
      {canvas.clipRect(50, 50, 200, 200)}

      {/* This circle will be clipped */}
      <Circle cx={150} cy={150} r={100} color="blue" />
    </Canvas>
  );
};

export default ClippedDrawing;
```

- **Result**: Only the part of the blue circle inside the light gray rectangle is visible.

---

#### **Example: Clipping with a Path**

```tsx
import { Skia, Canvas, Path, Circle, useCanvas } from '@shopify/react-native-skia';

const ClippedPath = () => {
  const path = Skia.Path.Make();
  path.addCircle(150, 150, 100); // Define a circular clipping region

  const canvas = useCanvas();

  return (
    <Canvas style={{ flex: 1 }}>
      {canvas.clipPath(path)} {/* Apply the clipping path */}

      {/* Draw a rectangle, which will be clipped */}
      <Rect x={50} y={50} width={300} height={300} color="red" />
    </Canvas>
  );
};

export default ClippedPath;
```

- **Result**: Only the part of the red rectangle within the circular path is visible.

---

### **2. Masking in Skia**

Masking involves using one shape (the mask) to control the visibility of another. Unlike clipping, masks can include transparency or gradients.

#### **Key Component**
- **`Mask`**: Defines how two layers combine.

---

#### **Example: Simple Masking with Text**

Use text as a mask to reveal an image or gradient.

```tsx
import { Canvas, Mask, Text, Rect, LinearGradient, Skia } from '@shopify/react-native-skia';

const TextMask = () => {
  const font = Skia.Font(Skia.Typeface.MakeDefault(), 50);

  return (
    <Canvas style={{ flex: 1 }}>
      {/* Apply a text mask */}
      <Mask mask={<Text x={50} y={100} text="TRADE" font={font} color="black" />}>
        <LinearGradient
          colors={["blue", "green"]}
          start={{ x: 0, y: 0 }}
          end={{ x: 300, y: 300 }}
        />
      </Mask>
    </Canvas>
  );
};

export default TextMask;
```

- **Result**: The word "TRADE" appears, filled with the gradient.

---

#### **Example: Image Masking**

Use an image to mask another shape or gradient.

```tsx
import { Canvas, Mask, Image, LinearGradient, Skia } from '@shopify/react-native-skia';

const ImageMask = () => {
  const maskImage = Skia.Image.MakeFromEncoded(require('./assets/mask-image.png'));

  return (
    <Canvas style={{ flex: 1 }}>
      <Mask mask={<Image image={maskImage} x={0} y={0} width={300} height={300} />}>
        <LinearGradient
          colors={["red", "yellow"]}
          start={{ x: 0, y: 0 }}
          end={{ x: 300, y: 300 }}
        />
      </Mask>
    </Canvas>
  );
};

export default ImageMask;
```

- **Result**: The gradient is visible only where the mask image is opaque.

---

### **3. Animated Clipping and Masking**

You can animate the clipping region or mask to create dynamic effects.

#### **Example: Animated Clipping**

```tsx
import { Canvas, Rect, useValue, runTiming, Easing, useCanvas } from '@shopify/react-native-skia';

const AnimatedClipping = () => {
  const clipWidth = useValue(50);

  useEffect(() => {
    runTiming(clipWidth, 300, { duration: 2000, easing: Easing.inOut(Easing.cubic) });
  }, []);

  const canvas = useCanvas();

  return (
    <Canvas style={{ flex: 1 }}>
      {/* Dynamic clipping rectangle */}
      {canvas.clipRect(50, 50, clipWidth, 200)}

      {/* Background */}
      <Rect x={50} y={50} width={300} height={200} color="blue" />
    </Canvas>
  );
};

export default AnimatedClipping;
```

- **Result**: The visible portion of the rectangle grows dynamically.

---

#### **Example: Animated Masking**

```tsx
import { Canvas, Mask, Text, LinearGradient, Skia, useValue, runTiming, Easing } from '@shopify/react-native-skia';

const AnimatedTextMask = () => {
  const x = useValue(0);

  useEffect(() => {
    runTiming(x, 200, { duration: 2000, easing: Easing.inOut(Easing.cubic) });
  }, []);

  const font = Skia.Font(Skia.Typeface.MakeDefault(), 50);

  return (
    <Canvas style={{ flex: 1 }}>
      <Mask
        mask={<Text x={x} y={100} text="TRADE" font={font} color="black" />}
      >
        <LinearGradient
          colors={["blue", "cyan"]}
          start={{ x: 0, y: 0 }}
          end={{ x: 300, y: 300 }}
        />
      </Mask>
    </Canvas>
  );
};

export default AnimatedTextMask;
```

- **Result**: The masked text slides into view from the left.

---

### **Applications for TradeChampion**

1. **News Highlights**:
   - Use text clipping to reveal company names or sectors over relevant images or colors.

2. **Portfolio Visualization**:
   - Apply clipping to highlight specific sectors dynamically.

3. **Dynamic Stock Charts**:
   - Use animated masking for visually appealing highlights or focus areas.

4. **Custom Overlays**:
   - Use image masking to add thematic textures (e.g., company logos) over charts.

---
### **Performance Optimizations for Complex Masking and Clipping in Skia**

When working with advanced masking and clipping, performance can become a concern, especially when rendering on lower-end devices or dealing with animations. Below are techniques to ensure your Skia graphics remain smooth and efficient.

---

### **1. Optimize Clipping Performance**

#### **a. Use Simple Shapes for Clipping**
- Clipping with simple geometric shapes like rectangles and circles is more efficient than complex paths.
- Example: Prefer `clipRect` or `clipRRect` (rounded rectangle) over `clipPath` with intricate curves.

**Efficient Example:**
```tsx
canvas.clipRect(0, 0, 200, 200); // Simple rectangle
```

**Inefficient Example:**
```tsx
canvas.clipPath(Skia.Path.MakeFromSVG("...complex path...")); // Complex path
```

---

#### **b. Avoid Overlapping Clipping Calls**
- Avoid applying multiple clipping regions if they overlap unnecessarily.
- Combine clip paths or regions when possible to minimize GPU workload.

**Example: Merging Clipping Regions**
```tsx
const combinedPath = Skia.Path.Make();
combinedPath.addCircle(150, 150, 100);
combinedPath.addRect(100, 100, 200, 200);

canvas.clipPath(combinedPath);
```

---

#### **c. Use Static Clipping for Non-Animated Content**
- For non-dynamic elements, apply clipping once and avoid re-calculating it during rendering.

**Example: Apply Clipping Outside Animation Loops**
```tsx
const clipRegion = Skia.Path.Make();
clipRegion.addRect(50, 50, 200, 200);

<Canvas style={{ flex: 1 }}>
  {canvas.clipPath(clipRegion)} {/* Static clip region */}
  <Circle cx={150} cy={150} r={100} color="blue" />
</Canvas>;
```

---

### **2. Optimize Masking Performance**

#### **a. Use Pre-Rendered Masks**
- Instead of dynamically generating masks on each frame, pre-render them into an image and reuse.
- Skia’s `Image` API can create a reusable bitmap for this purpose.

**Example: Pre-Rendered Mask**
```tsx
const maskImage = Skia.Image.MakeFromEncoded(require('./assets/mask-image.png'));

<Canvas style={{ flex: 1 }}>
  <Mask mask={<Image image={maskImage} x={0} y={0} width={300} height={300} />}>
    <Rect x={0} y={0} width={300} height={300} color="blue" />
  </Mask>
</Canvas>;
```

---

#### **b. Optimize Animated Masks**
- For animated masks, limit the mask’s complexity and reduce the number of points or layers.

**Example: Simplify Animation**
```tsx
const maskText = <Text x={animatedX} y={100} text="TRADE" font={font} color="black" />;
```
Instead of masking a gradient:
```tsx
<LinearGradient colors={...} />
```

---

### **3. Reduce Overdraw**

Overdraw occurs when the same area is rendered multiple times unnecessarily. Minimize overdraw to improve performance.

#### **a. Use Transparent Areas in Masks**
- Ensure masks have transparency in unused areas to prevent rendering extra pixels.

**Example: Use a Simple SVG Mask**
```tsx
<Mask mask={<Image image={optimizedSVG} x={0} y={0} width={300} height={300} />}>
  <Rect x={0} y={0} width={300} height={300} color="blue" />
</Mask>;
```

---

### **4. Batch Rendering**

#### **a. Group Related Draw Calls**
- Use `Group` to combine multiple elements and transformations into a single operation.

**Example: Batch Draw Calls with Group**
```tsx
<Group>
  <Rect x={50} y={50} width={100} height={100} color="red" />
  <Circle cx={150} cy={150} r={50} color="blue" />
</Group>
```

#### **b. Avoid Redundant Drawing**
- Reuse shapes and paths instead of re-creating them.

**Efficient Example:**
```tsx
const path = Skia.Path.Make();
path.addCircle(100, 100, 50);

<Canvas style={{ flex: 1 }}>
  <Path path={path} color="blue" />
  <Path path={path} color="red" style="stroke" />
</Canvas>;
```

---

### **5. Optimize Animations**

#### **a. Limit Frame Updates**
- Use `runTiming` or interpolate values smoothly to reduce CPU overhead for animations.

**Example: Smooth Animation**
```tsx
runTiming(animatedValue, 300, { duration: 2000, easing: Easing.inOut(Easing.cubic) });
```

#### **b. Reduce Animation Scope**
- Animate only the properties that change.
- For example, instead of animating the entire mask, animate just the position or opacity.

---

### **6. Leverage GPU**

#### **a. Use GPU-Friendly Techniques**
- Skia is GPU-accelerated, but complex clipping and masking can still slow down rendering. Optimize GPU usage by:
  - Keeping paths simple.
  - Avoiding excessive transparency layers.

#### **b. Reduce Render Resolution**
- For animations, temporarily render at a lower resolution and scale up.

---

### **7. Profile and Debug**

#### **a. Use Skia Debugging Tools**
- Skia provides debugging options to visualize clipping regions and overdraw.

#### **b. Profile on Real Devices**
- Test on low-end devices to identify bottlenecks.
- Use React Native performance tools like `Flipper` or Skia’s profiling API.

---

### **Practical Applications for TradeChampion**

1. **Efficient Stock Trend Visualizations**:
   - Use pre-rendered masks for stock price highlights.
   - Limit clipping regions to focus areas (e.g., specific time ranges).

2. **Portfolio Growth Charts**:
   - Use batching (`Group`) for pie chart segments.
   - Animate only the relevant parts of a chart (e.g., growing bars or expanding slices).

3. **Dynamic News Highlights**:
   - Use simplified masks for text or logo overlays to emphasize breaking news or top-performing stocks.

