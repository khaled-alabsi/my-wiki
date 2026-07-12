### **Summary: Difference Between `runBlocking`, `launch`, and `async`**

| **Feature**           | **runBlocking**              | **launch**                      | **async**                       |
|------------------------|------------------------------|----------------------------------|----------------------------------|
| **Purpose**           | Bridges blocking and non-blocking worlds. | Launches a coroutine for fire-and-forget tasks. | Launches a coroutine to compute and return a result. |
| **Start Behavior**    | Executes immediately and blocks the thread. | Starts immediately (unless explicitly lazy). | Starts immediately (unless explicitly lazy). |
| **Return Type**       | Result of the block.         | `Job` (no result).              | `Deferred<T>` (result via `await()`). |
| **Blocking**          | Yes, blocks the current thread. | No, non-blocking.               | No, non-blocking (but `await()` suspends). |
| **When to Use**       | For testing or bridging synchronous and asynchronous code. | For tasks where no result is needed (fire-and-forget). | For concurrent tasks where results are needed later. |
| **Lazy Support**      | Not applicable.              | Yes, with `start = CoroutineStart.LAZY`. | Yes, with `start = CoroutineStart.LAZY`. |

---

### **Key Takeaways**
1. **`runBlocking`:**
   - Blocks the current thread until all coroutines inside finish.
   - Useful for testing or entry points like `main`.

2. **`launch`:**
   - Fire-and-forget coroutine. Does not return a result.
   - Ideal for background jobs, logging, or other side effects.

3. **`async`:**
   - Returns a `Deferred` object that represents a future result.
   - Best for concurrent computations, especially when results are needed later.
   - Avoid calling `await()` immediately unless necessary; let tasks run concurrently.

4. **Lazy Mode:**
   - Both `launch` and `async` can be configured as lazy using `start = CoroutineStart.LAZY`, requiring explicit `start()` or `await()` to begin execution.

Here are **detailed examples** for each of `runBlocking`, `launch`, and `async`, showcasing their specific use cases.

---

### 1. **`runBlocking`: Blocking Execution**

`runBlocking` is often used in the `main` function or tests to run suspend functions in a blocking manner. 

#### Example: Sequential Execution
```kotlin
import kotlinx.coroutines.*

fun main() {
    println("Before runBlocking")
    runBlocking {
        println("Inside runBlocking: Start")
        delay(1000) // Simulates a suspending task
        println("Inside runBlocking: End")
    }
    println("After runBlocking")
}
```

**Output:**
```
Before runBlocking
Inside runBlocking: Start
Inside runBlocking: End
After runBlocking
```

**Explanation:**
- The `runBlocking` block suspends for `delay(1000)` but blocks the thread it's running on (e.g., the main thread).
- Execution outside `runBlocking` resumes only after the block completes.

---

### 2. **`launch`: Fire-and-Forget Task**

`launch` is used for tasks that don’t return results but run concurrently in the background.

#### Example: Concurrent Execution
```kotlin
import kotlinx.coroutines.*

fun main() = runBlocking {
    println("Before launching coroutine")
    val job = launch {
        println("Launch: Starting background work")
        delay(1000) // Simulates background task
        println("Launch: Background work complete")
    }
    println("Main: Doing other work")
    job.join() // Wait for the coroutine to finish
    println("Main: All work done")
}
```

**Output:**
```
Before launching coroutine
Launch: Starting background work
Main: Doing other work
Launch: Background work complete
Main: All work done
```

**Explanation:**
- `launch` starts a coroutine immediately and runs in the background.
- The `join()` call ensures the main program waits for the `launch` coroutine to complete.

---

### 3. **`async`: Concurrent Tasks with Results**

`async` is used for concurrent tasks that return a value, which can be accessed using `await()`.

#### Example: Fetching Data Concurrently
```kotlin
import kotlinx.coroutines.*

fun main() = runBlocking {
    println("Starting concurrent tasks")

    val task1 = async { fetchData("Task 1", 2000) }
    val task2 = async { fetchData("Task 2", 1000) }

    println("Main: Doing other work while tasks are running")

    val result1 = task1.await() // Wait for Task 1 result
    val result2 = task2.await() // Wait for Task 2 result

    println("Results: $result1, $result2")
}

suspend fun fetchData(name: String, delayTime: Long): String {
    delay(delayTime)
    return "$name completed"
}
```

