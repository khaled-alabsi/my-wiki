### **1. What is Kotlin Multiplatform?**

Kotlin Multiplatform (KMP) allows you to share code across multiple platforms, such as:
- **Android**
- **iOS**
- **Desktop** (Windows, macOS, Linux)
- **Web** (JavaScript)
- **Backend** (JVM-based servers)

With KMP, you write platform-independent logic in a shared module and platform-specific code in separate modules.

---

### **2. Structure of a KMP Project**

A typical Kotlin Multiplatform project consists of:
1. **Shared Code**: The common module where you write platform-agnostic logic.
2. **Platform-Specific Code**: Modules for platform-specific implementations (e.g., Android, iOS).

**Project Structure:**
```
root/
├── common/
│   ├── src/commonMain/     // Shared code
│   ├── src/commonTest/     // Shared tests
├── androidApp/
│   ├── src/main/           // Android-specific code
├── iosApp/
│   ├── src/iosMain/        // iOS-specific code
```

---

### **3. Setting Up a KMP Project**

#### **3.1 Gradle Configuration**

**Root `build.gradle.kts`**:
```kotlin
plugins {
    kotlin("multiplatform") version "1.8.0"
    id("com.android.application") version "7.3.0"
}

kotlin {
    android()                     // Target Android
    iosX64()                      // Target iOS (Simulator)
    iosArm64()                    // Target iOS (Devices)

    sourceSets {
        val commonMain by getting {
            dependencies {
                implementation(kotlin("stdlib"))
            }
        }
        val androidMain by getting
        val iosMain by creating {
            dependsOn(commonMain)
        }
    }
}
```

**Explanation:**
- **`commonMain`**: Shared code for all platforms.
- **`androidMain`** and **`iosMain`**: Platform-specific code.

---

#### **3.2 Adding Android and iOS Modules**

**Android Module (`androidApp/build.gradle.kts`):**
```kotlin
plugins {
    id("com.android.application")
    kotlin("android")
}

android {
    compileSdk = 33
    defaultConfig {
        applicationId = "com.example.kmp"
        minSdk = 21
        targetSdk = 33
    }
}

dependencies {
    implementation(project(":common"))
}
```

**iOS Setup:**
For iOS, use **Xcode** to configure your project and link the KMP framework.

---

### **4. Writing Shared Code**

Shared code is placed in `commonMain`. This code is platform-agnostic and can include:
- Business logic
- API calls
- Data models
- Shared utilities

**Example: Shared Code (`common/src/commonMain/kotlin/Utils.kt`):**
```kotlin
expect fun getPlatformName(): String

fun greet(): String {
    return "Hello from ${getPlatformName()}"
}
```

---

### **5. Writing Platform-Specific Code**

Platform-specific implementations are provided in the respective source sets (`androidMain`, `iosMain`).

**Example: Platform-Specific Implementation**

**Android (`common/src/androidMain/kotlin/Platform.kt`):**
```kotlin
actual fun getPlatformName(): String {
    return "Android"
}
```

**iOS (`common/src/iosMain/kotlin/Platform.kt`):**
```kotlin
import platform.UIKit.UIDevice

actual fun getPlatformName(): String {
    return UIDevice.currentDevice.systemName() + " " + UIDevice.currentDevice.systemVersion
}
```

---

### **6. Testing in KMP**

Testing can also be shared or platform-specific.

**Shared Test (`common/src/commonTest/kotlin/UtilsTest.kt`):**
```kotlin
import kotlin.test.Test
import kotlin.test.assertEquals

class UtilsTest {
    @Test
    fun testGreet() {
        assertEquals("Hello from Android", greet()) // Run this on Android
    }
}
```

---

### **7. Working with APIs**

#### **7.1 HTTP Requests**
Use `Ktor` for making HTTP requests across platforms.

**Add Dependency:**
```kotlin
dependencies {
    implementation("io.ktor:ktor-client-core:2.2.0")
    implementation("io.ktor:ktor-client-json:2.2.0")
    implementation("io.ktor:ktor-client-logging:2.2.0")
    implementation("io.ktor:ktor-client-android:2.2.0") // For Android
    implementation("io.ktor:ktor-client-ios:2.2.0")     // For iOS
}
```

**Example:**
```kotlin
import io.ktor.client.*
import io.ktor.client.request.*

val client = HttpClient()

suspend fun fetchData(url: String): String {
    return client.get(url)
}
```

---

#### **7.2 Serialization**
Use `Kotlinx Serialization` for parsing JSON.

**Add Dependency:**
```kotlin
dependencies {
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.5.0")
}
```

**Example:**
```kotlin
import kotlinx.serialization.*
import kotlinx.serialization.json.*

@Serializable
data class User(val id: Int, val name: String)

val json = Json.decodeFromString<User>("""{"id":1,"name":"John"}""")
```

---

### **8. Managing Database**

#### **8.1 SQLDelight**
Use `SQLDelight` for a multiplatform database.

**Add Dependency:**
```kotlin
dependencies {
    implementation("com.squareup.sqldelight:runtime:1.5.5")
    implementation("com.squareup.sqldelight:android-driver:1.5.5") // Android
    implementation("com.squareup.sqldelight:native-driver:1.5.5")  // iOS
}
```

**Example:**
```kotlin
val database = SqlDriver("my_database")
val userQueries = database.createUserQueries()

userQueries.insertUser(1, "John Doe")
val users = userQueries.selectAll().executeAsList()
```

---

### **9. Sharing UI Logic**

For shared UI logic, you can use **Jetpack Compose** for Android and **SwiftUI** for iOS with a shared ViewModel.

**Shared ViewModel (`common/src/commonMain/kotlin/ViewModel.kt`):**
```kotlin
class ViewModel {
    private val _state = MutableStateFlow("Initial State")
    val state: StateFlow<String> = _state

    fun updateState(newState: String) {
        _state.value = newState
    }
}
```

