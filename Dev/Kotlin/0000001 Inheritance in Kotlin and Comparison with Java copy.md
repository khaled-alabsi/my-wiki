### Inheritance in Kotlin and Comparison with Java

#### **Kotlin: Key Concepts**
1. **Classes are Final by Default**:  
   - Kotlin classes are `final` by default, meaning they cannot be inherited unless explicitly marked as `open`.  
     ```kotlin
     open class Parent
     class Child : Parent()
     ```

2. **Explicit Overriding**:  
   - Methods and properties in the parent class must also be marked as `open` to allow overriding. The child class uses the `override` keyword.  
     ```kotlin
     open class Parent {
         open fun greet() = "Hello"
     }
     class Child : Parent() {
         override fun greet() = "Hi"
     }
     ```

3. **Primary Constructor in Inheritance**:  
   - If the parent class has a primary constructor, it must be explicitly called using `: super(...)`.  
     ```kotlin
     open class Parent(val name: String)
     class Child(name: String) : Parent(name)
     ```

4. **No `extends` or `implements` Keywords**:  
   - Kotlin uses `:` for both class inheritance and interface implementation.  
     ```kotlin
     open class Parent
     interface Worker
     class Child : Parent(), Worker
     ```

---

#### **Java: Key Concepts**
1. **Classes are Open by Default**:  
   - Java classes are not `final` by default, allowing inheritance unless explicitly marked `final`.  
     ```java
     class Parent {}
     class Child extends Parent {}
     ```

2. **Overriding Methods**:  
   - Methods can be overridden unless marked `final`. No need for explicit keywords like Kotlin's `open` or `override`.  
     ```java
     class Parent {
         public String greet() {
             return "Hello";
         }
     }
     class Child extends Parent {
         @Override
         public String greet() {
             return "Hi";
         }
     }
     ```

3. **Constructor Chaining**:  
   - Use `super(...)` to call the parent class constructor, similar to Kotlin.  
     ```java
     class Parent {
         Parent(String name) {}
     }
     class Child extends Parent {
         Child(String name) {
             super(name);
         }
     }
     ```

4. **Separate Keywords for Inheritance and Interfaces**:  
   - Java uses `extends` for classes and `implements` for interfaces.  
     ```java
     class Parent {}
     interface Worker {}
     class Child extends Parent implements Worker {}
     ```

---

### **Comparison Table**

| Feature                        | **Kotlin**                               | **Java**                                |
|--------------------------------|------------------------------------------|-----------------------------------------|
| **Default Class Behavior**     | `final` (explicit `open` for inheritance) | Open for inheritance                   |
| **Method/Property Override**   | Explicit: `open` and `override` keywords | Implicit: Use `@Override` annotation   |
| **Inheritance Syntax**         | `:` for both classes and interfaces      | `extends` for classes, `implements` for interfaces |
| **Constructor Invocation**     | `: super(...)`                          | `super(...)`                           |
| **Multiple Inheritance**       | Only via interfaces                     | Only via interfaces                    |

---

### Key Differences
1. **Default Behavior**: Kotlin restricts inheritance by default (`final`), promoting immutability, while Java allows inheritance unless explicitly restricted.
2. **Explicit Overriding**: Kotlin requires both `open` in the parent and `override` in the child, whereas Java only uses `@Override` as a best practice.
3. **Syntax**: Kotlin simplifies inheritance syntax with `:`, while Java distinguishes between `extends` and `implements`.

Here’s a detailed example comparing **Kotlin** and **Java** for an `Animal` class with multiple use cases, focusing on **inheritance**, **overriding**, and **constructors**:

---

### **Kotlin Implementation**

#### Base Class: `Animal`
```kotlin
open class Animal(val name: String, val age: Int) {
    open fun speak(): String {
        return "$name makes a sound"
    }

    open fun eat() {
        println("$name is eating")
    }
}
```

#### Derived Class: `Dog`
```kotlin
class Dog(name: String, age: Int, val breed: String) : Animal(name, age) {
    override fun speak(): String {
        return "$name barks"
    }

    override fun eat() {
        println("$name is eating dog food")
    }

    fun fetch() {
        println("$name is fetching a ball")
    }
}
```

#### Derived Class: `Cat`
```kotlin
class Cat(name: String, age: Int, val color: String) : Animal(name, age) {
    override fun speak(): String {
        return "$name meows"
    }
}
```

#### Usage
```kotlin
fun main() {
    val dog = Dog("Rex", 5, "Labrador")
    println(dog.speak()) // Rex barks
    dog.eat()            // Rex is eating dog food
    dog.fetch()          // Rex is fetching a ball

    val cat = Cat("Mittens", 3, "Black")
    println(cat.speak()) // Mittens meows
    cat.eat()            // Mittens is eating
}
```

#### What Cannot Be Done in Kotlin
1. **Direct instantiation of `Animal` if it’s abstract**:
   ```kotlin
   abstract open class Animal // Makes it non-instantiable
   ```

2. **Overriding final methods**:
   ```kotlin
   open class Animal {
       final fun cannotBeOverridden() {}
   }
   ```

---

### **Java Implementation**

