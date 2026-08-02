# Redux Toolkit Notes (Store, Slice, Dispatch, Selector)

## 1. What is the Store?

The **store** is the single object that contains the application's
shared state.

``` text
Store
│
├── process
├── customer
├── approval
├── pavData
└── ...
```

It is created by:

``` ts
const store = configureStore({
    reducer: {
        process: processReducer,
        customer: customerReducer,
        approval: approvalReducer,
    }
});
```

Although you only provide the reducers, `configureStore()` returns an
object similar to:

``` ts
store = {
    dispatch,
    getState,
    subscribe,
    replaceReducer
}
```

So methods such as `store.dispatch()` and `store.getState()` already
exist.

------------------------------------------------------------------------

## 2. What is a Slice?

A slice owns one part of the store together with the logic that modifies
it.

``` text
Store
│
├── customer
├── process
├── openingPavScenario  ← this slice
└── approval
```

Each slice contains:

-   Initial state
-   Reducers
-   Generated action creators

------------------------------------------------------------------------

## 3. What are reducers?

Inside `createSlice`, `reducers` is simply an object.

``` ts
reducers: {
    initCurrentStep(state, action) {
        ...
    },

    setCurrentStep(state, action) {
        ...
    }
}
```

Each property is one reducer function.

### Object method shorthand

This syntax:

``` ts
const obj = {
    hello(name) {
        console.log(name);
    }
}
```

is exactly the same as

``` ts
const obj = {
    hello: function(name) {
        console.log(name);
    }
}
```

and also works as

``` ts
const obj = {
    hello: (name) => {
        console.log(name);
    }
}
```

(The arrow version behaves differently regarding `this`, but for Redux
reducers all three work.)

So your reducer

``` ts
initCurrentStep(state, action) {
    ...
}
```

can be mentally read as

``` ts
initCurrentStep: function(state, action) {
    ...
}
```

------------------------------------------------------------------------

## 4. What does dispatch() do?

`dispatch()` sends an action into Redux.

``` ts
dispatch(addUser(user));
```

Flow:

``` text
dispatch(action)
        │
        ▼
Redux Store
        │
        ▼
Every reducer receives the action
        │
        ▼
Reducers decide whether to update their state
        │
        ▼
Store is updated
        │
        ▼
React components re-render if necessary
```

------------------------------------------------------------------------

## 5. Reducers vs Action Creators

Inside your slice you write

``` ts
reducers: {
    initCurrentStep(state, action) {
        ...
    }
}
```

Redux Toolkit automatically creates another function with the same name:

``` ts
initCurrentStep(payload)
```

Internally it behaves roughly like:

``` ts
const initCurrentStep = (payload) => ({
    type: "page/pavOpening/initCurrentStep",
    payload
});
```

Therefore

``` ts
dispatch(initCurrentStep({
    isFinalizationBackwardAction,
    isTaxResidencyBackwardAction
}));
```

becomes

``` ts
dispatch({
    type: "page/pavOpening/initCurrentStep",
    payload: {
        isFinalizationBackwardAction,
        isTaxResidencyBackwardAction
    }
});
```

Two different functions share the same name:

-   Reducer → called by Redux
-   Action creator → called by you

------------------------------------------------------------------------

## 6. AppDispatch

``` ts
export type AppDispatch = typeof store.dispatch;
```

Meaning:

> Create a type equal to the type of `store.dispatch`.

------------------------------------------------------------------------

## 7. RootState

``` ts
export type RootState =
    ReturnType<typeof store.getState>;
```

`store.getState()` returns the complete Redux state.

Therefore `RootState` becomes the type of the entire state.

------------------------------------------------------------------------

## 8. useAppDispatch

``` ts
export const useAppDispatch: () => AppDispatch =
    useDispatch;
```

This is only a typed alias.

Equivalent idea:

``` ts
const useAppDispatch = useDispatch;
```

except TypeScript knows the return type is `AppDispatch`.

------------------------------------------------------------------------

## 9. useAppSelector

Definition:

``` ts
export const useAppSelector:
    TypedUseSelectorHook<RootState> =
    useSelector;
```

Again, this is just a typed wrapper around `useSelector`.

------------------------------------------------------------------------

## 10. How useSelector Works

Usage:

``` ts
const value = useAppSelector(
    root => root.process.isFinalizationBackwardAction
);
```

The callback

``` ts
root => root.process.isFinalizationBackwardAction
```

is equivalent to

``` ts
function(root) {
    return root.process.isFinalizationBackwardAction;
}
```

`root` is **not** a global variable.

Redux internally does something conceptually similar to:

``` ts
const state = store.getState();

const value =
    callback(state);
```

So Redux passes the current state into your callback.

------------------------------------------------------------------------

## 11. Why not call store.getState() directly?

You could do:

``` ts
const state = store.getState();
const value = state.process.isFinalizationBackwardAction;
```

The problem:

This reads the state **only once**.

If the store changes later, React does not know your component depends
on it.

`useSelector` does two jobs:

1.  Reads the selected value.
2.  Subscribes the component to the store.

Flow:

``` text
Store changes
      │
      ▼
useSelector notices
      │
      ▼
Component re-renders
      │
      ▼
Selector runs again
```

This automatic subscription is the main reason React components use
`useSelector`.

------------------------------------------------------------------------

## 12. Overall Redux Flow

``` text
Component
    │
    ▼
dispatch(actionCreator(payload))
    │
    ▼
Action object
    │
    ▼
Redux Store
    │
    ▼
Matching reducer updates its slice
    │
    ▼
Store state changes
    │
    ▼
useSelector detects the change
    │
    ▼
React component re-renders
```

## Key Takeaways

-   The store is the application's shared state.
-   A slice owns one part of the store.
-   Reducers modify only their slice.
-   Action creators create action objects.
-   `dispatch()` sends actions into Redux.
-   `useSelector()` reads state and subscribes for updates.
-   `useAppSelector()` and `useAppDispatch()` are typed wrappers around
    the React Redux hooks.