---

### **10. Real-World Use Cases**

#### **Case 1: Sharing Business Logic**
Use shared code for business logic like authentication, data processing, or validation.

**Example: Shared Validation Logic**
```kotlin
fun validateEmail(email: String): Boolean {
    return email.contains("@") && email.endsWith(".com")
}
```

#### **Case 2: Shared Networking**
API calls in shared modules to fetch data for Android and iOS.

#### **Case 3: Cross-Platform Libraries**
- **Ktor**: Networking
- **SQLDelight**: Database
- **Kotlinx Serialization**: JSON parsing

---

### **11. Key Benefits**

1. **Code Reuse**:
   - Write shared code once and use it across Android, iOS, and other platforms.

2. **Improved Productivity**:
   - Focus on platform-specific UI while sharing core logic.

3. **Open Ecosystem**:
   - Use existing libraries like `Ktor` and `SQLDelight` to speed up development.

---

### **12. Challenges**

1. **Platform-Specific Code**:
   - Not all libraries are supported on every platform (e.g., some Android libraries won’t work on iOS).

2. **Tooling**:
   - iOS requires Xcode setup, and Android requires Android Studio.

3. **Debugging**:
   - Debugging shared code across platforms can be complex.

---

### **13. Future of KMP**

- Kotlin Multiplatform is evolving with better tooling and library support.
- JetBrains is actively enhancing the ecosystem with features like **Compose Multiplatform** for shared UI across Android, iOS, and Desktop.

---

Here’s a **comprehensive explanation of Kotlin Multiplatform (KMP)**, including advanced topics like **Compose Multiplatform**, **Testing**, and **Debugging**.

---

### **1. Compose Multiplatform**

Compose Multiplatform is Kotlin's declarative UI framework for sharing UI across platforms. It allows you to write shared UI code for Android, iOS, Desktop, and Web.

---

#### **1.1 Setting Up Compose Multiplatform**

**Dependencies (in `build.gradle.kts`):**
```kotlin
plugins {
    kotlin("multiplatform")
    id("org.jetbrains.compose") version "1.5.0"
}

kotlin {
    jvm() // For desktop
    android() // For Android
    iosX64() // For iOS

    sourceSets {
        val commonMain by getting {
            dependencies {
                implementation(compose.runtime)
                implementation(compose.foundation)
                implementation(compose.material)
            }
        }
        val androidMain by getting
        val iosMain by getting
    }
}
```

---

#### **1.2 Shared UI Example**

**Shared Code (`common/src/commonMain/kotlin/App.kt`):**
```kotlin
import androidx.compose.runtime.Composable
import androidx.compose.material.Text

@Composable
fun App() {
    Text("Hello, Compose Multiplatform!")
}
```

**Android (`androidApp/src/main/java/com/example/MainActivity.kt`):**
```kotlin
import android.os.Bundle
import androidx.activity.compose.setContent
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            App()
        }
    }
}
```

**iOS (Swift UIBridge):**
```swift
import UIKit
import SwiftUI
import shared

@main
struct iOSApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}

struct ContentView: UIViewControllerRepresentable {
    func makeUIViewController(context: Context) -> UIViewController {
        AppKt.AppViewController() // Connects shared Compose UI
    }

    func updateUIViewController(_ uiViewController: UIViewController, context: Context) {}
}
```

---

### **2. Advanced Testing in KMP**

Testing in Kotlin Multiplatform includes unit tests, integration tests, and UI tests.

---

#### **2.1 Shared Unit Tests**

Write tests in `commonTest` to verify shared logic.

**Example: Testing Shared Logic**
```kotlin
import kotlin.test.Test
import kotlin.test.assertTrue

class ValidatorTest {
    @Test
    fun testEmailValidation() {
        assertTrue(validateEmail("user@example.com"))
        assertTrue(!validateEmail("invalid-email"))
    }
}
```

Run tests with:
- **Android**: Gradle tasks (`testDebugUnitTest`).
- **iOS**: Xcode test runners.

---

#### **2.2 Platform-Specific Tests**

Use `androidTest` or `iosTest` for platform-specific logic.

**Android Example:**
```kotlin
@Test
fun testAndroidSpecificFeature() {
    // Android-specific validation
}
```

**iOS Example:**
```kotlin
@Test
fun testIosSpecificFeature() {
    // iOS-specific validation
}
```

---

#### **2.3 Integration Tests with Ktor**

**Example: Mocking Ktor Client**
```kotlin
import io.ktor.client.*
import io.ktor.client.engine.mock.*
import io.ktor.client.request.*
import io.ktor.http.*
import kotlin.test.Test
import kotlin.test.assertEquals

@Test
fun testKtorClient() = runBlocking {
    val client = HttpClient(MockEngine) {
        engine {
            addHandler { request ->
                respond(
                    content = """{"message": "Success"}""",
                    status = HttpStatusCode.OK,
                    headers = headersOf("Content-Type" to listOf("application/json"))
                )
            }
        }
    }

    val response = client.get<String>("http://example.com")
    assertEquals("""{"message": "Success"}""", response)
}
```

---

#### **2.4 UI Testing for Compose Multiplatform**

Use Compose Testing for shared UI components.

**Shared UI Test Example:**
```kotlin
import androidx.compose.ui.test.junit4.createComposeRule
import org.junit.Rule
import org.junit.Test

class AppTest {
    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun testAppUI() {
        composeTestRule.setContent {
            App()
        }
        composeTestRule.onNodeWithText("Hello, Compose Multiplatform!").assertExists()
    }
}
```

---

### **3. Debugging KMP Projects**

Debugging Kotlin Multiplatform requires configuring tools for each platform.

---

#### **3.1 Debugging Shared Code**

