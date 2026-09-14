### **How Metricbeat Works in This Configuration**
Metricbeat collects metrics from Logstash and other Beats instances, then sends them to Logstash for further processing before reaching Elasticsearch.

---

### **Inputs of Metricbeat**
1. **Logstash Metrics:**
   - Uses the `logstash` module.
   - Collects `node` and `node_stats` every **10s**.
   - Connects to Logstash instances via `logstash-headless` service on port **9600**.
   - `xpack.enabled: true` enables enhanced monitoring.

2. **Beats Metrics (Self-Monitoring + Other Beats)**
   - Uses the `beat` module.
   - Collects `stats` and `state` every **10s**.
   - Reads from:
     - Localhost (`http://localhost:5066`) – Own Metricbeat process.
     - `example-log-workload-metrics` (`http://${BEATS_MONITORED_SERVICENAME}.${NAMESPACE}.svc.cluster.local:5066`) – Another Beat instance.

---

### **How Metricbeat Connects**
1. **Logstash Metrics Collection:**
   - Connects to Logstash nodes at `logstash-0.logstash-headless.${NAMESPACE}.svc.cluster.local:9600`, etc.
   
2. **Beats Metrics Collection:**
   - Connects to self (`localhost:5066`) and another monitored Beat service (`example-log-workload-metrics`).

3. **Sending Data to Logstash:**
   - Sends collected metrics to `logstash.${NAMESPACE}.svc.cluster.local:5044`.
   - Uses TLS (`logstash-ca.crt`) for secure communication.

---

### **Workflow**
1. Metricbeat starts and initializes the keystore (via `initContainers`).
2. It reads the configuration from `metricbeat.yml` (mounted via ConfigMap).
3. It collects Logstash and Beats metrics every **10 seconds**.
4. Metrics are sent securely to Logstash (`5044`), which processes and forwards them to Elasticsearch.
5. The HTTP server (`5066`) exposes local metrics for health monitoring.

This setup enables Logstash monitoring and self-monitoring of Metricbeat, ensuring visibility into the pipeline.

**Metricbeat does not get called by any other service**. Instead, it is the **client** that actively collects metrics from other services. Specifically:

- It **calls** Logstash instances (on port 9600) to collect **Logstash metrics**.
- It **calls** other Beats (like Filebeat, if configured) to collect their metrics (on port 5066, for example).

In summary, Metricbeat is a **pull-based** agent that gathers data from other services (Logstash, Filebeat, etc.) and then forwards it, typically to Logstash for further processing. It does not have any service actively calling or interacting with it.

So, Metricbeat gathers the information, sends it to Logstash, and Logstash handles sending the data to Elasticsearch.. Here's how the flow works:

1. **Metricbeat** collects metrics from **Logstash** (via its HTTP interface on port 9600) and other Beats (like Filebeat).
2. Metricbeat then sends this data **back to Logstash** (on port 5044).
3. **Logstash** processes the incoming metrics from Metricbeat and forwards them to **Elasticsearch** for storage, analysis, and visualization.

---

## Configs


