### **1. Loops**

#### **`for` Loop**
Iterates over a sequence by incrementing or decrementing.
```typescript
for (let i: number = 0; i < 5; i++) {
  console.log(i); // Output: 0, 1, 2, 3, 4
}
// Arguments: 
// - `i = 0` (initialization)
// - `i < 5` (condition to continue the loop)
// - `i++` (update step after each iteration)
```

---

#### **`while` Loop**
Repeats as long as the condition is `true`.
```typescript
let i: number = 0;
while (i < 5) {
  console.log(i); // Output: 0, 1, 2, 3, 4
  i++;
}
// Arguments: 
// - `i < 5` (loop continues while condition is true)
```

---

#### **`do-while` Loop**
Executes the body at least once before checking the condition.
```typescript
let i: number = 0;
do {
  console.log(i); // Output: 0, 1, 2, 3, 4
  i++;
} while (i < 5);
// Arguments:
// - Condition `i < 5` checked after each iteration.
```

---

#### **`for-of` Loop**
Iterates over iterable objects (e.g., arrays, strings).
```typescript
const arr: number[] = [10, 20, 30];
for (const value of arr) {
  console.log(value); // Output: 10, 20, 30
}
// Arguments:
// - `arr` (iterable array)
// - `value` (current element in the array)
```

---

#### **`for-in` Loop**
Iterates over the keys of an object or array.
```typescript
const obj: { [key: string]: number } = { a: 1, b: 2, c: 3 };
for (const key in obj) {
  console.log(key, obj[key]); // Output: a 1, b 2, c 3
}
// Arguments:
// - `obj` (object being iterated over)
// - `key` (current property key)
```

---

### **2. Array Functions**

#### **`forEach()`**
Executes a function for each element in the array.
```typescript
const arr: number[] = [1, 2, 3];
arr.forEach((value, index, array) => {
  console.log(`Value: ${value}, Index: ${index}, Array: ${array}`);
});
// Arguments:
// - `value` (current element)
// - `index` (current index)
// - `array` (original array)
```

---

#### **`map()`**
Creates a new array by applying a function to each element.
```typescript
const arr: number[] = [1, 2, 3];
const squared: number[] = arr.map((value, index, array) => value * value);
console.log(squared); // Output: [1, 4, 9]
// Arguments:
// - `value` (current element)
// - `index` (current index)
// - `array` (original array)
```

---

#### **`filter()`**
Creates a new array with elements that satisfy a condition.
```typescript
const arr: number[] = [1, 2, 3, 4];
const even: number[] = arr.filter((value, index, array) => value % 2 === 0);
console.log(even); // Output: [2, 4]
// Arguments:
// - `value` (current element)
// - `index` (current index)
// - `array` (original array)
```

---

#### **`reduce()`**
Reduces the array to a single value.
```typescript
const arr: number[] = [1, 2, 3, 4];
const sum: number = arr.reduce((acc, value, index, array) => acc + value, 0);
console.log(sum); // Output: 10
// Arguments:
// - `acc` (accumulator)
// - `value` (current element)
// - `index` (current index)
// - `array` (original array)
// - `0` (initial value for `acc`)
```

---

#### **`find()`**
Returns the first element that satisfies the condition.
```typescript
const arr: number[] = [1, 2, 3, 4];
const firstEven: number | undefined = arr.find((value, index, array) => value % 2 === 0);
console.log(firstEven); // Output: 2
// Arguments:
// - `value` (current element)
// - `index` (current index)
// - `array` (original array)
```

---

#### **`findIndex()`**
Returns the index of the first element that satisfies the condition.
```typescript
const arr: number[] = [1, 2, 3, 4];
const index: number = arr.findIndex((value, index, array) => value > 2);
console.log(index); // Output: 2
// Arguments:
// - `value` (current element)
// - `index` (current index)
// - `array` (original array)
```

---

#### **`every()`**
Checks if all elements satisfy the condition.
```typescript
const arr: number[] = [2, 4, 6];
const allEven: boolean = arr.every((value, index, array) => value % 2 === 0);
console.log(allEven); // Output: true
// Arguments:
// - `value` (current element)
// - `index` (current index)
// - `array` (original array)
```

---

#### **`some()`**
Checks if at least one element satisfies the condition.
```typescript
const arr: number[] = [1, 3, 4];
const hasEven: boolean = arr.some((value, index, array) => value % 2 === 0);
console.log(hasEven); // Output: true
// Arguments:
// - `value` (current element)
// - `index` (current index)
// - `array` (original array)
```

---

#### **`sort()`**
Sorts the array based on a comparison function.
```typescript
const arr: number[] = [3, 1, 2];
arr.sort((a, b) => a - b);
console.log(arr); // Output: [1, 2, 3]
// Arguments:
// - `a` (first element to compare)
// - `b` (second element to compare)
```

---

#### **`flatMap()`**
Maps and flattens nested arrays.
```typescript
const nested: number[][] = [[1, 2], [3, 4]];
const flat: number[] = nested.flatMap((subArray) => subArray.map((value) => value * 2));
console.log(flat); // Output: [2, 4, 6, 8]
// Arguments:
// - `subArray` (current nested array element)
// - `value` (current element inside the subarray)
```

---

#### **`includes()`**
Checks if an array includes a specific value.
```typescript
const arr: number[] = [1, 2, 3];
const hasValue: boolean = arr.includes(2);
console.log(hasValue); // Output: true
// Arguments:
// - `value` (value to check for inclusion)
```

---

#### **`reverse()`**
Reverses the array in place.
```typescript
const arr: number[] = [1, 2, 3];
arr.reverse();
console.log(arr); // Output: [3, 2, 1]
// No arguments.
```

---

#### **`splice()`**
Modifies the array by adding or removing elements.
```typescript
const arr: number[] = [1, 2, 3];
arr.splice(1, 1, 99); // Removes 1 element at index 1, adds 99
console.log(arr); // Output: [1, 99, 3]
// Arguments:
// - `start` (index to start)
// - `deleteCount` (number of elements to remove)
// - `...items` (elements to add)
```

---

#### **`concat()`**
Merges two or more arrays into one.
```typescript
const arr1: number[] = [1, 2];
const arr2: number[] = [3, 4];
const merged: number[] = arr1.concat(arr2);
console.log(merged); // Output: [1, 2, 3, 4]
// Arguments:
// - Arrays to concatenate
```

---

### **3. Object Functions**

#### **`Object.keys()`**
Returns an array of object keys.
```typescript
const obj: { [key: string]: number } = { a: 1, b: 2, c: 3 };
const keys: string[] = Object.keys(obj);
console.log(keys); // Output: ["a", "b", "c"]
```

---

#### **`Object.values()`**
Returns an array of object values.
```typescript
const obj: { [key: string]: number } = { a: 1, b: 2, c: 3 };
const values: number[] = Object.values(obj);
console.log(values); // Output: [1, 2, 3]
```

---

#### **`Object.entries()`**
Returns an array of `[key, value]` pairs.
```typescript
const obj: { [key: string]: number } = { a: 1, b: 2, c: 3 };
const entries: [string, number][] = Object.entries(obj);
console.log(entries); // Output: [["a", 1], ["b", 2], ["c", 3]]
```

--- 