Shared code is debuggable via **breakpoints** in the shared module (`commonMain`) using IntelliJ IDEA or Android Studio.

---

#### **3.2 Debugging Android**

Debug the Android app using Android Studio’s emulator or a physical device.

- Set breakpoints in `androidMain`.
- Use Android Studio’s **logcat** for runtime logs.

---

#### **3.3 Debugging iOS**

Debug the iOS app using Xcode:
- Attach the debugger to the running app.
- Use `println` or Xcode logs for debugging shared Kotlin code.

---

### **4. Performance Optimization in KMP**

---

#### **4.1 Minimize Platform-Specific Code**
Keep most logic in `commonMain` to avoid code duplication.

---

#### **4.2 Optimize Serialization**
- Use `kotlinx.serialization` for JSON parsing instead of manually handling data.
- Avoid creating unnecessary data transformations.

---

#### **4.3 Reduce Startup Time**
- Use lazy initialization for components (e.g., database, network clients).
- Keep shared modules lightweight.

---

#### **4.4 Use Multithreading for Performance**
- Use `Dispatchers.Default` for CPU-intensive tasks.
- Use `Dispatchers.IO` for I/O operations like file or network access.

---

### **5. Real-World Use Cases**

---

#### **Case 1: Shared Networking Layer**

**Example:**
```kotlin
import io.ktor.client.*
import io.ktor.client.request.*

class ApiClient {
    private val client = HttpClient()

    suspend fun fetchData(): String {
        return client.get("https://example.com/data")
    }
}
```

---

#### **Case 2: Shared Validation Logic**

**Example:**
```kotlin
fun validateEmail(email: String): Boolean {
    return email.contains("@") && email.endsWith(".com")
}
```

---

#### **Case 3: Cross-Platform Authentication**
Use shared logic for authentication while keeping platform-specific UI for login screens.

---

### Comprehensive Guide: Publishing KMP Libraries and Integrating Third-Party Tools in Kotlin Multiplatform

---

### **1. Publishing Kotlin Multiplatform Libraries**

Publishing a KMP library involves creating a reusable library that can be consumed by multiple platforms. This includes setting up Gradle metadata, adding dependencies, and publishing to a repository.

---

#### **1.1 Project Structure for a KMP Library**

A typical KMP library project has the following structure:

```
root/
├── build.gradle.kts
├── settings.gradle.kts
├── src/
│   ├── commonMain/
│   ├── androidMain/
│   ├── iosMain/
│   ├── jsMain/
```

---

#### **1.2 Gradle Configuration for Publishing**

**`build.gradle.kts`:**
```kotlin
plugins {
    kotlin("multiplatform") version "1.8.0"
    id("maven-publish")
}

kotlin {
    jvm()  // JVM Target
    android()  // Android Target
    iosArm64()  // iOS Device
    iosX64()  // iOS Simulator
    js(IR) { browser() }  // JavaScript Target

    sourceSets {
        val commonMain by getting {
            dependencies {
                implementation(kotlin("stdlib"))
            }
        }
        val androidMain by getting
        val iosMain by getting
        val jsMain by getting
    }
}

publishing {
    publications {
        create<MavenPublication>("multiplatform") {
            from(components["kotlin"])
            groupId = "com.example"
            artifactId = "shared-library"
            version = "1.0.0"
        }
    }

    repositories {
        maven {
            url = uri("https://your-repository-url")
            credentials {
                username = "your-username"
                password = "your-password"
            }
        }
    }
}
```

---

#### **1.3 Steps to Publish**

1. **Build the Library**: Run `./gradlew build` to ensure everything compiles.
2. **Publish the Library**:
   ```bash
   ./gradlew publish
   ```
3. **Consume the Library**:
   Add the library dependency to your project:
   ```kotlin
   dependencies {
       implementation("com.example:shared-library:1.0.0")
   }
   ```

---

### **2. Integrating Third-Party Tools**

Many third-party libraries support Kotlin Multiplatform or have alternatives for each platform.

---

#### **2.1 Networking with Ktor**

**Setup:**
```kotlin
dependencies {
    implementation("io.ktor:ktor-client-core:2.2.0")
    implementation("io.ktor:ktor-client-json:2.2.0")
    implementation("io.ktor:ktor-client-logging:2.2.0")
    implementation("io.ktor:ktor-client-android:2.2.0") // Android
    implementation("io.ktor:ktor-client-ios:2.2.0")     // iOS
}
```

**Example:**
```kotlin
import io.ktor.client.*
import io.ktor.client.features.logging.*
import io.ktor.client.request.*

val client = HttpClient {
    install(Logging) {
        level = LogLevel.INFO
    }
}

suspend fun fetchData(): String {
    return client.get("https://api.example.com/data")
}
```

---

#### **2.2 JSON Parsing with Kotlinx Serialization**

**Setup:**
```kotlin
dependencies {
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.5.0")
}
```

**Example:**
```kotlin
import kotlinx.serialization.*
import kotlinx.serialization.json.*

@Serializable
data class User(val id: Int, val name: String)

val json = """{"id":1,"name":"John"}"""
val user = Json.decodeFromString<User>(json)
println(user) // Output: User(id=1, name=John)
```

---

#### **2.3 Dependency Injection with Koin**

**Setup:**
```kotlin
dependencies {
    implementation("io.insert-koin:koin-core:3.4.0")
}
```

**Example:**
```kotlin
import org.koin.core.context.startKoin
import org.koin.dsl.module

val appModule = module {
    single { ApiClient() }
}

class ApiClient {
    fun fetch() = "Fetched Data"
}

fun main() {
    startKoin {
        modules(appModule)
    }

    val apiClient: ApiClient = get()
    println(apiClient.fetch()) // Output: Fetched Data
}
```

---

#### **2.4 Database with SQLDelight**

