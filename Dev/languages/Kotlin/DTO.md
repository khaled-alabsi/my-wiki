### Creating a DTO (Data Transfer Object) in Kotlin and Java

A DTO is a simple object used to transfer data between layers, typically containing only fields and their getters/setters without any business logic.

---

## **Kotlin**

Kotlin provides multiple concise ways to create DTOs.

### 1. **Using `data class`**
- The most common way to create a DTO in Kotlin. It provides built-in features like `equals()`, `hashCode()`, `toString()`, and `copy()`.

```kotlin
data class UserDto(val id: Int, val name: String, val email: String)
```

#### Usage:
```kotlin
val user = UserDto(1, "Alice", "alice@example.com")
println(user.name) // Access field
println(user)      // toString(): UserDto(id=1, name=Alice, email=alice@example.com)
```

---

### 2. **Class with Properties and Custom Getters/Setters**
- Used when additional logic is needed in getters or setters.

```kotlin
class UserDto(var id: Int, var name: String, var email: String) {
    var isActive: Boolean = true
        get() = field && id > 0
        set(value) {
            field = value
        }
}
```

#### Usage:
```kotlin
val user = UserDto(1, "Alice", "alice@example.com")
println(user.isActive) // true
user.isActive = false
println(user.isActive) // false
```

Here are more examples of Kotlin classes with properties and custom getters/setters to handle different use cases:

---

### 1. **Basic Custom Getter and Setter**
Adding validation in a setter or derived logic in a getter.

```kotlin
class Product(var price: Double, var discount: Double) {
    var discountedPrice: Double = price
        get() = price - (price * (discount / 100)) // Custom getter

        set(value) { // Custom setter
            if (value > price) {
                println("Discounted price can't be more than original price!")
            } else {
                field = value
            }
        }
}
```

#### Usage:
```kotlin
fun main() {
    val product = Product(100.0, 10.0)
    println(product.discountedPrice) // Output: 90.0

    product.discountedPrice = 95.0 // Discounted price can't be more than original price!
}
```

---

### 2. **Lazy Initialization**
Using a custom getter to initialize a property when accessed for the first time.

```kotlin
class User(val firstName: String, val lastName: String) {
    val fullName: String
        get() {
            println("Computing full name...")
            return "$firstName $lastName"
        }
}
```

#### Usage:
```kotlin
fun main() {
    val user = User("John", "Doe")
    println(user.fullName) // Output: Computing full name... John Doe
    println(user.fullName) // Output: Computing full name... John Doe
}
```

---

### 3. **Computed Property Without Backing Field**
When the value of a property is derived dynamically.

```kotlin
class Rectangle(var width: Double, var height: Double) {
    val area: Double
        get() = width * height // No backing field, always computed dynamically
}
```

#### Usage:
```kotlin
fun main() {
    val rectangle = Rectangle(5.0, 4.0)
    println(rectangle.area) // Output: 20.0

    rectangle.width = 10.0
    println(rectangle.area) // Output: 40.0
}
```

---

### 4. **Backing Field Example**
Using a backing field to manage underlying property storage.

```kotlin
class Person {
    var name: String = "Unknown"
        set(value) {
            field = value.uppercase() // Store the uppercase version
        }
}
```

#### Usage:
```kotlin
fun main() {
    val person = Person()
    person.name = "john"
    println(person.name) // Output: JOHN
}
```

---

### 5. **Conditional Access in Getter**
Adding conditional logic to a getter.

```kotlin
class Employee(var workHours: Int) {
    val status: String
        get() = if (workHours >= 40) "Full-time" else "Part-time"
}
```

#### Usage:
```kotlin
fun main() {
    val employee = Employee(30)
    println(employee.status) // Output: Part-time

    employee.workHours = 50
    println(employee.status) // Output: Full-time
}
```

---

### 6. **Read-Only Property with Custom Getter**
Allowing only a getter for derived properties.