#### Base Class: `Animal`
```java
public class Animal {
    private String name;
    private int age;

    public Animal(String name, int age) {
        this.name = name;
        this.age = age;
    }

    public String speak() {
        return name + " makes a sound";
    }

    public void eat() {
        System.out.println(name + " is eating");
    }

    public String getName() {
        return name;
    }
}
```

#### Derived Class: `Dog`
```java
public class Dog extends Animal {
    private String breed;

    public Dog(String name, int age, String breed) {
        super(name, age);
        this.breed = breed;
    }

    @Override
    public String speak() {
        return getName() + " barks";
    }

    @Override
    public void eat() {
        System.out.println(getName() + " is eating dog food");
    }

    public void fetch() {
        System.out.println(getName() + " is fetching a ball");
    }
}
```

#### Derived Class: `Cat`
```java
public class Cat extends Animal {
    private String color;

    public Cat(String name, int age, String color) {
        super(name, age);
        this.color = color;
    }

    @Override
    public String speak() {
        return getName() + " meows";
    }
}
```

#### Usage
```java
public class Main {
    public static void main(String[] args) {
        Dog dog = new Dog("Rex", 5, "Labrador");
        System.out.println(dog.speak()); // Rex barks
        dog.eat();                       // Rex is eating dog food
        dog.fetch();                     // Rex is fetching a ball

        Cat cat = new Cat("Mittens", 3, "Black");
        System.out.println(cat.speak()); // Mittens meows
        cat.eat();                       // Mittens is eating
    }
}
```

#### What Cannot Be Done in Java
1. **Inheritance from a final class**:
   ```java
   public final class Animal {}
   ```

2. **Overriding final methods**:
   ```java
   public class Animal {
       public final void cannotBeOverridden() {}
   }
   ```

---

### **Kotlin vs Java: Comparison Table**

| Feature                         | Kotlin                                  | Java                                   |
|----------------------------------|-----------------------------------------|----------------------------------------|
| **Class Declaration**            | Classes are `final` by default (`open` to inherit). | Classes are open by default unless `final`. |
| **Overriding Methods**           | Use `open` in parent and `override` in child. | Override directly, use `@Override` annotation. |
| **Constructors**                 | Primary and secondary constructors.     | Single or multiple constructors.       |
| **Final Methods**                | Mark with `final` to prevent overriding. | Mark with `final` to prevent overriding. |
| **Abstract Classes**             | Explicitly use `abstract`.              | Explicitly use `abstract`.             |
| **Syntax**                       | Concise with `: super(...)`.            | Uses `super(...)`.                     |
| **Top-Level Declarations**       | Possible (no need for a class wrapper). | Not possible, everything must be inside a class. |




In Kotlin, the reason why `name` and `age` don't have `val` in this line:

```kotlin
class Dog(name: String, age: Int, val breed: String) : Animal(name, age)
```

is because `name` and `age` are parameters being passed to the **base class (`Animal`) constructor**, not properties of the `Dog` class. Let's break it down:

---

### Key Points:

1. **`name` and `age` Are Handled by the Base Class (`Animal`)**:
   - In `Animal`, `name` and `age` are already declared as properties:
     ```kotlin
     open class Animal(val name: String, val age: Int)
     ```
   - When `Dog` extends `Animal`, it passes `name` and `age` to the `Animal` constructor via `super(name, age)` (implicitly in Kotlin).

2. **`val` or `var` in Constructor**:
   - Adding `val` or `var` in the constructor of a class makes the parameter a **property of that class**.
   - For example:
     ```kotlin
     class Dog(val name: String, val age: Int, val breed: String) : Animal(name, age)
     ```
     Here, `name` and `age` would also become properties of `Dog` in addition to `Animal`.

3. **Avoid Redundancy**:
   - Since `name` and `age` are already properties of `Animal`, declaring them as `val` in `Dog` would create **duplicate properties** in `Dog`. This is unnecessary and redundant.

4. **`breed` is a New Property in `Dog`**:
   - `breed` is not part of the `Animal` class, so it is declared as a `val` to make it a property of `Dog`.

---

### Example with Explanation:
#### Base Class
```kotlin
open class Animal(val name: String, val age: Int)
```

- `name` and `age` are already declared as properties in `Animal`.

#### Subclass
```kotlin
class Dog(name: String, age: Int, val breed: String) : Animal(name, age)
```

- `name` and `age` are passed to `Animal`'s constructor.
- `breed` is a new property added specifically for `Dog`.

#### What If You Add `val` to `name` and `age` in `Dog`?
```kotlin
class Dog(val name: String, val age: Int, val breed: String) : Animal(name, age)
```

This would compile, but it creates **new properties** `name` and `age` in `Dog`, shadowing those in `Animal`. Accessing `name` and `age` from `Dog` would refer to `Dog`'s versions, not `Animal`'s. This is usually undesirable because it creates ambiguity and redundancy.

---

### Conclusion:
- In `class Dog(name: String, age: Int, val breed: String) : Animal(name, age)`, `name` and `age` are constructor parameters that are passed to the base class (`Animal`) where they are already declared as properties. Therefore, they don't need `val` in `Dog`.