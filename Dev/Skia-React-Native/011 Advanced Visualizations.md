### **11. Advanced Visualizations in Skia**

Skia’s flexibility allows you to create complex and interactive visualizations like custom stock charts, bar graphs, and animated data visualizations. These visualizations can be optimized for interactivity and performance.

---

### **1. Custom Charts**

#### **a. Line Chart (Stock Chart)**

**Implementation**:
```tsx
import React from 'react';
import { Canvas, Path, Skia } from '@shopify/react-native-skia';

const stockData = [
  { x: 0, y: 200 },
  { x: 50, y: 150 },
  { x: 100, y: 180 },
  { x: 150, y: 120 },
  { x: 200, y: 170 },
];

const StockChart = () => {
  const path = Skia.Path.Make();
  stockData.forEach((point, index) => {
    if (index === 0) {
      path.moveTo(point.x, point.y);
    } else {
      path.lineTo(point.x, point.y);
    }
  });

  return (
    <Canvas style={{ flex: 1 }}>
      <Path path={path} color="blue" style="stroke" strokeWidth={2} />
    </Canvas>
  );
};

export default StockChart;
```

- **Flow**:
  - The `Path` object connects stock data points.
  - `lineTo` creates straight lines between data points.
  - Use a dynamic `stockData` array to feed real-time stock prices into the chart.

---

#### **b. Bar Graph**

**Implementation**:
```tsx
import React from 'react';
import { Canvas, Rect } from '@shopify/react-native-skia';

const data = [
  { label: 'A', value: 50 },
  { label: 'B', value: 100 },
  { label: 'C', value: 75 },
];

const BarGraph = () => {
  return (
    <Canvas style={{ flex: 1 }}>
      {data.map((item, index) => (
        <Rect
          key={index}
          x={index * 60 + 20}
          y={200 - item.value}
          width={40}
          height={item.value}
          color="green"
        />
      ))}
    </Canvas>
  );
};

export default BarGraph;
```

- **Flow**:
  - Each bar’s height corresponds to the `value` in the dataset.
  - The `x` position is calculated based on the bar index for spacing.

---

#### **c. Pie Chart**

**Implementation**:
```tsx
import React from 'react';
import { Canvas, Path, Skia } from '@shopify/react-native-skia';

const data = [
  { value: 40, color: 'red' },
  { value: 30, color: 'blue' },
  { value: 30, color: 'green' },
];

const PieChart = () => {
  const total = data.reduce((sum, item) => sum + item.value, 0);
  let startAngle = 0;

  return (
    <Canvas style={{ flex: 1 }}>
      {data.map((item, index) => {
        const sweepAngle = (item.value / total) * 360;
        const path = Skia.Path.Make();
        path.moveTo(150, 150);
        path.arcTo(150, 150, 150, 150, startAngle, sweepAngle, false);
        path.close();
        startAngle += sweepAngle;

        return <Path key={index} path={path} color={item.color} />;
      })}
    </Canvas>
  );
};

export default PieChart;
```

- **Flow**:
  - The `arcTo` method draws each pie slice based on its angle.
  - Each slice’s color and sweep angle are determined by the data.

---

### **2. Animating Graphs and Data Visualizations**

#### **a. Animating a Line Chart**

**Implementation**:
```tsx
import React, { useEffect } from 'react';
import { Canvas, Path, useValue, runTiming, Easing } from '@shopify/react-native-skia';

const stockData = [
  { x: 0, y: 200 },
  { x: 50, y: 150 },
  { x: 100, y: 180 },
  { x: 150, y: 120 },
  { x: 200, y: 170 },
];

const AnimatedLineChart = () => {
  const progress = useValue(0);

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

- **Flow**:
  - `progress` controls how much of the path is drawn.
  - `runTiming` animates `progress` from `0` to `1`.

---

#### **b. Animated Bar Graph**

**Implementation**:
```tsx
import React, { useEffect } from 'react';
import { Canvas, Rect, useValue, runTiming, Easing } from '@shopify/react-native-skia';