```kotlin
class Circle(var radius: Double) {
    val circumference: Double
        get() = 2 * Math.PI * radius // Read-only property
}
```

#### Usage:
```kotlin
fun main() {
    val circle = Circle(5.0)
    println(circle.circumference) // Output: 31.41592653589793
}
```

---

### 7. **Custom Setter with Multiple Conditions**
Adding multiple checks before setting a property.

```kotlin
class Account {
    var balance: Double = 0.0
        set(value) {
            if (value < 0) {
                println("Balance cannot be negative!")
            } else if (value > 1_000_000) {
                println("Balance exceeds maximum limit!")
            } else {
                field = value
            }
        }
}
```

#### Usage:
```kotlin
fun main() {
    val account = Account()
    account.balance = -500.0 // Output: Balance cannot be negative!
    account.balance = 2_000_000.0 // Output: Balance exceeds maximum limit!
    account.balance = 10_000.0
    println(account.balance) // Output: 10,000.0
}
```

---

### 8. **Encapsulated State with Custom Setter**
Hiding internal state and applying transformations before setting the value.

```kotlin
class Temperature {
    private var _celsius: Double = 0.0

    var fahrenheit: Double
        get() = _celsius * 9 / 5 + 32 // Convert Celsius to Fahrenheit
        set(value) {
            _celsius = (value - 32) * 5 / 9 // Convert Fahrenheit to Celsius
        }
}
```

#### Usage:
```kotlin
fun main() {
    val temp = Temperature()
    temp.fahrenheit = 98.6
    println(temp.fahrenheit) // Output: 98.6
}
```

These examples demonstrate how to use custom getters and setters in Kotlin to create more dynamic and functional class properties while keeping the syntax concise and intuitive.
---

### 3. **Using `Map` to DTO Conversion**
- When the structure of DTOs is dynamic or needs conversion from maps.

```kotlin
class UserDto(val data: Map<String, Any?>) {
    val id: Int by data
    val name: String by data
    val email: String by data
}
```

#### Usage:
```kotlin
val user = UserDto(mapOf("id" to 1, "name" to "Alice", "email" to "alice@example.com"))
println(user.name) // Alice
```

---

### 4. **Manual Declaration**
- A verbose way similar to Java.

```kotlin
class UserDto(val id: Int, val name: String, val email: String) {
    override fun toString(): String {
        return "UserDto(id=$id, name=$name, email=$email)"
    }
}
```

---

## **Java**

In Java, DTOs are typically implemented using plain classes with fields, getters, setters, and optional additional methods.

### 1. **Plain Java Class**
- The traditional approach with private fields and public getters/setters.

```java
public class UserDto {
    private int id;
    private String name;
    private String email;

    public UserDto() {}

    public UserDto(int id, String name, String email) {
        this.id = id;
        this.name = name;
        this.email = email;
    }

    public int getId() { return id; }
    public void setId(int id) { this.id = id; }
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }

    @Override
    public String toString() {
        return "UserDto{id=" + id + ", name='" + name + "', email='" + email + "'}";
    }
}
```

---

### 2. **Using Libraries like Lombok**
- Lombok can reduce boilerplate code using annotations like `@Data`.

```java
import lombok.Data;

@Data
public class UserDto {
    private int id;
    private String name;
    private String email;
}
```

---

### 3. **Record Class (Java 14+)**
- Java `record` is the closest equivalent to Kotlin’s `data class`.

```java
public record UserDto(int id, String name, String email) {}
```

#### Usage:
```java
UserDto user = new UserDto(1, "Alice", "alice@example.com");
System.out.println(user.name()); // Alice
System.out.println(user);        // UserDto[id=1, name=Alice, email=alice@example.com]
```

---

### 4. **Immutable DTO**
- A manual way to create immutable DTOs for older Java versions.