```yaml
---

kind: Secret
apiVersion: v1
metadata:
  name: logstash-metricbeat-tls
  # namespace: 015005-examplecloud-dev
  labels:
    app: logstash
    app.kubernetes.io/component: metrics
data:
  logstash-ca.crt: >-
    LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0tLS0tCk1J....
type: Opaque
---
kind: ConfigMap
apiVersion: v1
metadata:
  name: logstash-metricbeat-env
  # namespace: 015005-elasticpre-dev
  labels:
    app: logstash
    app.kubernetes.io/component: metrics
data:
  BEATS_MONITORED_SERVICENAME: 'example-log-workload-metrics'

---

kind: ConfigMap
apiVersion: v1
metadata:
  name: logstash-metricbeat-config
  # namespace: 015005-elasticpre-dev
  labels:
    app: logstash
    app.kubernetes.io/component: metrics
data:
  metricbeat.yml: |-
    name: "${NAMESPACE}.${POD_NAME}"
    metricbeat:
      modules:
      - module: logstash
        metricsets:
          - node
          - node_stats
        period: 10s
        hosts: ["logstash-0.logstash-headless.${NAMESPACE}.svc.cluster.local:9600", "logstash-1.logstash-headless.${NAMESPACE}.svc.cluster.local:9600", "logstash-2.logstash-headless.${NAMESPACE}.svc.cluster.local:9600"]
        xpack.enabled: true
      - module: beat
        metricsets:
          - stats
          - state
        period: 10s
        hosts: ["http://localhost:5066", "http://${BEATS_MONITORED_SERVICENAME}.${NAMESPACE}.svc.cluster.local:5066"]
        xpack.enabled: true
    output:
      logstash:
        hosts:
          - "logstash.${NAMESPACE}.svc.cluster.local:5044"
        ssl:
          certificate_authorities: ["/usr/share/metricbeat/tls/logstash-ca.crt"]

    http:
      enabled: true
      port: 5066 # The default port, just to document it for local collection above
    monitoring:
      enabled: "false"
      cluster_uuid: "${ES_MONITORING_CLUSTER_UUID}"
    logging.metrics.enabled: false

---

kind: PersistentVolumeClaim
apiVersion: v1
metadata:
  name: logstash-metricbeat-data
  # namespace: 015005-examplecloud-dev
  labels:
    app: logstash
    app.kubernetes.io/component: metrics
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 50Mi
  storageClassName: netapp-trident-nas
  volumeMode: Filesystem

---

kind: Deployment
apiVersion: apps/v1
metadata:
  name: logstash-metricbeat
  # namespace: 015005-examplecloud-dev
  labels:
    app: logstash
    app.kubernetes.io/component: metrics
  annotations:
    reloader.stakater.com/auto: "true"
spec:
  replicas: 1
  selector:
    matchLabels:
      app: logstash-metricbeat
  template:
    metadata:
      labels:
        app: logstash-metricbeat
        app.kubernetes.io/component: metrics
    spec:
      restartPolicy: Always
      initContainers:
        - resources:
            limits:
              cpu: 50m
              memory: 200Mi
            requests:
              cpu: 5m
              memory: 50Mi
          terminationMessagePath: /dev/termination-log
          name: elastic-internal-init-keystore
          command:
            - /usr/bin/env
            - bash
            - '-c'
            - "#!/usr/bin/env bash\n\nset -eux\n\necho \"Initializing keystore.\"\n\n# create a keystore in the default data path\nmetricbeat keystore create --force\n\n# add all existing secret entries into it\nfor filename in  /mnt/elastic-internal/secure-settings/*; do\n\t[[ -e \"$filename\" ]] || continue # glob does not match\n\tkey=$(basename \"$filename\")\n\techo \"Adding \"$key\" to the keystore.\"\n\tcat \"$filename\" | metricbeat keystore add \"$key\" --stdin --force\ndone\n\necho \"Keystore initialization successful.\"\n"
          env:
            - name: POD_IP
              valueFrom:
                fieldRef:
                  apiVersion: v1
                  fieldPath: status.podIP
            - name: POD_NAME
              valueFrom:
                fieldRef:
                  apiVersion: v1
                  fieldPath: metadata.name
            - name: NODE_NAME
              valueFrom:
                fieldRef:
                  apiVersion: v1
                  fieldPath: spec.nodeName
            - name: NAMESPACE
              valueFrom:
                fieldRef:
                  apiVersion: v1
                  fieldPath: metadata.namespace
          securityContext:
            privileged: false
          imagePullPolicy: IfNotPresent
          volumeMounts:
            - name: beat-data
              mountPath: /usr/share/metricbeat/data
          terminationMessagePolicy: File
          image: 'quay.apps.cloud.internal/01-50-05-monitoring/metricbeat-ubi8:8.5.0'
      schedulerName: default-scheduler
      terminationGracePeriodSeconds: 30
      securityContext: {}
      containers:
        - resources:
            limits:
              cpu: 50m
              memory: 200Mi
            requests:
              cpu: 5m
              memory: 50Mi
          terminationMessagePath: /dev/termination-log
          name: metricbeat
          envFrom: 
            - configMapRef:
                name: logstash-metricbeat-env
          env:
            - name: POD_NAME
              valueFrom:
                fieldRef:
                  apiVersion: v1
                  fieldPath: metadata.name
            - name: NAMESPACE
              valueFrom:
                fieldRef:
                  apiVersion: v1
                  fieldPath: metadata.namespace
            - name: ES_MONITORING_CLUSTER_UUID
              valueFrom:
                configMapKeyRef:
                  name: logstash-elastic-env
                  key: ES_MONITORING_CLUSTER_UUID
          imagePullPolicy: IfNotPresent
          volumeMounts:
            - name: beat-data
              mountPath: /usr/share/metricbeat/data
            - name: config
              readOnly: true
              mountPath: /usr/share/metricbeat/metricbeat.yml
              subPath: metricbeat.yml
            - name: tls
              readOnly: true
              mountPath: /usr/share/metricbeat/tls
          terminationMessagePolicy: File
          image: 'quay.apps.cloud.internal/01-50-05-monitoring/metricbeat-ubi8:8.5.0'
          args:
            - '-e'
      automountServiceAccountToken: false
      volumes:
        - name: beat-data
          persistentVolumeClaim:
            claimName: logstash-metricbeat-data
        - name: config
          configMap:
            name: logstash-metricbeat-config
            defaultMode: 292
            optional: false
        - name: tls
          secret:
            secretName: logstash-metricbeat-tls
            defaultMode: 420
            optional: false
      dnsPolicy: ClusterFirst
  strategy:
    type: Recreate
  revisionHistoryLimit: 10
  progressDeadlineSeconds: 600

---

```