**Output:**
```
Starting concurrent tasks
Main: Doing other work while tasks are running
Results: Task 1 completed, Task 2 completed
```

**Explanation:**
- Both tasks run concurrently in the background.
- `await()` retrieves the results after the tasks are complete.

---

### 4. **Lazy Mode with `launch` and `async`**

You can control when coroutines start using `CoroutineStart.LAZY`.

#### Example: Lazy `launch`
```kotlin
import kotlinx.coroutines.*

fun main() = runBlocking {
    val job = launch(start = CoroutineStart.LAZY) {
        println("Lazy Launch: Work started")
        delay(1000)
        println("Lazy Launch: Work finished")
    }

    println("Main: Job not started yet")
    job.start() // Explicitly start the coroutine
    job.join()  // Wait for it to finish
    println("Main: Job complete")
}
```

**Output:**
```
Main: Job not started yet
Lazy Launch: Work started
Lazy Launch: Work finished
Main: Job complete
```

---

#### Example: Lazy `async`
```kotlin
import kotlinx.coroutines.*

fun main() = runBlocking {
    val deferred = async(start = CoroutineStart.LAZY) {
        println("Lazy Async: Work started")
        delay(1000)
        "Lazy Result"
    }

    println("Main: Async not started yet")
    deferred.start() // Explicitly start the coroutine
    val result = deferred.await() // Wait for result
    println("Main: Got result: $result")
}
```

**Output:**
```
Main: Async not started yet
Lazy Async: Work started
Main: Got result: Lazy Result
```

**Explanation:**
- Lazy mode allows control over when the coroutine starts.
- In both `launch` and `async`, the task won’t start until `start()` or `await()` is called.

---

### 5. **Comparison of `launch` and `async` in Parallel Execution**

#### Example: Using `launch` and `async` Together
```kotlin
import kotlinx.coroutines.*

fun main() = runBlocking {
    // Using launch for background work
    val job = launch {
        println("Launch: Starting background task")
        delay(1500)
        println("Launch: Background task complete")
    }

    // Using async for concurrent computations
    val deferred = async {
        println("Async: Starting computation")
        delay(1000)
        "Computation Result"
    }

    println("Main: Doing other work")

    job.join() // Wait for the launch task
    val result = deferred.await() // Wait for the async result
    println("Main: Got async result: $result")
}
```

**Output:**
```
Launch: Starting background task
Async: Starting computation
Main: Doing other work
Async: Computation Result
Launch: Background task complete
Main: Got async result: Computation Result
```

---

### Summary of Examples

1. **`runBlocking`**: Sequential execution that blocks the thread, used in tests or the `main` function.
2. **`launch`**: Fire-and-forget tasks, ideal for side effects or background work.
3. **`async`**: Concurrent computations, ideal for returning results without blocking.
4. **Lazy Mode**: Controls when `launch` or `async` coroutines start.

Here are examples demonstrating **error handling** and **structured concurrency** with `launch` and `async`.

---

### **Error Handling in Coroutines**

Error handling in coroutines requires understanding that:
- Exceptions thrown in a coroutine propagate to the parent coroutine (unless explicitly handled).
- `try-catch` can be used for individual coroutines.
- CoroutineScope handles uncaught exceptions for child coroutines.

---

#### Example 1: Using `try-catch` in `launch`
```kotlin
import kotlinx.coroutines.*

fun main() = runBlocking {
    val job = launch {
        try {
            println("Launch: Starting risky task")
            throw Exception("Something went wrong")
        } catch (e: Exception) {
            println("Launch: Caught exception - ${e.message}")
        }
    }
    job.join()
    println("Main: Job complete despite exception")
}
```

**Output:**
```
Launch: Starting risky task
Launch: Caught exception - Something went wrong
Main: Job complete despite exception
```

---