```java
public class UserDto {
    private final int id;
    private final String name;
    private final String email;

    public UserDto(int id, String name, String email) {
        this.id = id;
        this.name = name;
        this.email = email;
    }

    public int getId() { return id; }
    public String getName() { return name; }
    public String getEmail() { return email; }
}
```

---

## **Comparison: Kotlin vs Java**

| **Feature**            | **Kotlin**                                | **Java**                                   |
|-------------------------|-------------------------------------------|-------------------------------------------|
| **Conciseness**         | `data class` minimizes boilerplate code.  | Requires more boilerplate (unless using Lombok or records). |
| **Immutability**        | Easy with `val` properties.               | Use `final` fields and constructor.       |
| **Getters/Setters**     | Implicit for `val`/`var`.                 | Explicit or auto-generated (Lombok/IDE).  |
| **Constructors**        | Primary and secondary constructors.       | Constructor chaining is verbose.          |
| **Equals/HashCode**     | Auto-generated in `data class`.           | Manual implementation or `@Data`/record.  |

### Recommendation:
- Use **Kotlin's `data class`** or **Java's `record`** for DTOs whenever possible, as they are concise, immutable, and readable.


---


### Builder Pattern in Kotlin and Java

The **Builder Pattern** is used to construct complex objects step by step, often providing a fluent interface for better readability. Below are implementations of the Builder Pattern in both **Kotlin** and **Java**.

---

## **Builder Pattern in Kotlin**

Kotlin offers several ways to implement the Builder Pattern, thanks to its features like **data classes**, **DSLs**, and **default parameters**.

### 1. **Manual Builder Class**
```kotlin
class User private constructor(
    val id: Int,
    val name: String,
    val email: String,
    val age: Int
) {
    data class Builder(
        var id: Int = 0,
        var name: String = "",
        var email: String = "",
        var age: Int = 0
    ) {
        fun id(id: Int) = apply { this.id = id }
        fun name(name: String) = apply { this.name = name }
        fun email(email: String) = apply { this.email = email }
        fun age(age: Int) = apply { this.age = age }
        fun build() = User(id, name, email, age)
    }
}
```

#### Usage:
```kotlin
val user = User.Builder()
    .id(1)
    .name("Alice")
    .email("alice@example.com")
    .age(25)
    .build()

println(user) // User(id=1, name=Alice, email=alice@example.com, age=25)
```

---

### 2. **Using Kotlin DSL**
Kotlin DSL allows a more idiomatic approach to the Builder Pattern.

```kotlin
class User(
    val id: Int,
    val name: String,
    val email: String,
    val age: Int
)

class UserBuilder {
    var id: Int = 0
    var name: String = ""
    var email: String = ""
    var age: Int = 0

    fun build() = User(id, name, email, age)
}

fun user(block: UserBuilder.() -> Unit): User {
    val builder = UserBuilder()
    builder.block()
    return builder.build()
}
```

#### Usage:
```kotlin
val user = user {
    id = 1
    name = "Alice"
    email = "alice@example.com"
    age = 25
}

println(user) // User(id=1, name=Alice, email=alice@example.com, age=25)
```

---

### 3. **Simplified Builder with Default Parameters**
In Kotlin, you can avoid the Builder Pattern entirely by using default arguments in the constructor.

```kotlin
data class User(
    val id: Int = 0,
    val name: String = "",
    val email: String = "",
    val age: Int = 0
)
```

#### Usage:
```kotlin
val user = User(id = 1, name = "Alice", email = "alice@example.com", age = 25)
println(user) // User(id=1, name=Alice, email=alice@example.com, age=25)
```

---

## **Builder Pattern in Java**

In Java, the Builder Pattern typically requires more boilerplate code compared to Kotlin.

