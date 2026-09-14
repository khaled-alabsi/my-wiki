The **Registry ID** in TeamCity is a unique identifier automatically assigned to a Docker registry connection you configure in the TeamCity administration panel. This ID is used in your Kotlin DSL scripts to reference the registry connection.

Here’s a step-by-step guide for setting up the connection and adding your Quay username and password:

---

### **Step 1: Add a Docker Registry Connection**
1. **Go to TeamCity Administration Panel:**
   - Navigate to **Administration > Connections > Docker Registry Connections**.

2. **Add a New Registry:**
   - Click on **+ Add Connection** and select **Docker Registry**.

3. **Configure the Connection for Quay:**
   - **Registry Type:** Docker
   - **Registry URL:** `https://quay.io`
   - **Username:** Enter your Quay username.
   - **Password/Token:** Enter your Quay account password or an access token generated from Quay.

4. **Save the Connection:**
   - TeamCity will test the connection. If successful, it will save the registry connection and assign it a unique **Registry ID**.

---

### **Step 2: Use the Registry Connection in Build Configurations**
1. After saving, TeamCity will assign a unique identifier to the registry connection (e.g., `QuayRegistry_1`).
   - You can find this ID in the **Docker Registry Connections** list under Administration.

2. Use this `Registry ID` in your Kotlin DSL script:
   ```kotlin
   dockerSupport {
       cleanupPushedImages = true
       loginToRegistry = on {
           dockerRegistryId = "QuayRegistry_1" // Replace with the actual ID
       }
   }
   ```

---

### **Alternative: Add Username and Password in Build Parameters**
If you prefer, you can also manage credentials using TeamCity build parameters:
1. Go to your build configuration.
2. Add two secure parameters:
   - `docker.username`: Your Quay username.
   - `docker.password`: Your Quay password or token.

3. Reference these in the Docker-related steps (if not using the Docker Registry Connections feature directly).

---

### **Best Practices**
- Always use secure parameters for sensitive data like passwords or tokens.
- Use Quay **robot accounts** or tokens for automation rather than personal credentials.

If you follow these steps, your Quay registry connection should work seamlessly with TeamCity.

---

I understand you're having trouble locating the **Connections** tab within the **Administration** section of TeamCity. This tab is essential for configuring connections to external services, such as Docker registries like Quay.

**Accessing the Connections Tab:**

1. **Navigate to Your Project Settings:**
   - In the TeamCity web interface, click on the **Projects** link in the top navigation bar to view all projects.
   - Select the specific project where you want to add the Docker registry connection.

2. **Access the Connections Tab:**
   - Within the selected project's settings, look for the **Connections** tab in the sidebar. This tab allows you to manage connections to external services, including Docker registries.

**If the Connections Tab is Missing:**

- **Permissions:** Ensure that your user account has the necessary permissions to view and modify project settings. Lack of appropriate permissions can hide certain configuration options.

- **TeamCity Version:** The availability of the **Connections** tab depends on the TeamCity version. In some versions, this feature might be located elsewhere or may not be available. For instance, in certain versions, Docker registry connections are configured under **Project Settings** > **Connections**. 

- **Alternative Configuration:** If the **Connections** tab is unavailable, you can configure Docker registry connections directly in your build configurations:

  1. **Edit Build Configuration:**
     - Go to the build configuration where you want to add the Docker registry connection.
     - Navigate to the **Build Features** section.

  2. **Add Docker Support:**
     - Click on **Add Build Feature** and select **Docker Support**.
     - In the Docker Support settings, you can specify the Docker registry URL, username, and password directly.

  3. **Save Configuration:**
     - Save the build feature settings to apply the Docker registry connection to your build configuration.

**Additional Resources:**

- For detailed instructions on configuring Docker connections in TeamCity, refer to the official documentation: 

If you continue to experience difficulties, please provide your TeamCity version and any error messages or screenshots. This information will help in diagnosing the issue more precisely. 