**Setup:**
```kotlin
dependencies {
    implementation("com.squareup.sqldelight:runtime:1.5.5")
    implementation("com.squareup.sqldelight:android-driver:1.5.5") // Android
    implementation("com.squareup.sqldelight:native-driver:1.5.5")  // iOS
}
```

**Example:**
```kotlin
import com.squareup.sqldelight.Transacter
import com.squareup.sqldelight.db.SqlDriver

fun createDatabase(driver: SqlDriver): Database {
    return Database(driver)
}

val driver: SqlDriver = ... // Platform-specific driver
val database = createDatabase(driver)

database.userQueries.insertUser(1, "John Doe")
val users = database.userQueries.selectAll().executeAsList()
```

---

### **3. Debugging and Optimization**

---

#### **3.1 Debugging Shared Code**

- **Set Breakpoints**: Place breakpoints in `commonMain`.
- **Run Tests**: Use IntelliJ IDEA's test runner to debug shared tests.
- **Use Logs**: Add `println` or logging frameworks like `Napier` for detailed logs.

---

#### **3.2 Debugging Platform-Specific Code**

- **Android**: Use Android Studio for debugging with Logcat and breakpoints.
- **iOS**: Use Xcode for Swift bridging and breakpoints in iOS-specific code.

---

#### **3.3 Optimize Build Times**

1. **Enable Build Caching**:
   Add this to your `gradle.properties`:
   ```properties
   org.gradle.caching=true
   ```
2. **Parallel Execution**:
   ```properties
   org.gradle.parallel=true
   ```
3. **Incremental Compilation**:
   Ensure `kotlin.incremental=true` is enabled in `gradle.properties`.

---

#### **3.4 Optimize Performance in Shared Code**

- Use `StateFlow` and `SharedFlow` for efficient state management.
- Avoid blocking threads; always use coroutines with appropriate `Dispatchers`.

---

### **4. Real-World Applications of KMP**

---

#### **4.1 Shared SDKs**
- Companies build shared SDKs for internal use across mobile platforms.
- Example: Payment SDKs shared between Android and iOS.

#### **4.2 Cross-Platform Apps**
- Apps like Slack, Netflix, and Airbnb use shared logic to reduce development time.

#### **4.3 Internal Tools**
- Internal dashboards or tools that require shared backend logic for multiple platforms.

---

Here’s a comprehensive guide to **building a complete Kotlin Multiplatform project**, including **real-world implementation scenarios** and **debugging techniques**.

---

### **1. Building a Complete Kotlin Multiplatform Project**

We'll build a KMP project with shared business logic, platform-specific implementations, and a simple UI for Android and iOS.

---

#### **1.1 Project Setup**

**Step 1: Create a New KMP Project**

Use IntelliJ IDEA or Android Studio to create a new Kotlin Multiplatform project.

---

**Step 2: Configure the Gradle Files**

**Root `build.gradle.kts`:**
```kotlin
plugins {
    kotlin("multiplatform") version "1.8.0"
    id("com.android.application")
    id("org.jetbrains.compose") version "1.5.0" // For shared UI
}

kotlin {
    android()
    iosX64()
    iosArm64()
    iosSimulatorArm64()

    sourceSets {
        val commonMain by getting {
            dependencies {
                implementation(compose.runtime)
                implementation(compose.foundation)
                implementation(compose.material)
                implementation("io.ktor:ktor-client-core:2.2.0")
                implementation("io.ktor:ktor-client-serialization:2.2.0")
                implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.5.0")
            }
        }
        val androidMain by getting
        val iosMain by creating {
            dependsOn(commonMain)
        }
    }
}

android {
    namespace = "com.example.kmp"
    compileSdk = 33
    defaultConfig {
        minSdk = 21
        targetSdk = 33
    }
}
```

---

**Step 3: Shared Code**

Place shared code in the `commonMain` module.

---

#### **1.2 Writing Shared Logic**

**Networking with Ktor:**
```kotlin
import io.ktor.client.*
import io.ktor.client.request.*
import io.ktor.client.features.json.*
import io.ktor.client.features.logging.*

class ApiClient {
    private val client = HttpClient {
        install(JsonFeature) {
            serializer = kotlinx.serialization.json.Json {
                ignoreUnknownKeys = true
            }
        }
        install(Logging) {
            level = LogLevel.INFO
        }
    }

    suspend fun fetchMessage(): String {
        return client.get("https://example.com/message")
    }
}
```

---

**Shared ViewModel:**
```kotlin
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow

class SharedViewModel {
    private val _state = MutableStateFlow("Initial State")
    val state: StateFlow<String> = _state

    suspend fun updateState(newState: String) {
        _state.emit(newState)
    }
}
```

---

#### **1.3 Android-Specific Code**

**Main Activity (`androidApp/src/main/java/com/example/MainActivity.kt`):**
```kotlin
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.material.Text
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    private val viewModel = SharedViewModel()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            Text("Loading...")
        }

        lifecycleScope.launch {
            viewModel.state.collect { state ->
                setContent {
                    Text(state)
                }
            }
        }
    }
}
```

---

#### **1.4 iOS-Specific Code**

**Swift UI Integration (`iosApp/ContentView.swift`):**
```swift
import SwiftUI
import shared

struct ContentView: View {
    @ObservedObject var viewModel = ViewModelWrapper()

    var body: some View {
        Text(viewModel.state)
    }
}

class ViewModelWrapper: ObservableObject {
    private let viewModel = SharedViewModel()
    @Published var state: String = "Loading..."

    init() {
        viewModel.state.collect { newState in
            DispatchQueue.main.async {
                self.state = newState as! String
            }
        }
    }
}
```

---

### **2. Real-World Implementation Scenarios**

---

#### **2.1 Shared Validation Logic**