### 1. **Manual Builder Class**
```java
public class User {
    private final int id;
    private final String name;
    private final String email;
    private final int age;

    private User(Builder builder) {
        this.id = builder.id;
        this.name = builder.name;
        this.email = builder.email;
        this.age = builder.age;
    }

    public static class Builder {
        private int id;
        private String name;
        private String email;
        private int age;

        public Builder id(int id) {
            this.id = id;
            return this;
        }

        public Builder name(String name) {
            this.name = name;
            return this;
        }

        public Builder email(String email) {
            this.email = email;
            return this;
        }

        public Builder age(int age) {
            this.age = age;
            return this;
        }

        public User build() {
            return new User(this);
        }
    }

    @Override
    public String toString() {
        return "User{id=" + id + ", name='" + name + "', email='" + email + "', age=" + age + "}";
    }
}
```

#### Usage:
```java
public class Main {
    public static void main(String[] args) {
        User user = new User.Builder()
            .id(1)
            .name("Alice")
            .email("alice@example.com")
            .age(25)
            .build();

        System.out.println(user); // User{id=1, name='Alice', email='alice@example.com', age=25}
    }
}
```

---

### 2. **Using Lombok's `@Builder`**
Lombok simplifies the Builder Pattern significantly with its `@Builder` annotation.

```java
import lombok.Builder;
import lombok.ToString;

@Builder
@ToString
public class User {
    private int id;
    private String name;
    private String email;
    private int age;
}
```

#### Usage:
```java
public class Main {
    public static void main(String[] args) {
        User user = User.builder()
            .id(1)
            .name("Alice")
            .email("alice@example.com")
            .age(25)
            .build();

        System.out.println(user); // User(id=1, name=Alice, email=alice@example.com, age=25)
    }
}
```

---

### **Comparison**

| Feature                  | **Kotlin**                                    | **Java**                                      |
|--------------------------|-----------------------------------------------|-----------------------------------------------|
| **Boilerplate Code**     | Minimal, especially with `data class` or DSL | More verbose unless using Lombok or records  |
| **Fluent Interface**     | Supported with custom or DSL builders         | Supported with manual builders or Lombok     |
| **Default Parameters**   | Native support (avoids the need for builders)| Not available; requires overloaded constructors |
| **DSL-like Syntax**      | Supported                                     | Not natively supported                       |

---

### Conclusion
- Use **Kotlin's DSL or `data class`** for simplicity and readability.
- In **Java**, Lombok's `@Builder` or a manually implemented builder is common.


---

Here’s a complete Kotlin example with multiple DTOs implemented in various ways to demonstrate different techniques.

---

### **1. Using `data class`**
A simple and concise way to create immutable DTOs.

```kotlin
data class UserDto(
    val id: Int,
    val name: String,
    val email: String
)

data class AddressDto(
    val street: String,
    val city: String,
    val zipCode: String
)
```

#### Usage:
```kotlin
fun main() {
    val user = UserDto(1, "Alice", "alice@example.com")
    val address = AddressDto("123 Main St", "Wonderland", "12345")

    println(user) // UserDto(id=1, name=Alice, email=alice@example.com)
    println(address) // AddressDto(street=123 Main St, city=Wonderland, zipCode=12345)
}
```

---

### **2. Custom Getters/Setters**
Adding validation or derived properties.

```kotlin
class OrderDto(
    val orderId: Int,
    val userId: Int,
    var totalPrice: Double
) {
    var discount: Double = 0.0
        set(value) {
            field = if (value < 0 || value > 100) {
                throw IllegalArgumentException("Discount must be between 0 and 100")
            } else value
        }

    val finalPrice: Double
        get() = totalPrice - (totalPrice * (discount / 100))
}
```

#### Usage:
```kotlin
fun main() {
    val order = OrderDto(101, 1, 200.0)
    order.discount = 10.0

    println(order.finalPrice) // Output: 180.0
}
```

---

### **3. Builder Pattern**
For building DTOs step-by-step.