Here's an explanation of the **Metricbeat config lines** from the `metricbeat.yml` section:

1. **`name: "${NAMESPACE}.${POD_NAME}"`**:
   - Sets the **name** of the Metricbeat instance using the namespace and pod name from the environment variables. This helps to uniquely identify each instance of Metricbeat in a Kubernetes cluster.

2. **`metricbeat:`**:
   - Main configuration block for Metricbeat.

3. **`modules:`**:
   - Defines the modules that Metricbeat will use to collect metrics.

4. **`- module: logstash`**:
   - Specifies that Metricbeat will use the **Logstash module** to collect metrics from Logstash instances.

5. **`metricsets:`**:
   - Defines which specific metrics will be collected by the module.
   - **`node`**: Collects general node statistics.
   - **`node_stats`**: Collects detailed statistics about Logstash nodes.

6. **`period: 10s`**:
   - Sets the **collection period** to every 10 seconds for the specified metricsets.

7. **`hosts: [...]`**:
   - Lists the **Logstash instances** Metricbeat will collect metrics from. The hosts are specified as service names in the Kubernetes cluster (e.g., `logstash-0.logstash-headless.${NAMESPACE}.svc.cluster.local:9600`), indicating the address of Logstash nodes.

8. **`xpack.enabled: true`**:
   - Enables **X-Pack** features like security, monitoring, and alerting for Metricbeat.

9. **`- module: beat`**:
   - Specifies the **Beat module**, which allows Metricbeat to collect metrics from other Beats (e.g., Filebeat).

10. **`metricsets:`**:
    - **`stats`**: Collects general statistics about the Beat.
    - **`state`**: Collects the state of the Beat.

11. **`hosts: [...]`**:
    - Lists the **Beat instances** Metricbeat will collect metrics from, including the local Beat (`localhost:5066`) and other Beats defined by the `BEATS_MONITORED_SERVICENAME` environment variable.

12. **`output:`**:
    - Configures the output destination for the metrics collected by Metricbeat.

13. **`logstash:`**:
    - Specifies **Logstash** as the output destination for Metricbeat, using the `5044` port, which is the Beats input port on Logstash.

14. **`hosts: [...]`**:
    - Defines the **Logstash service** in the Kubernetes cluster as the destination for Metricbeat data.

15. **`ssl:`**:
    - Enables **SSL encryption** for communication between Metricbeat and Logstash.
    - **`certificate_authorities:`**: Specifies the path to the **CA certificate** used to verify the SSL connection.

16. **`http:`**:
    - Configures an HTTP server for local collection of metrics (port 5066).
    - **`enabled: true`**: Enables HTTP collection.
    - **`port: 5066`**: Specifies the port for the HTTP collection.

17. **`monitoring:`**:
    - Disables the built-in monitoring of Metricbeat (`enabled: "false"`).

18. **`logging.metrics.enabled: false`**:
    - Disables logging of **Metricbeat metrics** themselves.

These lines define how Metricbeat interacts with Logstash, other Beats, and its output, ensuring it collects and sends relevant metrics to the designated Logstash instances for further processing.