const data = [
  { label: 'A', value: 50 },
  { label: 'B', value: 100 },
  { label: 'C', value: 75 },
];

const AnimatedBarGraph = () => {
  const heights = data.map(() => useValue(0));

  useEffect(() => {
    heights.forEach((height, index) => {
      runTiming(height, data[index].value, { duration: 1500, easing: Easing.inOut(Easing.cubic) });
    });
  }, []);

  return (
    <Canvas style={{ flex: 1 }}>
      {data.map((item, index) => (
        <Rect
          key={index}
          x={index * 60 + 20}
          y={200 - heights[index].current}
          width={40}
          height={heights[index]}
          color="green"
        />
      ))}
    </Canvas>
  );
};

export default AnimatedBarGraph;
```

- **Flow**:
  - Each bar’s height animates from `0` to its value.
  - `useValue` ensures smooth animations for each bar.

---

#### **c. Interactive Highlight in Pie Chart**

**Implementation**:
```tsx
import React, { useState } from 'react';
import { Canvas, Path, Skia } from '@shopify/react-native-skia';

const data = [
  { value: 40, color: 'red' },
  { value: 30, color: 'blue' },
  { value: 30, color: 'green' },
];

const InteractivePieChart = () => {
  const [highlighted, setHighlighted] = useState(null);
  const total = data.reduce((sum, item) => sum + item.value, 0);
  let startAngle = 0;

  return (
    <Canvas style={{ flex: 1 }}>
      {data.map((item, index) => {
        const sweepAngle = (item.value / total) * 360;
        const path = Skia.Path.Make();
        path.moveTo(150, 150);
        path.arcTo(150, 150, 150, 150, startAngle, sweepAngle, false);
        path.close();
        startAngle += sweepAngle;

        return (
          <Path
            key={index}
            path={path}
            color={highlighted === index ? "yellow" : item.color}
            onTouchStart={() => setHighlighted(index)}
          />
        );
      })}
    </Canvas>
  );
};

export default InteractivePieChart;
```

- **Flow**:
  - Tapping a pie slice highlights it by changing its color.

---

### **Applications for TradeChampion**

1. **Stock Trendlines**:
   - Animate line charts to show real-time updates or historical playback.

2. **Portfolio Visualization**:
   - Use pie charts or bar graphs to display portfolio distribution.
   - Add interactivity to highlight or filter specific sectors.

3. **Real-Time Data Updates**:
   - Integrate animations with live stock data for responsive visualizations.

---
### **Deeper Dive into Interactive Charts with Skia**

Interactive charts are essential for engaging users and providing actionable insights. This deeper dive focuses on techniques for creating interactive line charts, bar graphs, and pie charts in Skia.

---

### **Techniques for Interactive Charts**

1. **Responding to User Input**:
   - Tap gestures to highlight specific points or areas.
   - Drag gestures to navigate charts.
   - Pinch gestures to zoom in and out.

2. **Real-Time Updates**:
   - Update the chart dynamically with live data.
   - Recalculate and redraw based on user interaction.

3. **Layering for Clarity**:
   - Use `Group` to layer and manage elements (e.g., gridlines, data points, labels).

---

### **1. Interactive Line Chart**

#### **Feature: Highlight Closest Point on Drag**

**Implementation**:
```tsx
import React, { useState } from 'react';
import { Canvas, Circle, Path, Skia } from '@shopify/react-native-skia';
import { GestureDetector, GestureHandlerRootView, PanGestureHandlerGestureEvent } from 'react-native-gesture-handler';

const stockData = [
  { x: 50, y: 200 },
  { x: 100, y: 150 },
  { x: 150, y: 180 },
  { x: 200, y: 120 },
  { x: 250, y: 170 },
];

