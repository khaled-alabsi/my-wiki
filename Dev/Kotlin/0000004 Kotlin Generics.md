### **1. What Are Generics?**
Generics allow you to create classes, functions, and interfaces that can operate on different types while still maintaining type safety. This improves **code reusability** and **type checking at compile time**.

---

### **2. Generic Classes**
A **generic class** can work with different data types.

#### Example: Generic Box Class
```kotlin
class Box<T>(val value: T) {
    fun getValue(): T = value
}

fun main() {
    val intBox = Box(42)
    val stringBox = Box("Hello")
    println(intBox.getValue())    // Output: 42
    println(stringBox.getValue()) // Output: Hello
}
```

**Key Points:**
- `<T>` is a type parameter.
- It is replaced with the actual type when the object is created (`Int`, `String`, etc.).

**Use Case:**
- Wrapping different types in a reusable container (e.g., a `Box`, `Result` class).

---

### **3. Generic Functions**
A **generic function** can be used with different types without duplicating code.

#### Example: Swapping Two Items
```kotlin
fun <T> swap(a: T, b: T): Pair<T, T> {
    return Pair(b, a)
}

fun main() {
    val swapped = swap(1, 2)
    println(swapped) // Output: (2, 1)
}
```

**Key Points:**
- `<T>` declares a type parameter for the function.
- The function can work with any type.

**Use Case:**
- Utility functions for data manipulation (e.g., swapping, sorting).

---

### **4. Bounded Type Parameters**
You can restrict the types that a generic function or class can accept by using **upper bounds** (`<T : Type>`).

#### Example: Accepting Only Numbers
```kotlin
fun <T : Number> add(a: T, b: T): Double {
    return a.toDouble() + b.toDouble()
}

fun main() {
    println(add(5, 10))       // Output: 15.0
    println(add(5.5, 4.5))    // Output: 10.0
    // println(add("Hello", "World")) // Compilation error
}
```

**Key Points:**
- `T : Number` means `T` must be a subclass of `Number` (e.g., `Int`, `Double`).

**Use Case:**
- Limiting generics to a specific family of types (e.g., numbers, collections).

---

### **5. Variance**
Variance helps control how generics behave in **inheritance hierarchies**. Kotlin provides `in` (contravariance) and `out` (covariance) to manage this.

---

#### **Covariance (`out`)**
Use `out` when a generic type is **produced** (read-only).

**Example: Producer Example**
```kotlin
class Producer<out T>(private val value: T) {
    fun getValue(): T = value
}

fun main() {
    val producer: Producer<Number> = Producer<Int>(42) // Covariance allows this
    println(producer.getValue()) // Output: 42
}
```

**Key Points:**
- `out T` means `T` can only be **produced**, not consumed (you can't pass `T` to methods).

**Use Case:**
- Read-only data sources (e.g., lists, streams).

---

#### **Contravariance (`in`)**
Use `in` when a generic type is **consumed** (write-only).

**Example: Consumer Example**
```kotlin
class Consumer<in T> {
    fun consume(value: T) {
        println("Consumed $value")
    }
}

fun main() {
    val consumer: Consumer<Int> = Consumer<Number>() // Contravariance allows this
    consumer.consume(42)
}
```

**Key Points:**
- `in T` means `T` can only be **consumed**, not produced (you can't return `T`).

**Use Case:**
- Write-only operations (e.g., processors, handlers).

---

### **6. Star Projections (`*`)**
When you don’t know the exact type of a generic, you can use `*` to represent an unknown type.

#### Example: Working with Unknown Generics
```kotlin
fun printList(list: List<*>) {
    list.forEach { println(it) }
}

fun main() {
    val intList = listOf(1, 2, 3)
    val stringList = listOf("A", "B", "C")
    printList(intList)   // Output: 1, 2, 3
    printList(stringList) // Output: A, B, C
}
```

**Use Case:**
- Working with APIs or libraries where the generic type is unknown.

---

### **7. Reified Type Parameters**
In normal generics, type information is erased at runtime (type erasure). However, **reified** type parameters preserve the type at runtime for inline functions.

#### Example: Filtering a List by Type
```kotlin
inline fun <reified T> filterByType(list: List<Any>): List<T> {
    return list.filterIsInstance<T>()
}

fun main() {
    val mixedList = listOf(1, "Kotlin", 3.0, "Java")
    val strings = filterByType<String>(mixedList)
    println(strings) // Output: [Kotlin, Java]
}
```

**Key Points:**
- `reified` allows access to the actual type at runtime.
- Only works with `inline` functions.

**Use Case:**
- Type-safe filtering or casting in collections.

---

### **8. Use-Site vs. Declaration-Site Variance**

#### Use-Site Variance
You specify `in` or `out` **at the point of use**.

**Example:**
```kotlin
fun printNumbers(numbers: List<out Number>) {
    numbers.forEach { println(it) }
}
```

#### Declaration-Site Variance
You specify `in` or `out` **when declaring a class or interface**.

**Example:**
```kotlin
interface Source<out T> {
    fun produce(): T
}
```

**Use Case:**
- Enforcing variance directly in APIs or libraries.

---

### **9. Generic Constraints**
You can use multiple constraints for generics using `where`.

#### Example:
```kotlin
fun <T> printDetails(item: T) where T : CharSequence, T : Comparable<T> {
    println(item.length)
    println(item.compareTo(item))
}

fun main() {
    printDetails("Hello") // Valid
    // printDetails(42) // Compilation error
}
```

**Use Case:**
- Creating APIs that require multiple capabilities (e.g., comparable and iterable objects).

---

### **10. Real-World Use Cases for Generics**

#### Case 1: Type-Safe Collections
```kotlin
fun <T> printCollection(items: Collection<T>) {
    items.forEach { println(it) }
}

fun main() {
    val numbers = listOf(1, 2, 3)
    val words = listOf("Hello", "World")
    printCollection(numbers)
    printCollection(words)
}
```

#### Case 2: Wrapping Results
```kotlin
sealed class Result<out T>
data class Success<T>(val data: T) : Result<T>()
data class Failure(val error: String) : Result<Nothing>()

fun <T> fetchData(): Result<T> {
    return Success("Data fetched successfully")
}
```

#### Case 3: Custom DSLs
```kotlin
class HTML {
    private val elements = mutableListOf<String>()

    fun element(tag: String, content: String) {
        elements.add("<$tag>$content</$tag>")
    }

    override fun toString(): String = elements.joinToString("\n")
}

fun <T> buildHTML(builder: T.() -> Unit): T where T : HTML {
    val html = HTML()
    html.builder()
    return html
}

fun main() {
    val html = buildHTML {
        element("h1", "Title")
        element("p", "Content")
    }
    println(html)
}
```