```kotlin
class ProductDto private constructor(
    val id: Int,
    val name: String,
    val price: Double
) {
    data class Builder(
        var id: Int = 0,
        var name: String = "",
        var price: Double = 0.0
    ) {
        fun id(id: Int) = apply { this.id = id }
        fun name(name: String) = apply { this.name = name }
        fun price(price: Double) = apply { this.price = price }
        fun build() = ProductDto(id, name, price)
    }
}
```

#### Usage:
```kotlin
fun main() {
    val product = ProductDto.Builder()
        .id(1)
        .name("Laptop")
        .price(1500.0)
        .build()

    println(product) // ProductDto(id=1, name=Laptop, price=1500.0)
}
```

---

### **4. Kotlin DSL**
Using a Domain-Specific Language (DSL) for building DTOs.

```kotlin
class InvoiceDto(
    val id: Int,
    val customerName: String,
    val items: List<String>
)

class InvoiceBuilder {
    var id: Int = 0
    var customerName: String = ""
    private val items = mutableListOf<String>()

    fun addItem(item: String) = apply { items.add(item) }
    fun build() = InvoiceDto(id, customerName, items)
}

fun invoice(block: InvoiceBuilder.() -> Unit): InvoiceDto {
    val builder = InvoiceBuilder()
    builder.block()
    return builder.build()
}
```

#### Usage:
```kotlin
fun main() {
    val invoice = invoice {
        id = 1001
        customerName = "Alice"
        addItem("Laptop")
        addItem("Mouse")
    }

    println(invoice) // InvoiceDto(id=1001, customerName=Alice, items=[Laptop, Mouse])
}
```

---

### **5. Top-Level Properties**
Simplifying DTOs by using Kotlin's top-level functions and properties.

```kotlin
data class CategoryDto(
    val id: Int,
    val name: String
)

fun defaultCategory() = CategoryDto(0, "Uncategorized")
```

#### Usage:
```kotlin
fun main() {
    val category = defaultCategory()
    println(category) // CategoryDto(id=0, name=Uncategorized)
}
```

---

### **6. Nested DTOs**
DTOs within other DTOs for hierarchical data.

```kotlin
data class CustomerDto(
    val id: Int,
    val name: String,
    val address: AddressDto
)
```

#### Usage:
```kotlin
fun main() {
    val address = AddressDto("456 Elm St", "Metropolis", "67890")
    val customer = CustomerDto(1, "Bob", address)

    println(customer)
    // CustomerDto(id=1, name=Bob, address=AddressDto(street=456 Elm St, city=Metropolis, zipCode=67890))
}
```

---

### **7. Mutable DTO with Default Parameters**
Useful for dynamic data.

```kotlin
class CartDto(
    var userId: Int = 0,
    var items: MutableList<String> = mutableListOf(),
    var total: Double = 0.0
) {
    fun addItem(item: String, price: Double) {
        items.add(item)
        total += price
    }
}
```

#### Usage:
```kotlin
fun main() {
    val cart = CartDto(userId = 1)
    cart.addItem("Book", 10.0)
    cart.addItem("Pen", 2.0)

    println(cart) // CartDto(userId=1, items=[Book, Pen], total=12.0)
}
```

---

### Summary of Techniques

| **Method**             | **Usage**                                                                                   |
|-------------------------|---------------------------------------------------------------------------------------------|
| **`data class`**        | Immutable DTOs with minimal code for most common use cases.                                 |
| **Custom Getters/Setters** | Add validation or computed properties.                                                     |
| **Builder Pattern**     | Step-by-step creation, especially for complex objects.                                      |
| **Kotlin DSL**          | Fluent, readable syntax for building DTOs in a structured manner.                          |
| **Top-Level Properties**| Quick setup for default or utility DTOs.                                                   |
| **Nested DTOs**         | Represent hierarchical relationships between data objects.                                  |
| **Mutable DTOs**        | For dynamic and changeable data structures with default values.                             | 

