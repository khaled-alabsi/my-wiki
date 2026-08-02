## Takeaway: Traditional Remote Bundle vs. RemoteThemenblock Library

### Traditional Remote JavaScript Bundle

A traditional remote JavaScript bundle is responsible for rendering itself.

The host application only needs to:

1. Create an HTML container with a predefined ID.
2. Load the remote JavaScript using a `<script>` tag.

Example:

```html
<div id="my-widget"></div>

<script src="https://server/widget.js"></script>
```

The bundle itself contains something like:

```tsx
ReactDOM.render(
    <Widget />,
    document.getElementById("my-widget")
);
```

Therefore:

- The bundle decides **where** it renders.
- The container ID is usually hardcoded inside the bundle.
- The host has little control over the rendering process.

---

### RemoteThemenblock Library

With the RemoteThemenblock library, the remote bundle **does not render itself**.

Instead, it only **registers** its React component:

```text
createThemenblockMount(...)
    ↓
window.tb["investorprofile-finances"] = new eer(...)
```

The registered object (`eer`) stores:

- the React component
- mount()
- unmount()
- event handling
- logging

Later, the **host library**:

1. Creates a container dynamically.
2. Downloads the remote bundle.
3. Calls:

```javascript
window.tb[name].mount(props);
```

The `mount()` method then performs:

```tsx
const container =
    document.getElementById(`${name}-container`);

ReactDOM.render(
    <Component {...props} />,
    container
);
```

Therefore:

- The remote bundle does **not** know where it will be rendered.
- The host decides **which** container to use.
- The root container is chosen dynamically at runtime.
- The remote only provides a React component; the library performs the actual rendering.

---

### Key Difference

| Traditional Bundle | RemoteThemenblock |
|--------------------|-------------------|
| Bundle renders itself | Library renders the component |
| Fixed root container | Dynamic runtime container |
| Bundle owns `ReactDOM.render()` | Library owns `ReactDOM.render()` / `mount()` |
| Host only loads JS | Host controls loading, mounting, communication and lifecycle |