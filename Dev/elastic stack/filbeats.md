### **Filebeat Configuration Explanation (Updated)**  

This configuration is designed for **collecting JSON logs** and **forwarding them to Logstash** in a Kubernetes environment.

---

## **1. General Settings**  
```yaml
name: "${POD_NAMESPACE}.${APP_NAME}"
```
- Sets the Filebeat instance name dynamically using environment variables.
- Useful for identifying logs from different pods or applications.

---

## **2. Log Input Configuration**  
```yaml
filebeat.inputs:
  - type: log
    paths:
      - /var/log/**/*.log
      - /var/log/*.log
      - /logs/vosp.*.log
```

### **Other `type` Options & Differences**
| Type            | Description |
|----------------|-------------|
| `log`          | Reads log files (default for most cases). |
| `filestream`   | More efficient than `log`, optimized for handling log rotation. |
| `stdin`        | Reads input from standard input (useful for debugging). |
| `syslog`       | Collects logs from the system syslog service. |
| `tcp` / `udp`  | Listens for logs sent over the network. |
| `httpjson`     | Pulls logs from HTTP APIs that return JSON responses. |

- **Use `log`** if reading from files.  
- **Use `filestream`** for better performance and rotation handling.  
- **Use `syslog`** if collecting from system logs.

---

## **3. JSON Parsing**
```yaml
    json.keys_under_root: true
    json.add_error_key: true
    json.message_key: message
```

### **Example of Log with JSON Parsing Disabled**
#### **Input File (`app.log`)**
```json
{"timestamp":"2025-03-06T12:00:00Z","level":"ERROR","message":"Something went wrong","user":"admin"}
```
#### **Output Without JSON Parsing**
```json
{
  "message": "{\"timestamp\":\"2025-03-06T12:00:00Z\",\"level\":\"ERROR\",\"message\":\"Something went wrong\",\"user\":\"admin\"}"
}
```
- The entire JSON is **treated as a string** inside `"message"`.

### **Example with JSON Parsing Enabled**
#### **Output With `json.keys_under_root: true`**
```json
{
  "timestamp": "2025-03-06T12:00:00Z",
  "level": "ERROR",
  "message": "Something went wrong",
  "user": "admin"
}
```
- **JSON keys are extracted and placed at the root level**.

#### **If `json.message_key: message` Is Set**
```json
{
  "timestamp": "2025-03-06T12:00:00Z",
  "level": "ERROR",
  "log.message": "Something went wrong",
  "user": "admin"
}
```
- The `"message"` key is **renamed to `log.message`**, preventing conflicts.

---

## **4. Multiline Log Handling**
```yaml
    multiline.type: pattern
    multiline.pattern: '^[0-9]{4}-[0-9]{2}-[0-9]{2}'
    multiline.negate: true
    multiline.match: after
```

### **Example Without Multiline Handling**
#### **Input File (`error.log`)**
```
2025-03-06 ERROR Something failed:
java.lang.NullPointerException
    at com.example.Main.main(Main.java:10)
```
#### **Output Without Multiline Handling**
```json
{ "message": "2025-03-06 ERROR Something failed:" }
{ "message": "java.lang.NullPointerException" }
{ "message": "at com.example.Main.main(Main.java:10)" }
```
- Each line is treated as a **separate log entry**.

### **Example With Multiline Handling Enabled**
```json
{
  "message": "2025-03-06 ERROR Something failed:\njava.lang.NullPointerException\n    at com.example.Main.main(Main.java:10)"
}
```
- **The stack trace is merged into a single log entry**.

---

## **5. Log Processing (`processors`)**
```yaml
  - dissect:
      tokenizer: '%{parsed-timestamp} %{+parsed-timestamp} %{log.level} [%{log.logger}] - %{message}'
      field: 'message'
      trim_values: all
      overwrite_keys: true
```

### **What Happens If Some Fields Are Missing?**
- **Missing fields are ignored**, but parsing may fail if essential fields are missing.

#### **Example Log**
```
2025-03-06 ERROR [AuthService] - User login failed
```
#### **With Correct Tokenizer (`parsed-timestamp`, `log.level`, etc.)**
```json
{
  "parsed-timestamp": "2025-03-06",
  "log.level": "ERROR",
  "log.logger": "AuthService",
  "message": "User login failed"
}
```
#### **If the Log Format Changes (e.g., Missing Log Level)**
```
2025-03-06 [AuthService] - User login failed
```
#### **Output**
```json
{
  "parsed-timestamp": "2025-03-06",
  "message": "[AuthService] - User login failed"
}
```
- **`log.level` is missing**, but the log is still processed.

---

## **6. Timestamp Handling**
```yaml
  - timestamp:
      field: parsed-timestamp
      layouts:
        - '2006-01-02 15:04:05'
```

### **What Is `layouts`?**
- Defines **the expected timestamp format**.

### **Why `2006-01-02 15:04:05`?**
- This is **a Go language convention**:
  - `2006` → Year  
  - `01` → Month  
  - `02` → Day  
  - `15:04:05` → Time (24-hour format)  

### **Example Input Log**
```
2025-03-06 12:30:45 ERROR - System failure
```
#### **Output**
```json
{
  "@timestamp": "2025-03-06T12:30:45.000Z"
}
```

---

## **7. Removing Unnecessary Fields**
```yaml
  - drop_fields:
      fields: [parsed-timestamp]
```
- **Yes, `parsed-timestamp` is first added and then removed** after extracting `@timestamp`.

---

## **8. What Is `"garbage"`?**
- `"garbage"` refers to **temporary or unwanted fields extracted during parsing**.
- Used in `dissect` to **capture unused values**.

#### **Example Dissect Tokenizer**
```yaml
  - dissect:
      tokenizer: '%{orchestrator.cluster.name}-%{garbage.hash1}-%{garbage.node.type}-%{geo.name}-%{garbage.hash2}'
      field: 'host.hostname'
```
#### **Input**
```
my-cluster-ABCD-worker-europe-XYZ
```
#### **Output**
```json
{
  "orchestrator.cluster.name": "my-cluster",
  "geo.name": "europe",
  "garbage": {
    "hash1": "ABCD",
    "node.type": "worker",
    "hash2": "XYZ"
  }
}
```
- **`garbage` fields are removed** later.

---

## **9. Monitoring Settings**
```yaml
monitoring:
  enabled: false
  cluster_uuid: "${ES_MONITORING_CLUSTER_UUID}"
```

### **Example When `enabled: true`**
- Filebeat **sends monitoring data to Elasticsearch**.
- Example output:
```json
{
  "filebeat.stats": {
    "events": 1500,
    "uptime": "2h30m",
    "harvesters": 5
  }
}
```

### **When `enabled: false`**
- **Monitoring is disabled**, and no stats are sent.

---

## **10. Example of Metric Logging**
```yaml
logging.metrics.enabled: true
```
#### **Example Output**
```json
{
  "log": {
    "level": "INFO",
    "message": "Filebeat is processing 5 files, sent 200 events in the last minute."
  }
}
```
- Useful for tracking Filebeat's health.

---

### **Final Notes**
- **`log` vs `filestream`** → `filestream` is better for handling log rotation.
- **Missing tokenizer fields are ignored, but essential ones can cause parsing errors**.
- **Garbage fields are placeholders and can be dropped later**.
- **Monitoring is useful but adds overhead**.