You can use shared logic for form validation across platforms.

**Shared Validation (`commonMain`):**
```kotlin
fun validateEmail(email: String): Boolean {
    return email.contains("@") && email.endsWith(".com")
}
```

**Android Integration:**
```kotlin
val isValid = validateEmail("user@example.com")
println("Is email valid? $isValid")
```

**iOS Integration:**
```swift
let isValid = CommonKt.validateEmail("user@example.com")
print("Is email valid? \(isValid)")
```

---

#### **2.2 Shared API Client**

Use shared networking logic for fetching data.

**Example:**
```kotlin
suspend fun fetchAndProcessData(apiClient: ApiClient): List<String> {
    val response = apiClient.fetchMessage()
    return response.split(",") // Processing shared logic
}
```

---

### **3. Debugging Techniques**

---

#### **3.1 Debugging Shared Code**

1. **Use IntelliJ IDEA**:
   - Set breakpoints in `commonMain`.
   - Run shared tests to verify logic.

2. **Use Logs**:
   Add logging to track shared code behavior.

**Example:**
```kotlin
println("Debugging shared code: Current state is $state")
```

---

#### **3.2 Debugging Android**

- Use Android Studio’s **Logcat** to view logs.
- Attach breakpoints to `androidMain`.

**Example:**
```kotlin
Log.d("MainActivity", "Fetching data...")
```

---

#### **3.3 Debugging iOS**

- Use Xcode to attach breakpoints to Swift UI code.
- Add logs in the Swift integration layer.

**Example:**
```swift
print("Debugging iOS integration...")
```

---

### **4. Best Practices for KMP**

---

#### **4.1 Keep Shared Code Clean**

Focus on keeping `commonMain` lightweight and platform-agnostic:
- Use expect/actual for platform-specific implementations.
- Keep shared modules limited to core logic and APIs.

---

#### **4.2 Dependency Injection**

Use libraries like **Koin** to inject dependencies in a multiplatform-friendly way.

**Shared Module:**
```kotlin
val appModule = module {
    single { ApiClient() }
}
```

**Initialize Koin in Android and iOS separately.**

---

#### **4.3 Modularize the Project**

Split large projects into smaller modules:
- Core logic (`core`).
- Networking (`networking`).
- Feature modules (`feature-auth`, `feature-payment`).

---### **Comprehensive Guide to Modularization in Kotlin Multiplatform**

Modularization in Kotlin Multiplatform (KMP) involves splitting a project into smaller, reusable modules. Each module has its own responsibilities, dependencies, and targets, making the project more maintainable and scalable.

---

### **1. Benefits of Modularization**

1. **Scalability**:
   - Large projects become easier to manage.
   - Teams can work on independent modules concurrently.

2. **Reusability**:
   - Shared modules can be reused across different projects.

3. **Faster Build Times**:
   - Gradle builds only the modules that have changed.

4. **Improved Code Separation**:
   - Promotes separation of concerns (e.g., UI, business logic, and APIs).

---

### **2. Modular Project Structure**

Here’s an example of a modularized KMP project:

```
root/
├── core/                 // Core logic (shared)
│   ├── build.gradle.kts
│   ├── src/
│       ├── commonMain/
│       ├── androidMain/
│       ├── iosMain/
├── feature-auth/         // Authentication feature
│   ├── build.gradle.kts
│   ├── src/
│       ├── commonMain/
│       ├── androidMain/
│       ├── iosMain/
├── feature-payment/      // Payment feature
│   ├── build.gradle.kts
│   ├── src/
│       ├── commonMain/
│       ├── androidMain/
│       ├── iosMain/
├── app-android/          // Android app
│   ├── build.gradle.kts
│   ├── src/
│       ├── main/
├── app-ios/              // iOS app
│   ├── build.gradle.kts
│   ├── src/
│       ├── iosMain/
```

---

### **3. Core Module**

The core module contains shared utilities, models, and API clients.

**`core/build.gradle.kts`:**
```kotlin
plugins {
    kotlin("multiplatform")
}

kotlin {
    android()
    iosX64()
    iosArm64()

    sourceSets {
        val commonMain by getting {
            dependencies {
                implementation("io.ktor:ktor-client-core:2.2.0")
                implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.5.0")
            }
        }
        val androidMain by getting
        val iosMain by getting
    }
}
```

**Core Code (`core/src/commonMain/kotlin/ApiClient.kt`):**
```kotlin
import io.ktor.client.*
import io.ktor.client.request.*

class ApiClient {
    private val client = HttpClient()

    suspend fun fetchData(): String {
        return client.get("https://example.com/data")
    }
}
```

---

### **4. Feature Module (Authentication)**

Each feature module contains logic and components specific to a feature, such as authentication.

**`feature-auth/build.gradle.kts`:**
```kotlin
plugins {
    kotlin("multiplatform")
}

kotlin {
    android()
    iosX64()
    iosArm64()

    sourceSets {
        val commonMain by getting {
            dependencies {
                implementation(project(":core")) // Depend on the core module
            }
        }
        val androidMain by getting
        val iosMain by getting
    }
}
```

**Feature Code (`feature-auth/src/commonMain/kotlin/AuthManager.kt`):**
```kotlin
class AuthManager(private val apiClient: ApiClient) {
    suspend fun login(username: String, password: String): Boolean {
        val response = apiClient.fetchData()
        return response.contains("success") // Dummy validation
    }
}
```

---

### **5. App Module (Android)**

The app module brings together the shared modules and adds platform-specific implementations.

**`app-android/build.gradle.kts`:**
```kotlin
plugins {
    id("com.android.application")
    kotlin("android")
}

android {
    compileSdk = 33
    defaultConfig {
        applicationId = "com.example.kmp"
        minSdk = 21
        targetSdk = 33
    }
}

dependencies {
    implementation(project(":core"))
    implementation(project(":feature-auth"))
}
```