#### Example 2: Using `try-catch` in `async`
```kotlin
import kotlinx.coroutines.*

fun main() = runBlocking {
    val deferred = async {
        try {
            println("Async: Starting risky computation")
            throw Exception("Computation failed")
        } catch (e: Exception) {
            println("Async: Caught exception - ${e.message}")
            "Default Result" // Return a fallback value
        }
    }

    val result = deferred.await()
    println("Main: Got result - $result")
}
```

**Output:**
```
Async: Starting risky computation
Async: Caught exception - Computation failed
Main: Got result - Default Result
```

**Key Point:**
- `async` can return a fallback value after handling the exception, unlike `launch` which doesn't return anything.

---

#### Example 3: Handling Exceptions with CoroutineScope
```kotlin
import kotlinx.coroutines.*

fun main() = runBlocking {
    val scope = CoroutineScope(SupervisorJob())

    val job1 = scope.launch {
        println("Job1: Starting task")
        throw Exception("Job1 failed")
    }

    val job2 = scope.launch {
        println("Job2: Independent task continues")
        delay(500)
        println("Job2: Task complete")
    }

    job1.join()
    job2.join()

    println("Main: All jobs finished")
}
```

**Output:**
```
Job1: Starting task
Job2: Independent task continues
Job2: Task complete
Main: All jobs finished
```

**Key Point:**
- `SupervisorJob` ensures that one coroutine's failure doesn't cancel others.

---

### **Structured Concurrency**

Structured concurrency ensures that all child coroutines are completed before the parent coroutine finishes, simplifying lifecycle management.

---

#### Example 1: `coroutineScope` for Hierarchical Control
```kotlin
import kotlinx.coroutines.*

fun main() = runBlocking {
    println("Main: Starting parent scope")
    coroutineScope {
        launch {
            println("Child1: Starting task")
            delay(1000)
            println("Child1: Task complete")
        }

        launch {
            println("Child2: Starting task")
            delay(500)
            println("Child2: Task complete")
        }
    }
    println("Main: Parent scope complete")
}
```

**Output:**
```
Main: Starting parent scope
Child1: Starting task
Child2: Starting task
Child2: Task complete
Child1: Task complete
Main: Parent scope complete
```

**Key Point:**
- The parent (`coroutineScope`) waits for all its children to complete before continuing.

---

#### Example 2: Cancelling Parent Cancels Children
```kotlin
import kotlinx.coroutines.*

fun main() = runBlocking {
    val job = launch {
        launch {
            println("Child1: Starting task")
            delay(1000)
            println("Child1: Task complete")
        }

        launch {
            println("Child2: Starting task")
            delay(1500)
            println("Child2: Task complete")
        }
    }

    delay(700) // Let the children run for a while
    println("Main: Cancelling parent job")
    job.cancelAndJoin()

    println("Main: Parent and children cancelled")
}
```

**Output:**
```
Child1: Starting task
Child2: Starting task
Main: Cancelling parent job
Main: Parent and children cancelled
```

**Key Point:**
- Cancelling a parent job cancels all child coroutines.

---

#### Example 3: `supervisorScope` for Independent Child Cancellation
```kotlin
import kotlinx.coroutines.*

fun main() = runBlocking {
    supervisorScope {
        val job1 = launch {
            println("Child1: Starting task")
            throw Exception("Child1 failed")
        }

        val job2 = launch {
            println("Child2: Starting task")
            delay(500)
            println("Child2: Task complete")
        }

        job1.join()
        job2.join()
    }
    println("Main: Supervisor scope complete")
}
```

**Output:**
```
Child1: Starting task
Child2: Starting task
Child2: Task complete
Main: Supervisor scope complete
```

**Key Point:**
- In `supervisorScope`, the failure of one child doesn’t cancel other children.

---

### **Key Takeaways**

#### Error Handling:
1. Use `try-catch` inside individual coroutines (`launch` or `async`).
2. Use `SupervisorJob` or `supervisorScope` to prevent failures in one coroutine from propagating to others.

#### Structured Concurrency:
1. `coroutineScope` ensures all child coroutines complete before exiting the scope.
2. Cancelling a parent cancels all its children unless `supervisorScope` is used.
