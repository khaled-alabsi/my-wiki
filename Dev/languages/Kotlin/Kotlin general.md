Kotlin is a modern programming language that is fully interoperable with Java and focuses on brevity, safety, and readability. Since you know Java and JavaScript, I'll highlight Kotlin features by comparing them with Java and JavaScript.

### 1. **Basics: Variables and Types**
   - **Kotlin** has a cleaner syntax for defining variables:
     - `val` (immutable) vs. `var` (mutable), similar to `const` and `let` in JavaScript.
   ```kotlin
   val immutableValue: Int = 10 // Can't be reassigned
   var mutableValue: Int = 20  // Can be reassigned
   mutableValue = 30
   ```

   - Type inference is supported, so explicit types are optional:
   ```kotlin
   val name = "Kotlin" // Type inferred as String
   ```

### 2. **Functions**
   - Functions in Kotlin are concise and can have default parameters.
   ```kotlin
   fun greet(name: String = "World"): String {
       return "Hello, $name!"
   }

   println(greet())            // Output: Hello, World!
   println(greet("Kotlin"))    // Output: Hello, Kotlin!
   ```

   - Single-expression functions:
   ```kotlin
   fun square(x: Int) = x * x
   ```

Here are detailed explanations for **Null Safety (3)**, **Control Structures (5)**, **Collections and Lambdas (6)**, and **Coroutines (7)** in Kotlin:

---

### 3. **Null Safety**
Kotlin eliminates the common `NullPointerException` issue by enforcing null safety at compile time.

#### Nullable Types
- Use `?` to allow a variable to hold `null`.
  ```kotlin
  val nullableString: String? = null
  val nonNullableString: String = "Kotlin"
  ```

#### Safe Calls
- Use `?.` to call methods on a nullable object safely.
  ```kotlin
  val length = nullableString?.length // Returns null if nullableString is null
  ```

#### Elvis Operator (`?:`)
- Provide a fallback value if the nullable object is `null`.
  ```kotlin
  val length = nullableString?.length ?: 0 // If null, length is 0
  ```

#### Non-Null Assertion (`!!`)
- Forcefully assert that a value is non-null (use cautiously).
  ```kotlin
  val length = nullableString!!.length // Throws NullPointerException if null
  ```

---

### 4. **Data Classes**
   - Kotlin simplifies the creation of classes for storing data:
   ```kotlin
   data class User(val id: Int, val name: String)

   val user = User(1, "John")
   println(user) // Output: User(id=1, name=John)
   ```

---

### 5. **Control Structures**

#### `if` Expression
- `if` can return a value.
  ```kotlin
  val max = if (a > b) a else b
  ```

- Supports traditional blocks:
  ```kotlin
  val max = if (a > b) {
      println("a is greater")
      a
  } else {
      println("b is greater")
      b
  }
  ```

#### `when` Expression
- Simplifies complex `switch` or `if-else` logic.
  ```kotlin
  when (x) {
      1 -> println("One")
      2 -> println("Two")
      in 3..10 -> println("Between 3 and 10")
      else -> println("Other")
  }
  ```

- Can return a value:
  ```kotlin
  val result = when (x) {
      1 -> "One"
      2 -> "Two"
      else -> "Other"
  }
  ```

---

### 6. **Collections and Lambdas**

#### Creating Collections
- Kotlin supports `listOf`, `mutableListOf`, `setOf`, `mapOf`.
  ```kotlin
  val list = listOf(1, 2, 3) // Immutable
  val mutableList = mutableListOf(1, 2, 3) // Mutable
  ```

#### Functional Operations
- **`map`**: Transforms each element.
  ```kotlin
  val squared = list.map { it * it } // [1, 4, 9]
  ```

- **`filter`**: Filters elements based on a condition.
  ```kotlin
  val even = list.filter { it % 2 == 0 } // [2]
  ```

- **`reduce`**: Combines elements into a single result.
  ```kotlin
  val sum = list.reduce { acc, num -> acc + num } // 6
  ```

- **`forEach`**: Iterates through elements.
  ```kotlin
  list.forEach { println(it) }
  ```

- **`groupBy`**: Groups elements by a key.
  ```kotlin
  val grouped = listOf("apple", "banana", "apricot").groupBy { it.first() }
  // {a=[apple, apricot], b=[banana]}
  ```

---

### 7. **Coroutines**
Coroutines simplify asynchronous programming by avoiding callback hell.

#### Basic Coroutine
```kotlin
import kotlinx.coroutines.*

fun main() = runBlocking {
    launch { 
        delay(1000L) 
        println("World!") 
    }
    println("Hello,")
}
```
- **Output**:  
  ```
  Hello,  
  World!
  ```

#### `suspend` Functions
- A function marked `suspend` can be paused and resumed.
  ```kotlin
  suspend fun fetchData(): String {
      delay(1000L) // Simulates network delay
      return "Data"
  }
  ```

#### Async/Await
- Perform concurrent operations.
  ```kotlin
  suspend fun compute(): Int {
      delay(1000)
      return 42
  }

  fun main() = runBlocking {
      val result1 = async { compute() }
      val result2 = async { compute() }
      println("Sum: ${result1.await() + result2.await()}")
  }
  ```

#### Coroutine Scopes
- **`GlobalScope`**: Lives for the application lifecycle.
- **`runBlocking`**: Blocks the main thread (not recommended for large apps).
- **`CoroutineScope`**: Encapsulates and manages coroutines.
  ```kotlin
  class MyViewModel : CoroutineScope {
      private val job = Job()
      override val coroutineContext = Dispatchers.Main + job
  }
  ```


### 5. **Control Structures**
   - `if` is an expression, not just a statement:
   ```kotlin
   val max = if (a > b) a else b
   ```

   - `when` replaces `switch`:
   ```kotlin
   when (x) {
       1 -> println("One")
       2 -> println("Two")
       else -> println("Other")
   }
   ```

### 6. **Collections and Lambdas**
   - Kotlin has built-in support for functional programming with `map`, `filter`, `reduce`, etc.:
   ```kotlin
   val numbers = listOf(1, 2, 3, 4)
   val doubled = numbers.map { it * 2 }
   val evenNumbers = numbers.filter { it % 2 == 0 }
   ```

### 7. **Coroutines**
   - Kotlin offers coroutines for asynchronous programming, similar to JavaScript's async/await:
   ```kotlin
   suspend fun fetchData(): String {
       delay(1000)
       return "Data"
   }

   GlobalScope.launch {
       val data = fetchData()
       println(data)
   }
   ```

### 8. **Interoperability with Java**
   - Call Java code directly from Kotlin.
   - Java classes and methods are accessible with no extra work.

   ```java
   // Java
   public class JavaClass {
       public static String greet() {
           return "Hello from Java!";
       }
   }
   ```

   ```kotlin
   // Kotlin
   println(JavaClass.greet()) // Output: Hello from Java!
   ```

### 9. **Extension Functions**
   - Add new functionality to existing classes:
   ```kotlin
   fun String.removeSpaces() = this.replace(" ", "")

   println("Kotlin is fun".removeSpaces()) // Output: Kotlinisfun
   ```