**Android-Specific Code (`app-android/src/main/java/MainActivity.kt`):**
```kotlin
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.lifecycle.lifecycleScope
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    private val authManager = AuthManager(ApiClient())

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        lifecycleScope.launch {
            val isLoggedIn = authManager.login("user", "password")
            setContent {
                Text(if (isLoggedIn) "Login Successful" else "Login Failed")
            }
        }
    }
}
```

---

### **6. App Module (iOS)**

The iOS app integrates the shared logic and provides platform-specific UI.

**iOS App Integration (`app-ios/ContentView.swift`):**
```swift
import SwiftUI
import shared

struct ContentView: View {
    let authManager = AuthManager(apiClient: ApiClient())

    @State private var message = "Loading..."

    var body: some View {
        Text(message)
            .onAppear {
                Task {
                    let isLoggedIn = try? await authManager.login(username: "user", password: "password")
                    message = isLoggedIn == true ? "Login Successful" : "Login Failed"
                }
            }
    }
}
```

---

### **7. Dependency Management**

To manage dependencies effectively:
1. Use the **`core`** module for shared utilities.
2. Each feature module depends on `core` and has isolated dependencies.

**Example Dependency Configuration in a Feature Module:**
```kotlin
dependencies {
    implementation(project(":core"))
    implementation("io.ktor:ktor-client-core:2.2.0")
}
```

---

### **8. Tips for Modularization**

1. **Layered Architecture**:
   - Use layers like `core`, `data`, and `feature-*` to organize code.
   - Shared utilities go into `core`, while features are isolated in their own modules.

2. **Minimize Cross-Module Dependencies**:
   - Avoid dependencies between feature modules.
   - Use the `core` module as the intermediary.

3. **Gradle Configuration**:
   - Use a single `settings.gradle.kts` file to manage module inclusion.

**Example: `settings.gradle.kts`:**
```kotlin
rootProject.name = "KMPProject"

include(":core")
include(":feature-auth")
include(":feature-payment")
include(":app-android")
include(":app-ios")
```

4. **Reuse Code Across Features**:
   - Move reusable code to `core` to avoid duplication.

---

### **9. Real-World Use Case**

#### **Modular E-Commerce App**
**Modules:**
- **Core**: Shared utilities, API clients, and models.
- **Feature-Catalog**: Product catalog logic.
- **Feature-Cart**: Shopping cart logic.
- **Feature-Checkout**: Payment and order processing.
- **App-Android**: Android-specific UI and platform integrations.
- **App-iOS**: iOS-specific UI and platform integrations.

**Benefits**:
- **Feature Teams**: Teams can independently develop `catalog`, `cart`, and `checkout` features.
- **Reuse**: Shared logic like API clients and validation logic is reused across all features.

---

### **10. Advanced Debugging for Modularized Projects**

1. **Debugging Shared Modules**:
   - Add logging in shared modules to identify issues across platforms.
   - Use `println` or third-party logging tools like `Napier`.

2. **Debugging Feature Modules**:
   - Test feature modules in isolation using unit tests.
   - Use dependency injection to mock shared dependencies.

3. **Debugging Platform-Specific Issues**:
   - Use Android Studio’s Logcat and Xcode’s console for platform-specific debugging.
   - Ensure each platform module has independent logging and debugging utilities.

---

### **Advanced Testing Strategies for Modular Projects in Kotlin Multiplatform**

Testing modular projects in Kotlin Multiplatform (KMP) ensures the correctness of shared and platform-specific logic. This guide covers strategies for **unit tests**, **integration tests**, **UI tests**, and **end-to-end tests** across modularized KMP projects.

---

### **1. Unit Testing in Modular Projects**

Unit tests focus on isolated components (e.g., utility functions, business logic) within each module.

---

#### **1.1 Shared Module Tests**

Test shared logic in `commonTest`.

**Example: Testing Shared Validation Logic (`core/src/commonTest/kotlin/ValidationTest.kt`):**
```kotlin
import kotlin.test.Test
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class ValidationTest {
    @Test
    fun testValidEmail() {
        assertTrue(validateEmail("user@example.com"))
    }

    @Test
    fun testInvalidEmail() {
        assertFalse(validateEmail("invalid-email"))
    }
}
```

Run shared tests:
```bash
./gradlew :core:test
```

---

#### **1.2 Feature Module Tests**

Test feature-specific logic (e.g., `AuthManager` in `feature-auth`).

**Example: Testing `AuthManager` (`feature-auth/src/commonTest/kotlin/AuthManagerTest.kt`):**
```kotlin
import kotlin.test.Test
import kotlin.test.assertTrue

class AuthManagerTest {
    private val mockApiClient = ApiClient() // Mocked API Client

    @Test
    fun testLoginSuccess() = runTest {
        val authManager = AuthManager(mockApiClient)
        val result = authManager.login("user", "password")
        assertTrue(result)
    }
}
```

---

### **2. Integration Testing**

Integration tests verify how modules interact with each other (e.g., `feature-auth` depends on `core`).

---

#### **2.1 Mocking Dependencies**

Mock shared dependencies to isolate feature modules.

**Example: Mocking API Client with `MockEngine` (in `feature-auth`):**
```kotlin
import io.ktor.client.*
import io.ktor.client.engine.mock.*
import io.ktor.client.features.json.*
import io.ktor.http.*
import kotlin.test.*

class AuthManagerIntegrationTest {
    @Test
    fun testLoginWithMockApi() = runTest {
        val mockEngine = MockEngine { request ->
            respond(
                content = """{"message": "success"}""",
                status = HttpStatusCode.OK,
                headers = headersOf("Content-Type" to listOf("application/json"))
            )
        }

        val client = HttpClient(mockEngine) {
            install(JsonFeature) {
                serializer = kotlinx.serialization.json.Json { ignoreUnknownKeys = true }
            }
        }

        val authManager = AuthManager(client)
        val result = authManager.login("user", "password")
        assertTrue(result)
    }
}
```

