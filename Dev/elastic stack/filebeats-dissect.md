### **Dissect Processor in Filebeat**  

`dissect` is a **string tokenizer** that **splits a log message into structured fields** based on a pattern. It works like `grok` but is **lighter and faster**, assuming a **fixed log format** instead of regex-based matching.

---

## **1. How Does Dissect Work?**
- It **extracts fields** from a log line based on **delimiters** (fixed separators).
- It is **non-greedy**, meaning it takes only what is necessary for each field.
- If a field in the pattern **does not exist in the log**, it remains **empty** instead of causing an error.

### **Syntax**
```yaml
- dissect:
    tokenizer: '<pattern>'
    field: '<source-field>'
    trim_values: true
    overwrite_keys: true
```
- `tokenizer`: Defines **how to split the log** into fields.
- `field`: Specifies **which field to apply the pattern to** (usually `"message"`).
- `trim_values`: Removes **leading/trailing spaces**.
- `overwrite_keys`: If `true`, overwrites existing fields.

---

## **2. Understanding Tokenizer & Field**
### **What Is `tokenizer`?**
- A **pattern** that tells **how to split the log message** into fields.
- Uses **placeholders (`%{field_name}`)** to capture data.

### **What Is `field`?**
- The **source field** in the event where `dissect` should extract data.
- **Most common value:** `"message"` (raw log content).

---

## **3. Example of Dissect in Action**
### **Example Log**
```
2025-03-06 12:00:00 ERROR [AuthService] - User login failed
```
### **Dissect Configuration**
```yaml
- dissect:
    tokenizer: "%{timestamp} %{+timestamp} %{log.level} [%{log.logger}] - %{message}"
    field: "message"
```
### **Output**
```json
{
  "timestamp": "2025-03-06 12:00:00",
  "log.level": "ERROR",
  "log.logger": "AuthService",
  "message": "User login failed"
}
```
- **`timestamp`** captures `2025-03-06 12:00:00`
- **`log.level`** captures `ERROR`
- **`log.logger`** captures `AuthService`
- **`message`** captures `User login failed`
- **`%{+timestamp}`** appends the second timestamp part (`12:00:00`).

---

## **4. Why Multiple `dissect` Processors?**
You **need multiple `dissect` processors** if:
1. **Extracting from different fields** (e.g., `"message"` and `"orchestrator.namespace"`).
2. **Handling nested structures** (e.g., first extracting a field, then dissecting its value further).
3. **Breaking logs into logical parts** before refining them.

### **Example of Multiple Dissects**
```yaml
- dissect:
    tokenizer: "%{host.name}-%{garbage.hash}-%{geo.location}"
    field: "host.hostname"
- dissect:
    tokenizer: "%{env}-%{garbage.project}"
    field: "orchestrator.namespace"
```
- **First `dissect`**: Splits `host.hostname` into `host.name` and `geo.location`, ignoring `garbage.hash`.
- **Second `dissect`**: Extracts `env` from `orchestrator.namespace`, ignoring `garbage.project`.

---

## **5. What Happens If Fields Are Missing?**
- Missing fields **do not cause errors**.
- The field is simply **left empty**.

### **Example**
#### **Log**
```
2025-03-06 ERROR - Something happened
```
#### **Pattern**
```yaml
- dissect:
    tokenizer: "%{timestamp} %{log.level} [%{log.logger}] - %{message}"
    field: "message"
```
#### **Output**
```json
{
  "timestamp": "2025-03-06",
  "log.level": "ERROR",
  "message": "Something happened"
}
```
- **`log.logger` is missing**, but parsing continues.

---

## **6. When to Use `dissect` vs `grok`**
| Feature  | `dissect` | `grok` |
|----------|----------|--------|
| **Performance** | Faster (no regex) | Slower (regex-based) |
| **Log Format** | Fixed (consistent separators) | Variable (regex parsing) |
| **Flexibility** | Low (must match order) | High (complex matching) |
| **Error Handling** | Missing fields are ignored | Missing fields may break parsing |

- **Use `dissect`** if logs have a **consistent structure**.
- **Use `grok`** if logs **vary in format**.

---

### **Summary**
- `dissect` **splits logs into fields** using a **fixed structure**.
- **`tokenizer`** defines **how to extract data**.
- **`field`** specifies **where to apply `dissect`**.
- **Multiple `dissect` processors** help **handle nested data** or **different log formats**.
- **Missing fields are ignored**, preventing errors.