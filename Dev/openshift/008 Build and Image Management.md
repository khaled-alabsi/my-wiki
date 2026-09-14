### **What Are ImageStreams?**

ImageStreams in OpenShift are like **smart pointers** to container images. Instead of directly referencing an image stored in a registry (e.g., Quay or DockerHub), you use an ImageStream. Think of it as a dynamic catalog entry that tracks which image version you are currently using.

#### Intuition:
Imagine you're running a restaurant. Instead of placing all ingredients directly in the kitchen (quay), you have a menu (ImageStream). This menu doesn't hold the ingredients but tells the chef where to get them. Whenever the ingredients (image version) are updated, your menu stays relevant without needing to rewrite recipes (deployments).

---

### **Why Are ImageStreams Useful When We Already Have Quay?**

Quay is just a **warehouse** where your images live. It provides storage and distribution, but it doesn’t do much beyond that. Here’s why ImageStreams add value:

1. **Tracking Changes:**
   If a new version of your app (image) is pushed to Quay, Quay doesn’t notify your application to use the new version. An ImageStream in OpenShift monitors these changes automatically and helps trigger actions (e.g., redeployments) when needed.

2. **Tag Management:**
   Suppose your app has two environments: production (`stable`) and development (`latest`). ImageStreams let you handle tags efficiently:
   - `stable`: Points to version 1.2 of the app
   - `latest`: Points to version 2.0, still under testing

   You can update `stable` later without disrupting production workflows.

3. **Integration with OpenShift Workflows:**
   OpenShift tightly integrates ImageStreams into its ecosystem:
   - Builds can use ImageStreams to fetch base images or dependencies.
   - Deployments tied to ImageStreams automatically react to updates.

---

### **Use Case Example for Better Understanding**

#### Scenario 1: A Simple Web App
You are running a web app called `myapp`. You store its image in Quay (`quay.io/myorg/myapp:v1.0`). When deploying, you don’t want to hardcode `v1.0` because:
   - You might want to test `v1.1` in development.
   - When `v1.1` becomes stable, you want production to automatically switch without updating configurations manually.

   **Solution**: Use an ImageStream to point to `quay.io/myorg/myapp`. The app deployment will rely on the ImageStream tag (`latest` or `stable`) to decide which version to run.

---

#### Scenario 2: Continuous Integration/Continuous Deployment (CI/CD)
You’ve set up a CI/CD pipeline where:
   - Developers push updates to `myapp`.
   - A new image is built and pushed to Quay after successful tests.
   - Production should automatically redeploy with the new image.

   **Problem**: Quay has no mechanism to notify OpenShift to redeploy.  
   **Solution**: ImageStreams monitor Quay for updates, detect the new image version, and trigger redeployments or builds.

---

### **Summary of ImageStreams**

- **Analogy**: A menu pointing to ingredients (Quay images) but with dynamic updates when ingredients change.
- **Why Needed**: Quay is just storage. ImageStreams enable automatic tracking, versioning, and seamless integration into OpenShift workflows.
- **Use Cases**: Dynamic deployments, version management, and CI/CD automation.  

You're absolutely correct! If you've already created and linked the ImageStream using the `oc import-image` command, running it again is unnecessary unless you want to manually re-import the image. Here's the corrected workflow:

---

### **Creating and Linking an ImageStream**

1. Create and link the ImageStream in one step:
   ```bash
   oc import-image myapp --from=quay.io/myorg/myapp:latest --confirm
   ```

   This sets up the ImageStream `myapp` and links it to the image `quay.io/myorg/myapp:latest`. OpenShift will now track this image.

---

### **Automatically Trigger Pod Restarts**

1. If a new image version becomes available in Quay, you can **update the ImageStream tags** (if needed):
   ```bash
   oc tag quay.io/myorg/myapp:2.0 myapp:latest
   ```

2. Pods will restart automatically if your Deployment references the ImageStream tag (`myapp:latest`) and OpenShift detects the new image.

---

### **Confirm Pods Restart**

Verify that pods with the label `app=myapp` are restarted after the update:
```bash
oc get pods -l app=myapp
```