---

#### **2.2 Testing Shared and Platform-Specific Interactions**

Platform-specific tests ensure that shared modules integrate correctly with platform APIs.

**Example: Android-Specific Test (`feature-auth/src/androidTest/kotlin/AndroidAuthTest.kt`):**
```kotlin
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class AndroidAuthTest {
    @Test
    fun testAndroidSpecificBehavior() {
        val authManager = AuthManager(ApiClient())
        val result = authManager.login("user", "password")
        assert(result)
    }
}
```

---

### **3. UI Testing**

---

#### **3.1 Compose Multiplatform Testing**

Test shared UI components with Compose Test APIs.

**Example: Testing Shared UI (`core/src/commonTest/kotlin/SharedUITest.kt`):**
```kotlin
import androidx.compose.ui.test.junit4.createComposeRule
import org.junit.Rule
import kotlin.test.Test

class SharedUITest {
    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun testSharedUIRendering() {
        composeTestRule.setContent {
            App() // Shared Composable
        }
        composeTestRule.onNodeWithText("Hello, Compose Multiplatform!").assertExists()
    }
}
```

---

#### **3.2 Android UI Tests**

Android-specific UI tests can be written using **Espresso** or **Compose Test APIs**.

**Example: Android UI Test:**
```kotlin
import androidx.compose.ui.test.junit4.createComposeRule
import org.junit.Rule
import org.junit.Test

class AndroidUITest {
    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun testAndroidUI() {
        composeTestRule.setContent {
            AndroidApp()
        }
        composeTestRule.onNodeWithText("Welcome to Android!").assertExists()
    }
}
```

---

#### **3.3 iOS UI Tests**

Write UI tests in Swift to test iOS-specific integrations.

**Example: iOS XCTest (`app-ios/UITests.swift`):**
```swift
import XCTest

class UITests: XCTestCase {
    func testLoginScreen() {
        let app = XCUIApplication()
        app.launch()
        
        let text = app.staticTexts["Welcome to iOS"]
        XCTAssertTrue(text.exists)
    }
}
```

---

### **4. End-to-End Testing**

End-to-end (E2E) tests verify the entire app workflow, including user interactions and backend communication.

---

#### **4.1 E2E Test Setup**