const InteractiveLineChart = () => {
  const [highlight, setHighlight] = useState(null);

  const handleDrag = (event: PanGestureHandlerGestureEvent) => {
    const { x } = event.nativeEvent;
    const closest = stockData.reduce((prev, curr) =>
      Math.abs(curr.x - x) < Math.abs(prev.x - x) ? curr : prev
    );
    setHighlight(closest);
  };

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
      <GestureDetector onGestureEvent={handleDrag}>
        <Canvas style={{ flex: 1 }}>
          {/* Line Chart */}
          <Path path={path} color="blue" style="stroke" strokeWidth={2} />

          {/* Data Points */}
          {stockData.map((point, index) => (
            <Circle key={index} cx={point.x} cy={point.y} r={5} color="blue" />
          ))}

          {/* Highlighted Point */}
          {highlight && (
            <Circle cx={highlight.x} cy={highlight.y} r={10} color="red" />
          )}
        </Canvas>
      </GestureDetector>
    </GestureHandlerRootView>
  );
};

export default InteractiveLineChart;
```

**How It Works**:
- **Gestures**: The `GestureDetector` captures the drag gesture.
- **Highlight Logic**: The `highlight` state is updated to the closest point based on the user’s drag position.
- **Layering**: The red circle for the highlighted point is drawn last, appearing on top.

---

### **2. Interactive Bar Graph**

#### **Feature: Tap to Show Bar Value**

**Implementation**:
```tsx
import React, { useState } from 'react';
import { Canvas, Rect, Text } from '@shopify/react-native-skia';
import { GestureDetector, GestureHandlerRootView, TapGestureHandlerGestureEvent } from 'react-native-gesture-handler';

const data = [
  { label: 'A', value: 50 },
  { label: 'B', value: 100 },
  { label: 'C', value: 75 },
];

const InteractiveBarGraph = () => {
  const [selectedBar, setSelectedBar] = useState(null);

  const handleTap = (event: TapGestureHandlerGestureEvent) => {
    const { x } = event.nativeEvent;
    const barIndex = Math.floor((x - 20) / 60); // Calculate bar index based on position
    if (barIndex >= 0 && barIndex < data.length) {
      setSelectedBar(data[barIndex]);
    }
  };

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <GestureDetector onGestureEvent={handleTap}>
        <Canvas style={{ flex: 1 }}>
          {/* Bar Graph */}
          {data.map((item, index) => (
            <Rect
              key={index}
              x={index * 60 + 20}
              y={200 - item.value}
              width={40}
              height={item.value}
              color={selectedBar?.label === item.label ? "red" : "green"}
            />
          ))}

          {/* Label for Selected Bar */}
          {selectedBar && (
            <Text
              x={150}
              y={50}
              text={`Value: ${selectedBar.value}`}
              font={Skia.Font(Skia.Typeface.MakeDefault(), 24)}
              color="black"
            />
          )}
        </Canvas>
      </GestureDetector>
    </GestureHandlerRootView>
  );
};

export default InteractiveBarGraph;
```

**How It Works**:
- **Gestures**: Taps are captured by the `GestureDetector`.
- **Logic**: Bar selection is calculated based on the x-coordinate of the tap.
- **Feedback**: The selected bar is highlighted, and its value is displayed as text.

---

### **3. Interactive Pie Chart**

#### **Feature: Rotate Pie Chart**

**Implementation**:
```tsx
import React, { useState } from 'react';
import { Canvas, Path, Skia, useValue, runTiming, Easing } from '@shopify/react-native-skia';
import { GestureDetector, GestureHandlerRootView, PanGestureHandlerGestureEvent } from 'react-native-gesture-handler';

const data = [
  { value: 40, color: 'red' },
  { value: 30, color: 'blue' },
  { value: 30, color: 'green' },
];

