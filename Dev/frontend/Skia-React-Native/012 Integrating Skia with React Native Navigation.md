### **12. Integrating Skia with React Native Navigation**

Integrating Skia into a navigable React Native app allows you to use Skia’s powerful rendering capabilities on specific screens while sharing data seamlessly across components. This section covers setting up Skia within navigable screens and passing/sharing data effectively.

---

### **1. Using Skia within Navigable Screens**

#### **Setup Navigation**
React Navigation is commonly used for navigation in React Native apps. Here's a quick setup:

**Install Navigation Dependencies**:
```bash
npm install @react-navigation/native @react-navigation/stack react-native-screens react-native-safe-area-context react-native-gesture-handler react-native-reanimated react-native-navigation
```

**Basic Navigation Setup**:
```tsx
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import HomeScreen from './HomeScreen';
import SkiaScreen from './SkiaScreen';

const Stack = createStackNavigator();

const App = () => {
  return (
    <NavigationContainer>
      <Stack.Navigator>
        <Stack.Screen name="Home" component={HomeScreen} />
        <Stack.Screen name="SkiaView" component={SkiaScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
};

export default App;
```

---

#### **Example: Skia in a Screen**

**`HomeScreen`: Navigate to the Skia view**
```tsx
import React from 'react';
import { View, Button } from 'react-native';

const HomeScreen = ({ navigation }) => {
  return (
    <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center' }}>
      <Button title="Go to Skia View" onPress={() => navigation.navigate('SkiaView')} />
    </View>
  );
};

export default HomeScreen;
```

**`SkiaScreen`: Render Skia elements**
```tsx
import React from 'react';
import { Canvas, Circle } from '@shopify/react-native-skia';

const SkiaScreen = () => {
  return (
    <Canvas style={{ flex: 1 }}>
      <Circle cx={150} cy={150} r={50} color="blue" />
    </Canvas>
  );
};

export default SkiaScreen;
```

**How It Works**:
1. **Home Screen**:
   - Contains a button to navigate to the Skia view.
2. **Skia Screen**:
   - Displays Skia-rendered content (`Circle`) within a navigable screen.

---

### **2. Sharing Data Between Components and Skia Views**

#### **a. Passing Data Through Navigation Parameters**

**Example: Pass data to the Skia view**

1. **HomeScreen**:
   Pass data using `navigation.navigate`:
   ```tsx
   <Button
     title="Go to Skia View"
     onPress={() => navigation.navigate('SkiaView', { color: 'red' })}
   />
   ```

2. **SkiaScreen**:
   Access the data from `route.params`:
   ```tsx
   import React from 'react';
   import { Canvas, Circle } from '@shopify/react-native-skia';

   const SkiaScreen = ({ route }) => {
     const { color } = route.params;

     return (
       <Canvas style={{ flex: 1 }}>
         <Circle cx={150} cy={150} r={50} color={color} />
       </Canvas>
     );
   };

   export default SkiaScreen;
   ```

- **Result**: The circle’s color is dynamically set based on the parameter passed from the Home Screen.

---

#### **b. Using Global State (Context or Redux)**

For complex apps, a global state management solution ensures seamless sharing of data across multiple Skia views.

1. **Setup Context**:
   ```tsx
   import React, { createContext, useContext, useState } from 'react';

   const AppContext = createContext();

   export const AppProvider = ({ children }) => {
     const [themeColor, setThemeColor] = useState('blue');

     return (
       <AppContext.Provider value={{ themeColor, setThemeColor }}>
         {children}
       </AppContext.Provider>
     );
   };

   export const useAppContext = () => useContext(AppContext);
   ```

2. **Wrap App with Context**:
   ```tsx
   import { AppProvider } from './AppContext';

   const App = () => (
     <AppProvider>
       <NavigationContainer>{/* Stack.Navigator here */}</NavigationContainer>
     </AppProvider>
   );

   export default App;
   ```

3. **Access Context in Skia Screen**:
   ```tsx
   import React from 'react';
   import { Canvas, Circle } from '@shopify/react-native-skia';
   import { useAppContext } from './AppContext';

   const SkiaScreen = () => {
     const { themeColor } = useAppContext();

     return (
       <Canvas style={{ flex: 1 }}>
         <Circle cx={150} cy={150} r={50} color={themeColor} />
       </Canvas>
     );
   };

   export default SkiaScreen;
   ```

- **Result**: The circle color dynamically adapts to the globally managed `themeColor`.

---

#### **c. Fetch Data Dynamically**

Fetch data from an API and use it in the Skia view.

**Example: Display stock price changes dynamically**
```tsx
import React, { useEffect, useState } from 'react';
import { Canvas, Path, Skia } from '@shopify/react-native-skia';

const SkiaScreen = () => {
  const [stockData, setStockData] = useState([]);

  useEffect(() => {
    fetch('https://api.example.com/stocks')
      .then((res) => res.json())
      .then((data) => setStockData(data));
  }, []);

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

export default SkiaScreen;
```

- **Result**: The chart dynamically updates based on the fetched stock data.

---

### **Best Practices**

1. **Optimize Data Flow**:
   - Use Context or Redux for global state that multiple screens need.
   - Pass smaller, specific parameters via `navigation.navigate`.

2. **Lazy Load Skia Views**:
   - Only initialize heavy Skia rendering when the screen is active.

3. **Debugging Navigation**:
   - Use the React Navigation DevTools or `console.log(route.params)` for debugging data passing.

4. **Performance Optimization**:
   - Avoid recalculating paths or elements unnecessarily.
   - Use Skia’s `useValue` for animations instead of relying solely on React state.

---

### **Applications for TradeChampion**

1. **Stock Details Screen**:
   - Navigate from a stock list to a detailed stock chart with dynamic updates.
   - Pass stock symbols and other data via navigation.

2. **Portfolio Management**:
   - Use Context to share portfolio data across screens.
   - Render charts dynamically based on user selection.

3. **Dynamic News Highlights**:
   - Fetch news data for a specific stock or sector when navigating to a news screen.

---

