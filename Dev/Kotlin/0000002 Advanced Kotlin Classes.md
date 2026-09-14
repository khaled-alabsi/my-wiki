Here’s a **detailed explanation of Advanced Kotlin Classes** with examples and use cases:

---

### **1. Abstract Classes and Interfaces**
Kotlin supports both `abstract classes` and `interfaces`. Abstract classes are used when you want to share behavior among subclasses, while interfaces are used to define a contract.

#### Abstract Classes
- Can have both abstract (unimplemented) and concrete (implemented) methods.
- Cannot be instantiated directly.

**Example:**
```kotlin
abstract class Animal {
    abstract fun sound(): String
    fun eat() = "Eating..."
}

class Dog : Animal() {
    override fun sound() = "Woof!"
}

fun main() {
    val dog = Dog()
    println(dog.sound()) // Output: Woof!
    println(dog.eat())   // Output: Eating...
}
```

**Use Case:**
- Creating a hierarchy of related classes with shared behavior.

---

#### Interfaces
- Can define properties and methods but cannot store state (no fields).
- Can have default method implementations.

**Example:**
```kotlin
interface Flyable {
    fun fly(): String
    fun land() = "Landing..."
}

class Bird : Flyable {
    override fun fly() = "Flying high!"
}

fun main() {
    val bird = Bird()
    println(bird.fly()) // Output: Flying high!
    println(bird.land()) // Output: Landing...
}
```

**Use Case:**
- Creating reusable contracts across unrelated classes.

---

### **2. Sealed Classes**
A **sealed class** is a type of abstract class that restricts subclassing to a predefined set of classes. It’s used to represent **hierarchies with limited types**.

**Example:**
```kotlin
sealed class Shape {
    data class Circle(val radius: Double) : Shape()
    data class Rectangle(val width: Double, val height: Double) : Shape()
}

fun calculateArea(shape: Shape): Double = when (shape) {
    is Shape.Circle -> Math.PI * shape.radius * shape.radius
    is Shape.Rectangle -> shape.width * shape.height
}

fun main() {
    val circle = Shape.Circle(5.0)
    println(calculateArea(circle)) // Output: 78.53981633974483
}
```

**Use Case:**
- Representing states (e.g., Success, Error, Loading) in network responses.
- Enforcing exhaustive `when` statements.

---

### **3. Data Classes**
Data classes are designed to hold data. They automatically generate `equals()`, `hashCode()`, `toString()`, `copy()`, and destructuring methods.

**Example:**
```kotlin
data class User(val id: Int, val name: String)

fun main() {
    val user = User(1, "John")
    val updatedUser = user.copy(name = "Jane")
    println(user)           // Output: User(id=1, name=John)
    println(updatedUser)    // Output: User(id=1, name=Jane)
}
```

**Use Case:**
- Creating models for APIs, databases, or other data containers.

---

### **4. Object Declarations and Singletons**
Kotlin provides `object` declarations to create **singleton** instances without additional boilerplate.

**Example:**
```kotlin
object Database {
    val name = "MainDB"
    fun connect() = "Connected to $name"
}

fun main() {
    println(Database.connect()) // Output: Connected to MainDB
}
```

**Use Case:**
- Managing global state or shared resources (e.g., configuration, logging).

---

### **5. Companion Objects**
Companion objects are like static members in Java. They belong to the class and not the instance.

**Example:**
```kotlin
class MathUtils {
    companion object {
        fun square(x: Int) = x * x
    }
}

fun main() {
    println(MathUtils.square(4)) // Output: 16
}
```

**Use Case:**
- Adding utility methods that logically belong to a class.

---

### **6. Inner and Nested Classes**
Kotlin supports both `nested` (static-like) and `inner` (non-static) classes.

#### Nested Classes
- Does not hold a reference to the outer class.
- Use `class` inside another class.

**Example:**
```kotlin
class Outer {
    class Nested {
        fun greet() = "Hello from Nested"
    }
}

fun main() {
    println(Outer.Nested().greet()) // Output: Hello from Nested
}
```

#### Inner Classes
- Holds a reference to the outer class.
- Use `inner` keyword.

**Example:**
```kotlin
class Outer(val greeting: String) {
    inner class Inner {
        fun greet() = "Outer says: $greeting"
    }
}

fun main() {
    val outer = Outer("Hello")
    val inner = outer.Inner()
    println(inner.greet()) // Output: Outer says: Hello
}
```

**Use Case:**
- Nested for independent logic, inner for tightly coupled behavior.

---

### **7. Enum Classes**
Enums represent a fixed set of constants. You can add properties and methods to enums.

**Example:**
```kotlin
enum class Direction(val degrees: Int) {
    NORTH(0), EAST(90), SOUTH(180), WEST(270);

    fun description() = "Direction is $name at $degrees°"
}

fun main() {
    val direction = Direction.EAST
    println(direction.description()) // Output: Direction is EAST at 90°
}
```

**Use Case:**
- Representing constant sets (e.g., days of the week, directions, states).

---

### **8. Generic Classes**
Generics allow you to write flexible and reusable classes.

**Example:**
```kotlin
class Box<T>(val value: T)

fun main() {
    val intBox = Box(5)
    val stringBox = Box("Hello")
    println(intBox.value)    // Output: 5
    println(stringBox.value) // Output: Hello
}
```

**Use Case:**
- Container classes (e.g., List, Map).

---

### **9. Delegation**
Kotlin supports **interface delegation**, allowing an object to delegate behavior to another object.

**Example:**
```kotlin
interface Printer {
    fun print(): String
}

class DefaultPrinter : Printer {
    override fun print() = "Printing..."
}

class AdvancedPrinter(private val delegate: Printer) : Printer by delegate {
    fun advancedPrint() = "Advanced " + delegate.print()
}

fun main() {
    val printer = AdvancedPrinter(DefaultPrinter())
    println(printer.print())          // Output: Printing...
    println(printer.advancedPrint())  // Output: Advanced Printing...
}
```

**Use Case:**
- Reusing functionality without inheritance.

---

### Real-World Use Cases for Advanced Classes

1. **Modeling Domain Data**:
   - Use `data classes` for models and `sealed classes` for result types (e.g., `Success`, `Error`).

2. **Dependency Injection**:
   - Use `companion objects` or `object` declarations to manage shared resources like a service locator.

3. **Design Patterns**:
   - Implement **Singleton** using `object`.
   - Use `interface delegation` for the **Decorator** pattern.

4. **State Management**:
   - Use `sealed classes` to represent UI states (e.g., `Loading`, `Success`, `Error`).
