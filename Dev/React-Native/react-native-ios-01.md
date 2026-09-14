Here’s a detailed list of **iOS-specific** code, styles, components, and features you can use in React Native for creating apps that align closely with iOS conventions:

---

### **iOS-Specific Components and APIs**

1. **`ActionSheetIOS`**
   - Displays a native iOS action sheet (a modal with options for user actions).
   ```javascript
   import { ActionSheetIOS } from 'react-native';

   ActionSheetIOS.showActionSheetWithOptions(
     {
       options: ['Cancel', 'Option 1', 'Option 2'],
       cancelButtonIndex: 0,
     },
     (buttonIndex) => {
       if (buttonIndex === 1) {
         console.log('Option 1 selected');
       }
     }
   );
   ```

2. **`SegmentedControlIOS`**
   - Provides a native iOS segmented control for switching between options.
   ```javascript
   import { SegmentedControlIOS } from 'react-native';

   <SegmentedControlIOS
     values={['Option 1', 'Option 2']}
     selectedIndex={0}
     onChange={(event) => console.log(event.nativeEvent.selectedSegmentIndex)}
   />;
   ```

3. **`SafeAreaView`**
   - Ensures content does not overlap with the notch or system UI (like the status bar).
   ```javascript
   import { SafeAreaView } from 'react-native';

   <SafeAreaView style={{ flex: 1, backgroundColor: '#f8f9fa' }}>
     <Text>Safe Area Content</Text>
   </SafeAreaView>;
   ```

