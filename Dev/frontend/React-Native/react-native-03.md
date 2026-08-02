### **Mapping HTML and CSS to Native Components**

1. **HTML Elements to Native Components:**
   - React Native provides components like `View`, `Text`, `Image`, and `ScrollView` that correspond to common HTML elements.
     - Example: `<div>` → `View`, `<span>` → `Text`, `<img>` → `Image`.
   - These components are wrappers around native platform-specific UI elements. For instance, `Text` maps to `UILabel` on iOS and `TextView` on Android.

2. **CSS-like Styling:**
   - React Native uses a subset of CSS properties defined in a JavaScript object.
     - Example: `{ padding: 10, fontSize: 16, color: 'blue' }`.
   - React Native's style system is platform-agnostic but interprets these styles into native APIs, which are then applied to the components.

3. **Yoga Layout Engine:**
   - React Native uses the **Yoga layout engine**, which implements a subset of CSS flexbox rules to handle layout across platforms.
   - This ensures consistent layout behavior, regardless of platform differences.

---

### **What Happens If an Exact Match Isn’t Found?**

1. **Font Types and Sizes:**
   - If a requested font isn’t available, React Native falls back to a default system font.
   - Platform-specific fonts can be used explicitly by name (e.g., `'San Francisco'` for iOS or `'Roboto'` for Android).
   - Font sizes might also render slightly differently between platforms due to DPI variations.

2. **Padding, Margins, and Layout:**
   - React Native uses the Yoga engine for layout, which is consistent across platforms. However:
     - Slight variations in rendering might occur because native UI components interpret layouts differently.
     - Developers can use `Platform` API to adjust styling based on the platform.

3. **Other Styles (e.g., Shadows):**
   - Certain styles, like shadows, behave differently across platforms:
     - iOS uses `shadowColor`, `shadowOffset`, `shadowOpacity`, etc.
     - Android primarily uses `elevation`.

4. **Custom Fallbacks or Defaults:**
   - If React Native cannot find an exact match for a property, it either:
     - Ignores the property (if non-critical).
     - Uses a default or closest approximation (e.g., system defaults for fonts, alignment).

5. **Platform-Specific Code:**
   - For significant discrepancies, developers can use platform-specific files (e.g., `MyComponent.ios.js` and `MyComponent.android.js`) or conditional logic with `Platform.OS`.

---

