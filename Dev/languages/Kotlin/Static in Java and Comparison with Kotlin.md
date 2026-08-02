### Explanation of `static` in Java and Comparison with Kotlin

#### **Static in Java**

The `static` keyword in Java is used to define members (variables, methods, or nested classes) that belong to the class itself, rather than to any specific object of the class. Static members are shared across all instances of the class.

---

### 1. **Static Variables**
- A `static` variable is shared by all instances of the class. It belongs to the class, not to any specific object.
- Example:
    ```java
    public class Example {
        static int count = 0; // Shared variable

        public Example() {
            count++; // Increment every time an instance is created
        }
    }

    public class Main {
        public static void main(String[] args) {
            new Example();
            new Example();
            System.out.println(Example.count); // Output: 2
        }
    }
    ```

---

### 2. **Static Methods**
- A `static` method can be called without creating an instance of the class. It can only access other static members of the class.
- Example:
    ```java
    public class Example {
        static int count = 0;

        static void increment() {
            count++;
        }
    }

    public class Main {
        public static void main(String[] args) {
            Example.increment(); // Call without an instance
            System.out.println(Example.count); // Output: 1
        }
    }
    ```

---

### 3. **Static Blocks**
- A `static` block is used for static initialization. It is executed when the class is loaded into memory, before any object is created or `static` methods are accessed.
- Example:
    ```java
    public class Example {
        static int count;

        static { // Static block
            count = 10; // Initialize static variables
        }
    }

    public class Main {
        public static void main(String[] args) {
            System.out.println(Example.count); // Output: 10
        }
    }
    ```

---

### 4. **Static Classes**
- In Java, a `static` class can only be a nested class. It does not have an implicit reference to the outer class, making it independent of any instance of the outer class.
- Example:
    ```java
    public class Outer {
        static class StaticNested {
            static void display() {
                System.out.println("Static nested class");
            }
        }
    }

    public class Main {
        public static void main(String[] args) {
            Outer.StaticNested.display(); // Access without creating Outer
        }
    }
    ```

---

#### **Static in Kotlin**

Kotlin does not have the `static` keyword. Instead, it uses **companion objects**, **top-level declarations**, and **object declarations** to achieve similar functionality.

1. **Static Variables in Kotlin**
   - Use **companion objects** for class-level properties.
   ```kotlin
   class Example {
       companion object {
           var count: Int = 0
       }
   }

   fun main() {
       Example.count++
       println(Example.count) // Output: 1
   }
   ```

2. **Static Methods in Kotlin**
   - Defined within a companion object or as top-level functions.
   ```kotlin
   class Example {
       companion object {
           fun increment() {
               println("Static-like method")
           }
       }
   }

   fun main() {
       Example.increment()
   }
   ```

3. **Static Blocks in Kotlin**
   - Use `init` blocks inside companion objects for static-like initialization.
   ```kotlin
   class Example {
       companion object {
           var count: Int

           init {
               count = 10 // Static-like initialization
           }
       }
   }

   fun main() {
       println(Example.count) // Output: 10
   }
   ```

4. **Static Classes in Kotlin**
   - Use `object` declarations or nested classes.
   ```kotlin
   class Outer {
       object StaticNested {
           fun display() {
               println("Static-like nested class")
           }
       }
   }

   fun main() {
       Outer.StaticNested.display()
   }
   ```

---

### **Comparison Table**

| Feature                | **Java**                                   | **Kotlin**                                                   |
|-------------------------|--------------------------------------------|-------------------------------------------------------------|
| **Static Variables**    | Use `static` keyword.                     | Use `companion object` or top-level variables.              |
| **Static Methods**      | Use `static` keyword.                     | Use `companion object` or top-level functions.              |
| **Static Blocks**       | Use `static` block for initialization.    | Use `init` block inside companion object.                   |
| **Static Classes**      | Use `static` keyword for nested classes.  | Use `object` declarations or top-level classes.             |

---

### Key Differences
1. Kotlin’s `companion object` provides a more structured way to handle static-like behavior.
2. Kotlin encourages **top-level declarations**, reducing reliance on static members altogether.
3. Java explicitly uses the `static` keyword for clarity, whereas Kotlin leverages object-oriented and functional paradigms to achieve the same.