4. **`DatePickerIOS`** (Deprecated in favor of `DateTimePicker`)
   - Used for native iOS date pickers.
   - For newer implementations, use [react-native-datetimepicker](https://github.com/react-native-datetimepicker/datetimepicker).

---

### **iOS-Specific Styles**

1. **System Fonts:**
   - iOS uses `San Francisco` by default. You can explicitly use it with `fontFamily: 'System'`.

2. **Shadows:**
   - iOS supports shadow properties like `shadowColor`, `shadowOpacity`, `shadowOffset`, and `shadowRadius`.
   ```javascript
   const styles = StyleSheet.create({
     box: {
       shadowColor: '#000',
       shadowOpacity: 0.2,
       shadowOffset: { width: 0, height: 2 },
       shadowRadius: 4,
       backgroundColor: '#fff',
       padding: 20,
     },
   });
   ```

3. **Blur Effects:**
   - Use libraries like `@react-native-community/blur` for iOS-specific blur views.
   ```javascript
   import { BlurView } from '@react-native-community/blur';

   <BlurView
     style={{ flex: 1 }}
     blurType="light"
     blurAmount={10}
   >
     <Text>Blurred Content</Text>
   </BlurView>;
   ```

4. **Safe Area Padding:**
   - Use `SafeAreaView` or manually add padding to respect the notch and home indicator.
   ```javascript
   const styles = StyleSheet.create({
     container: {
       paddingTop: Platform.OS === 'ios' ? 44 : 0,
     },
   });
   ```

---

### **iOS-Specific Behaviors**

1. **Haptic Feedback:**
   - Use the `react-native-haptic-feedback` library to trigger native vibrations for actions.
   ```javascript
   import HapticFeedback from 'react-native-haptic-feedback';

   HapticFeedback.trigger('impactLight');
   ```

2. **Status Bar Customization:**
   - Use the `StatusBar` component to customize the iOS status bar.
   ```javascript
   import { StatusBar } from 'react-native';

   <StatusBar barStyle="dark-content" />;
   ```

3. **Swipe Back Navigation:**
   - iOS supports default swipe-back gestures for stack navigation.

4. **Dynamic Type:**
   - iOS adjusts text sizes based on user preferences. React Native supports it via `allowFontScaling`:
   ```javascript
   <Text style={{ fontSize: 16 }} allowFontScaling={true}>
     Scalable Text
   </Text>;
   ```

5. **Native Alerts:**
   - Use `Alert` for iOS-style native popups.
   ```javascript
   import { Alert } from 'react-native';

   Alert.alert('Title', 'This is an alert message.', [
     { text: 'Cancel', style: 'cancel' },
     { text: 'OK', onPress: () => console.log('OK Pressed') },
   ]);
   ```

---

### **iOS-Specific Libraries and Integrations**

1. **Gesture Handling:**
   - Use libraries like `react-native-gesture-handler` for iOS gesture support.

2. **Face ID/Touch ID Authentication:**
   - Use `react-native-touch-id` or `react-native-keychain` for biometric authentication.

3. **Apple Pay:**
   - Integrate Apple Pay with libraries like `tipsi-stripe`.

4. **In-App Purchases:**
   - Use `react-native-iap` to handle subscriptions and purchases.

5. **Deep Linking:**
   - iOS uses `Universal Links`. React Native supports this with `react-navigation` or custom implementations via `Linking`.

---

### **Platform.OS-based Conditional Code**

React Native lets you write platform-specific code using `Platform.OS`:

```javascript
import { Platform } from 'react-native';

if (Platform.OS === 'ios') {
  console.log('This is iOS');
}
```

---

### **File-Based Platform-Specific Code**

You can create platform-specific files that React Native automatically detects:

- `MyComponent.ios.js` (for iOS)
- `MyComponent.android.js` (for Android)

React Native will import the correct file based on the platform.

---
Below is a complete React Native example implementing all the iOS-specific features we discussed. The code is structured to demonstrate each feature while being runnable in a single app.

---

### **Complete Example**

```javascript
import React, { useState } from 'react';
import {
  StyleSheet,
  Text,
  View,
  Platform,
  TouchableOpacity,
  SafeAreaView,
  Alert,
  StatusBar,
  ScrollView,
  ActionSheetIOS,
  Button,
} from 'react-native';
import { BlurView } from '@react-native-community/blur';
import HapticFeedback from 'react-native-haptic-feedback';

const App = () => {
  const [action, setAction] = useState('');
  const [blurEffect, setBlurEffect] = useState(false);

  // Action Sheet Handler
  const showActionSheet = () => {
    ActionSheetIOS.showActionSheetWithOptions(
      {
        options: ['Cancel', 'Option 1', 'Option 2'],
        cancelButtonIndex: 0,
      },
      (buttonIndex) => {
        if (buttonIndex === 1) {
          setAction('Option 1 Selected');
        } else if (buttonIndex === 2) {
          setAction('Option 2 Selected');
        }
      }
    );
  };

  // Haptic Feedback Handler
  const triggerHapticFeedback = () => {
    HapticFeedback.trigger('impactLight');
    Alert.alert('Haptic Feedback', 'Light haptic feedback triggered!');
  };

  // Toggle Blur Effect
  const toggleBlurEffect = () => {
    setBlurEffect(!blurEffect);
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar barStyle="dark-content" />
      <ScrollView contentContainerStyle={styles.container}>
        <Text style={styles.title}>iOS-Specific Features Example</Text>

        {/* Action Sheet */}
        <TouchableOpacity style={styles.button} onPress={showActionSheet}>
          <Text style={styles.buttonText}>Show Action Sheet</Text>
        </TouchableOpacity>
        {action ? <Text style={styles.actionText}>{action}</Text> : null}

        {/* Haptic Feedback */}
        <TouchableOpacity style={styles.button} onPress={triggerHapticFeedback}>
          <Text style={styles.buttonText}>Trigger Haptic Feedback</Text>
        </TouchableOpacity>

        {/* Blur Effect */}
        <TouchableOpacity style={styles.button} onPress={toggleBlurEffect}>
          <Text style={styles.buttonText}>
            {blurEffect ? 'Remove Blur Effect' : 'Add Blur Effect'}
          </Text>
        </TouchableOpacity>
        {blurEffect && (
          <BlurView style={styles.blurView} blurType="light" blurAmount={10}>
            <Text style={styles.blurText}>Blur Effect Applied</Text>
          </BlurView>
        )}

        {/* Dynamic Type (Text Scaling) */}
        <Text style={styles.scalableText} allowFontScaling>
          This text scales dynamically based on user settings.
        </Text>

        {/* Footer */}
        <Text style={styles.footer}>
          Running on {Platform.OS} | Version: {Platform.Version}
        </Text>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#f8f9fa',
  },
  container: {
    alignItems: 'center',
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#00008b',
    marginBottom: 20,
  },
  button: {
    backgroundColor: '#007aff',
    paddingVertical: 12,
    paddingHorizontal: 20,
    borderRadius: 8,
    marginBottom: 20,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
  },
  actionText: {
    marginTop: 10,
    fontSize: 16,
    color: '#333',
  },
  blurView: {
    width: '100%',
    height: 100,
    justifyContent: 'center',
    alignItems: 'center',
    marginVertical: 20,
  },
  blurText: {
    color: '#fff',
    fontSize: 16,
  },
  scalableText: {
    fontSize: 16,
    color: '#333',
    marginTop: 20,
    textAlign: 'center',
  },
  footer: {
    fontSize: 14,
    color: '#666',
    marginTop: 30,
  },
});

export default App;
```

---

### **How to Run**

1. **Install React Native Dependencies:**
   - Ensure you have a React Native environment set up. Follow the official [React Native setup guide](https://reactnative.dev/docs/environment-setup) for iOS.

2. **Install Required Libraries:**
   - Install the blur and haptic feedback libraries:
     ```bash
     npm install @react-native-community/blur react-native-haptic-feedback
     ```

3. **Run the App:**
   - Start the development server and run the app on an iOS simulator or device:
     ```bash
     npx react-native run-ios
     ```

---

### **Features Implemented**
1. **Action Sheet:** Displaying native iOS options modal.
2. **Haptic Feedback:** Triggering a light vibration for feedback.
3. **Blur Effect:** Applying a dynamic blur view.
4. **Dynamic Text Scaling:** Allowing text to scale based on system settings.
5. **Platform-Specific Footer:** Displaying platform name and version.
6. **Safe Area Handling:** Ensuring content doesn't overlap system UI. 

This example incorporates most of the discussed iOS-specific features, showcasing how to use them in a React Native app.