const InteractivePieChart = () => {
  const rotation = useValue(0);

  const handleDrag = (event: PanGestureHandlerGestureEvent) => {
    const { translationX } = event.nativeEvent;
    runTiming(rotation, translationX / 100, { duration: 500, easing: Easing.inOut(Easing.cubic) });
  };

  const total = data.reduce((sum, item) => sum + item.value, 0);
  let startAngle = 0;

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <GestureDetector onGestureEvent={handleDrag}>
        <Canvas style={{ flex: 1 }}>
          {data.map((item, index) => {
            const sweepAngle = (item.value / total) * 360;
            const path = Skia.Path.Make();
            path.moveTo(150, 150);
            path.arcTo(150, 150, 150, 150, startAngle, sweepAngle, false);
            path.close();
            startAngle += sweepAngle;

            return (
              <Path
                key={index}
                path={path}
                color={item.color}
                transform={[{ rotate: rotation }]}
              />
            );
          })}
        </Canvas>
      </GestureDetector>
    </GestureHandlerRootView>
  );
};

export default InteractivePieChart;
```

**How It Works**:
- **Gestures**: The user drags to rotate the pie chart.
- **Animation**: The `runTiming` function animates the rotation based on the drag distance.
- **Transformations**: The `rotate` transformation is applied to each slice.

---

### **Applications in TradeChampion**

1. **Stock Charts**:
   - Highlight specific data points or trends with drag gestures.
   - Zoom into a specific time range with pinch gestures.

2. **Portfolio Visualization**:
   - Rotate pie charts to focus on specific sectors.
   - Tap bar graphs to display sector values.

3. **Interactive News**:
   - Swipe gestures to browse through news highlights.
   - Tap on news charts to focus on a specific sector’s performance.

---

### **Dynamic Data Updates for Interactive Charts**

Dynamic data updates allow charts to reflect real-time or user-triggered changes, such as live stock price updates, user-selected data ranges, or API-driven data feeds. Skia's `useValue` and React state enable smooth integration of these updates.

---

### **1. Real-Time Updates in a Line Chart**

#### **Feature**: Simulate real-time stock price updates on a line chart.

**Implementation**:
```tsx
import React, { useEffect, useState } from 'react';
import { Canvas, Path, useValue, runTiming, Easing } from '@shopify/react-native-skia';

const initialData = [
  { x: 0, y: 200 },
  { x: 50, y: 150 },
  { x: 100, y: 180 },
  { x: 150, y: 120 },
];

const DynamicLineChart = () => {
  const [data, setData] = useState(initialData);
  const progress = useValue(0);

  // Simulate real-time data updates
  useEffect(() => {
    const interval = setInterval(() => {
      setData((prevData) => [
        ...prevData.slice(1), // Remove the oldest point
        { x: prevData[prevData.length - 1].x + 50, y: Math.random() * 200 }, // Add a new point
      ]);
    }, 2000); // Update every 2 seconds

    return () => clearInterval(interval);
  }, []);

  // Animate the drawing of the chart
  useEffect(() => {
    runTiming(progress, 1, { duration: 2000, easing: Easing.linear });
  }, [data]);

  const path = Skia.Path.Make();
  data.forEach((point, index) => {
    if (index === 0) {
      path.moveTo(point.x, point.y);
    } else {
      path.lineTo(point.x, point.y);
    }
  });

  return (
    <Canvas style={{ flex: 1 }}>
      <Path path={path} color="blue" style="stroke" strokeWidth={2} progress={progress} />
    </Canvas>
  );
};

export default DynamicLineChart;
```

**How It Works**:
- **Data Updates**: New data points are added every 2 seconds, and the oldest point is removed.
- **Animation**: The `progress` value animates the chart’s re-drawing after each update.

---

### **2. Bar Graph with Live Updates**

#### **Feature**: Dynamically update bar heights based on user input or API data.

**Implementation**:
```tsx
import React, { useEffect, useState } from 'react';
import { Canvas, Rect, useValue, runTiming, Easing } from '@shopify/react-native-skia';

const initialData = [
  { label: 'A', value: 50 },
  { label: 'B', value: 100 },
  { label: 'C', value: 75 },
];