1. **Use Mock Servers**:
   - Simulate API responses to ensure consistent test environments.
   - Tools: [MockWebServer](https://github.com/square/okhttp/tree/master/mockwebserver).

2. **Write Cross-Platform Tests**:
   - Use tools like **Ktor Mock Engine** for shared API mocks.
   - Use platform-specific tools for UI interactions (e.g., Espresso for Android, XCTest for iOS).

---

#### **4.2 E2E Test Example with MockWebServer**

**Setup MockWebServer in Tests:**
```kotlin
import okhttp3.mockwebserver.MockResponse
import okhttp3.mockwebserver.MockWebServer
import kotlin.test.*

class E2ETest {
    private val mockWebServer = MockWebServer()

    @BeforeTest
    fun setup() {
        mockWebServer.start()
    }

    @AfterTest
    fun teardown() {
        mockWebServer.shutdown()
    }

    @Test
    fun testAppEndToEnd() = runTest {
        mockWebServer.enqueue(
            MockResponse()
                .setResponseCode(200)
                .setBody("""{"message": "success"}""")
        )

        val apiClient = ApiClient(mockWebServer.url("/").toString())
        val result = apiClient.fetchMessage()

        assertEquals("success", result)
    }
}
```

---

### **5. Best Practices for Modular Testing**

1. **Isolate Tests per Module**:
   - Test core logic in the `core` module.
   - Test feature-specific functionality in feature modules.
   - Use mocks for external dependencies.

2. **Minimize Platform-Specific Tests**:
   - Focus on shared tests for core logic and shared UI.
   - Write platform-specific tests only when necessary.

3. **Use Dependency Injection**:
   - Inject dependencies like `ApiClient` to simplify mocking and testing.

4. **Run Tests in CI**:
   - Automate running shared and platform-specific tests using CI pipelines (e.g., GitHub Actions, Jenkins).

5. **Leverage Multiplatform Testing Tools**:
   - Use tools like `Ktor Mock Engine` and `SQLDelight Mock Driver` for integration testing.

---
### **CI/CD Setup for Modularized Kotlin Multiplatform Projects**

A robust CI/CD pipeline automates the build, testing, and deployment processes for a modularized Kotlin Multiplatform (KMP) project. Below are examples and best practices for setting up CI/CD pipelines for KMP projects using **GitHub Actions**.

---

### **1. CI/CD Workflow Overview**

#### **1.1 CI Workflow**
1. **Build and Test**:
   - Build all modules.
   - Run unit and integration tests for shared and platform-specific code.
2. **Static Code Analysis**:
   - Use tools like `ktlint` or `detekt` for code quality checks.

#### **1.2 CD Workflow**
1. **Publish Artifacts**:
   - Publish shared libraries (e.g., `core`, `feature-auth`) to a Maven repository.
2. **Deploy Applications**:
   - Deploy Android APKs to Play Store.
   - Deploy iOS apps to TestFlight or App Store.

---

### **2. CI/CD Setup Using GitHub Actions**

---

#### **2.1 Directory Structure**

```
.github/
├── workflows/
│   ├── build.yml      # CI workflow
│   ├── release.yml    # CD workflow
```

---

#### **2.2 Build Workflow (`build.yml`)**

This workflow builds the project and runs all tests.

```yaml
name: Build and Test

on:
  push:
    branches:
      - main
  pull_request:
    branches:
      - main

jobs:
  build-and-test:
    runs-on: ubuntu-latest

    steps:
    # Step 1: Checkout code
    - name: Checkout code
      uses: actions/checkout@v3

    # Step 2: Set up JDK
    - name: Set up JDK 11
      uses: actions/setup-java@v3
      with:
        distribution: 'temurin'
        java-version: '11'

    # Step 3: Cache Gradle dependencies
    - name: Cache Gradle
      uses: actions/cache@v3
      with:
        path: ~/.gradle/caches
        key: gradle-${{ hashFiles('**/*.gradle*', '**/gradle-wrapper.properties') }}

    # Step 4: Build and Test
    - name: Build and Test
      run: ./gradlew build
```

---

#### **2.3 Release Workflow (`release.yml`)**

This workflow publishes shared modules to a Maven repository and deploys platform-specific apps.

```yaml
name: Release

on:
  workflow_dispatch:

jobs:
  publish-shared-modules:
    runs-on: ubuntu-latest

    steps:
    # Step 1: Checkout code
    - name: Checkout code
      uses: actions/checkout@v3

    # Step 2: Set up JDK
    - name: Set up JDK 11
      uses: actions/setup-java@v3
      with:
        distribution: 'temurin'
        java-version: '11'

    # Step 3: Publish Maven Artifacts
    - name: Publish Shared Modules
      run: ./gradlew :core:publish :feature-auth:publish
      env:
        MAVEN_USERNAME: ${{ secrets.MAVEN_USERNAME }}
        MAVEN_PASSWORD: ${{ secrets.MAVEN_PASSWORD }}

  build-android:
    runs-on: ubuntu-latest
    needs: publish-shared-modules

    steps:
    # Step 1: Checkout code
    - name: Checkout code
      uses: actions/checkout@v3

    # Step 2: Set up JDK
    - name: Set up JDK 11
      uses: actions/setup-java@v3
      with:
        distribution: 'temurin'
        java-version: '11'

    # Step 3: Build Android APK
    - name: Build APK
      run: ./gradlew :app-android:assembleRelease

    # Step 4: Upload APK to Play Store
    - name: Deploy to Play Store
      uses: r0adkll/upload-google-play@v1
      with:
        serviceAccountJson: ${{ secrets.GOOGLE_PLAY_SERVICE_ACCOUNT }}
        packageName: com.example.kmp
        releaseFiles: app-android/build/outputs/apk/release/app-release.apk
        track: internal

  build-ios:
    runs-on: macos-latest
    needs: publish-shared-modules

    steps:
    # Step 1: Checkout code
    - name: Checkout code
      uses: actions/checkout@v3

    # Step 2: Set up CocoaPods
    - name: Install CocoaPods
      run: pod install

    # Step 3: Build iOS App
    - name: Build iOS App
      run: xcodebuild -workspace iosApp.xcworkspace -scheme iosApp -sdk iphoneos archive -archivePath iosApp.xcarchive

    # Step 4: Upload to TestFlight
    - name: Deploy to TestFlight
      uses: appleboy/app-store-release-action@v1
      with:
        api_key_id: ${{ secrets.APP_STORE_API_KEY_ID }}
        issuer_id: ${{ secrets.APP_STORE_ISSUER_ID }}
        app_path: iosApp.xcarchive
        app_bundle_identifier: com.example.kmp
        app_store_connect_key: ${{ secrets.APP_STORE_CONNECT_KEY }}
```

---

### **3. Testing in CI/CD**

---

#### **3.1 Running Unit Tests**

Run shared and platform-specific tests:
```yaml
    # Step 5: Run Unit Tests
    - name: Run Unit Tests
      run: ./gradlew test
```

#### **3.2 Integration Tests**

Use a mock server like MockWebServer to simulate backend interactions in the pipeline.

```yaml
    # Step 6: Run Integration Tests
    - name: Run Integration Tests
      run: ./gradlew integrationTest
```

#### **3.3 UI Tests**

Run UI tests using Android Emulator and XCTest for iOS.

**Android Emulator Setup:**
```yaml
    - name: Set up Android Emulator
      uses: reactivecircus/android-emulator-runner@v2
      with:
        api-level: 30
        script: ./gradlew connectedAndroidTest
```

**iOS XCTest:**
```yaml
    - name: Run iOS UI Tests
      run: xcodebuild -workspace iosApp.xcworkspace -scheme iosApp -sdk iphonesimulator test
```

---

### **4. Best Practices for CI/CD in KMP**

1. **Use Secrets for Credentials**:
   - Store sensitive information (e.g., Maven credentials, Play Store keys) in GitHub Secrets.

2. **Parallelize Jobs**:
   - Use `needs` to parallelize Android and iOS builds after shared modules are published.

3. **Automate Dependency Updates**:
   - Use Dependabot or similar tools to keep dependencies up to date.

4. **Use Incremental Builds**:
   - Leverage Gradle’s incremental builds to speed up pipelines.

5. **Fail Fast**:
   - Break workflows into smaller jobs so failures in one job don’t affect the entire pipeline.

---

### **5. Real-World Example: Modular KMP Project**

**Modules**:
1. **Core Module**: Contains utilities, models, and API clients.
2. **Feature Modules**:
   - `feature-auth`: Handles authentication.
   - `feature-payment`: Handles payments.
3. **App Modules**:
   - `app-android`: Android-specific UI and logic.
   - `app-ios`: iOS-specific UI and logic.

**CI/CD Workflow**:
- **Build and Test**:
   - Builds all modules and runs tests for shared and platform-specific code.
- **Publish Libraries**:
   - Publishes `core`, `feature-auth`, and `feature-payment` to a Maven repository.
- **Deploy Apps**:
   - Deploys Android APKs to Play Store and iOS apps to TestFlight.

---