These examples demonstrate a wide range of approaches to creating and using DTOs in Kotlin, catering to both simple and complex scenarios.

---

### 1. **Understanding `Unit` and `block: InvoiceBuilder.() -> Unit`**

#### **What is `Unit` in Kotlin?**
- `Unit` is Kotlin's equivalent of `void` in Java. 
- It represents a function that doesn't return any meaningful value.
- Unlike `void` in Java, `Unit` is a real type in Kotlin, so it can be used as a type argument or assigned to a variable.

Example:
```kotlin
fun printMessage(message: String): Unit {
    println(message)
}
```

Since `Unit` is implied, you can omit it:
```kotlin
fun printMessage(message: String) {
    println(message)
}
```

---

#### **What is `block: InvoiceBuilder.() -> Unit`?**
- **Syntax Breakdown**:
  - `InvoiceBuilder.() -> Unit`:
    - Declares a function type where the receiver is an instance of `InvoiceBuilder`.
    - The function does not return a value (`Unit`).
  - `block: InvoiceBuilder.() -> Unit`:
    - Declares a parameter `block` of the function type `InvoiceBuilder.() -> Unit`.

- **Receiver Functions (`InvoiceBuilder.()`)**:
  - Kotlin allows **receiver functions**, meaning the function is called on an object (`InvoiceBuilder` in this case).
  - Inside the block, you can access the `InvoiceBuilder` instance without explicitly referencing it.

- **Usage in DSL**:
  - This syntax is used for creating DSLs (Domain-Specific Languages), allowing elegant and concise APIs.

Example:
```kotlin
fun invoice(block: InvoiceBuilder.() -> Unit): InvoiceDto {
    val builder = InvoiceBuilder()
    builder.block() // Executes the block on the builder
    return builder.build()
}

class InvoiceBuilder {
    var id: Int = 0
    var customerName: String = ""
    fun build(): InvoiceDto = InvoiceDto(id, customerName)
}
```

#### Example Usage:
```kotlin
val invoice = invoice {
    id = 1001 // Access `InvoiceBuilder` properties directly
    customerName = "Alice"
}
```

---

### 2. **Understanding `var discount: Double = 0.0` with Custom Setter**

#### **Syntax Breakdown:**
```kotlin
var discount: Double = 0.0
    set(value) {
        field = if (value < 0 || value > 100) {
            throw IllegalArgumentException("Discount must be between 0 and 100")
        } else value
    }
```

- **`var discount: Double = 0.0`**:
  - Declares a mutable property `discount` of type `Double`, initialized to `0.0`.

- **Custom Setter (`set(value)`)**:
  - Defines a custom setter for the property `discount`.
  - **`value`**:
    - Represents the value being assigned to the property.
    - Example: `discount = 50.0` will pass `50.0` as `value` to the setter.

- **`field`**:
  - A special keyword in Kotlin that refers to the **backing field** of the property.
  - The backing field stores the actual value of the property.
  - It is used inside a custom setter or getter to avoid infinite recursion (e.g., calling `discount = value` would loop indefinitely without `field`).

- **Validation Logic**:
  - Before assigning the value to the backing field, the setter checks if the value is within the range [0, 100].
  - If the value is invalid, an exception is thrown.

---

#### **How It Works:**
```kotlin
fun main() {
    val order = OrderDto(101, 1, 200.0)
    order.discount = 50.0 // Setter is called; field is set to 50.0
    println(order.discount) // Output: 50.0

    order.discount = 150.0 // Throws IllegalArgumentException
}
```

---

### **Key Differences and Use Cases**

#### `block: InvoiceBuilder.() -> Unit`:
- Used for DSLs or APIs where you want to configure an object concisely.
- Allows scoped access to the `InvoiceBuilder` instance.

#### `var discount: Double` with Custom Setter:
- Used to add logic during property assignment (e.g., validation, transformation).
- Ensures the property holds only valid or properly formatted data.