Here’s the complete setup for the **ImageStream**, **Deployment**, and **values.yaml** file in a Helm chart, along with an explanation.

---

### **ImageStream YAML**
This defines the ImageStream that OpenShift uses to track your external image.

```yaml
apiVersion: image.openshift.io/v1
kind: ImageStream
metadata:
  name: {{ .Values.imageStream.name }}
  labels:
    app: {{ .Values.app.name }}
spec:
  tags:
    - name: {{ .Values.imageStream.tag }}
      from:
        kind: DockerImage
        name: {{ .Values.imageStream.image }}
      importPolicy:
        scheduled: {{ .Values.imageStream.importPolicy }}
```

### Explanation:
- `name`: The ImageStream's name, referenced in the Deployment.
- `tags.name`: The tag (`latest`) for the ImageStream.
- `from.name`: The full external image (e.g., `quay.io/myorg/myapp:latest`).
- `importPolicy.scheduled`: Ensures the ImageStream periodically checks for updates to the external image.

---

### **Deployment YAML**
This defines the application Deployment that uses the ImageStream.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Values.deployment.name }}
spec:
  replicas: {{ .Values.deployment.replicas }}
  selector:
    matchLabels:
      app: {{ .Values.app.name }}
  template:
    metadata:
      labels:
        app: {{ .Values.app.name }}
    spec:
      containers:
      - name: {{ .Values.app.name }}
        image: {{ .Values.imageStream.name }}:{{ .Values.imageStream.tag }}
        imagePullPolicy: Always
```

### Explanation:
- `image`: Refers to the ImageStream by name (`myapp`) and tag (`latest`), not the external registry.
- OpenShift resolves `myapp:latest` to the actual image URL (e.g., `quay.io/myorg/myapp:latest`) defined in the ImageStream.

---

### **values.yaml**
The `values.yaml` file contains parameters for the Helm chart.

```yaml
app:
  name: myapp

imageStream:
  name: myapp
  tag: latest
  image: quay.io/myorg/myapp:latest
  importPolicy: true

deployment:
  name: myapp-deployment
  replicas: 2
```

---

### **How It All Works**

1. **ImageStream**:
   - The ImageStream `myapp` tracks the external image `quay.io/myorg/myapp:latest`.
   - The `latest` tag in the ImageStream represents the latest version of the external image.

2. **Deployment**:
   - The `image` field in the Deployment references the ImageStream by name (`myapp`) and tag (`latest`), not the full external registry path.
   - When the ImageStream detects a new version of the external image, OpenShift updates the ImageStream and triggers the Deployment to redeploy pods.

3. **Dynamic Updates**:
   - This setup allows OpenShift to fetch and deploy the latest image from `quay.io` without hardcoding the external image URL in the Deployment. Instead, OpenShift resolves the reference via the ImageStream.

This design keeps your Deployment decoupled from the external image registry, providing flexibility and automation.

---

example:

```yml
kind: ImageStream
apiVersion: image.openshift.io/v1
metadata:
  name: vofe-aa-tuc-dev
  namespace: 015566-vopf01-tuc
  uid: 92b37049-5537-4f6c-a62a-de1b9aaf2fc7
  resourceVersion: '2923462160'
  generation: 7
  creationTimestamp: '2025-01-13T08:51:46Z'
  annotations:
    openshift.io/image.dockerRepositoryCheck: '2025-01-13T09:30:39Z'
spec:
  lookupPolicy:
    local: false
  tags:
    - name: dev
      annotations: null
      from:
        kind: DockerImage
        name: 'quay.apps.cloud.internal/015566-vopf/vofe-aa:dev'
      generation: 7
      importPolicy:
        scheduled: true
        importMode: Legacy
      referencePolicy:
        type: Source
```

```bash
oc delete is vofe-aa-tuc-test
 
oc import-image vofe-aa-tuc-dev --from=quay.apps.cloud.internal/015566-vopf/vofe-aa:dev --confirm
 
oc delete pod -l app=vofe-aa // not needed will auto restart
```