const DynamicBarGraph = () => {
  const [data, setData] = useState(initialData);
  const heights = data.map(() => useValue(0));

  // Simulate API updates
  useEffect(() => {
    const interval = setInterval(() => {
      setData((prevData) =>
        prevData.map((item) => ({
          ...item,
          value: Math.floor(Math.random() * 150), // Randomize values
        }))
      );
    }, 3000); // Update every 3 seconds

    return () => clearInterval(interval);
  }, []);

  // Animate bar height updates
  useEffect(() => {
    data.forEach((item, index) => {
      runTiming(heights[index], item.value, { duration: 1000, easing: Easing.inOut(Easing.cubic) });
    });
  }, [data]);

  return (
    <Canvas style={{ flex: 1 }}>
      {data.map((item, index) => (
        <Rect
          key={index}
          x={index * 60 + 20}
          y={200 - heights[index].current}
          width={40}
          height={heights[index]}
          color="green"
        />
      ))}
    </Canvas>
  );
};

export default DynamicBarGraph;
```

**How It Works**:
- **Data Updates**: Bar heights are updated every 3 seconds based on randomized values.
- **Smooth Transitions**: `runTiming` animates the transition of bar heights for a polished effect.

---

### **3. Pie Chart with Live Sector Updates**

#### **Feature**: Dynamically update sector sizes based on changing portfolio data.

**Implementation**:
```tsx
import React, { useState, useEffect } from 'react';
import { Canvas, Path, Skia } from '@shopify/react-native-skia';

const initialData = [
  { value: 40, color: 'red' },
  { value: 30, color: 'blue' },
  { value: 30, color: 'green' },
];

const DynamicPieChart = () => {
  const [data, setData] = useState(initialData);

  // Simulate real-time portfolio updates
  useEffect(() => {
    const interval = setInterval(() => {
      setData((prevData) =>
        prevData.map((sector) => ({
          ...sector,
          value: Math.floor(Math.random() * 100), // Randomize sector values
        }))
      );
    }, 4000); // Update every 4 seconds

    return () => clearInterval(interval);
  }, []);

  const total = data.reduce((sum, item) => sum + item.value, 0);
  let startAngle = 0;

  return (
    <Canvas style={{ flex: 1 }}>
      {data.map((item, index) => {
        const sweepAngle = (item.value / total) * 360;
        const path = Skia.Path.Make();
        path.moveTo(150, 150);
        path.arcTo(150, 150, 150, 150, startAngle, sweepAngle, false);
        path.close();
        startAngle += sweepAngle;

        return <Path key={index} path={path} color={item.color} />;
      })}
    </Canvas>
  );
};

export default DynamicPieChart;
```

**How It Works**:
- **Data Updates**: Sector values are recalculated every 4 seconds to simulate portfolio changes.
- **Redrawing Sectors**: Each sector’s sweep angle is recalculated based on the new data.

---

### **Techniques for Dynamic Data Updates**

1. **Use Timers for Simulations**:
   - `setInterval` is used to simulate live updates during development.
   - Replace it with API calls for real-world data.

2. **Combine React State and Skia Animations**:
   - Use `useState` to store the dynamic data and `useValue` to handle animation states.

3. **Batch Updates**:
   - When working with large datasets, update only the visible or impacted elements.

4. **Throttle Updates**:
   - Limit the frequency of updates to reduce rendering overhead.
   - Example: Use `lodash`'s `throttle` or `debounce` for better control.

---

### **Applications for TradeChampion**

1. **Stock Charts**:
   - Show real-time price movements with animated line updates.
   - Highlight the latest price point dynamically.

2. **Portfolio Insights**:
   - Visualize sector performance with pie chart animations.
   - Update bar graphs to reflect asset growth or decline.

3. **Live Market Overview**:
   - Use animations to highlight sectors or stocks experiencing significant changes.
   - Dynamically adjust heatmap intensity based on real-time data.

---

 **real-time API integration**, **data-driven interactivity** ?