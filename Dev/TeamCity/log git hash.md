Here is the complete set of steps to add the `GIT_COMMIT_HASH` to your Docker builds using TeamCity and ensure it is logged at runtime:

---

### **Step 1: Capture the Git Commit Hash in TeamCity**
TeamCity automatically provides the Git commit hash through the build parameter `%build.vcs.number%`. This represents the commit hash of the current VCS root.

- If you have multiple VCS roots, use the specific VCS root ID: `%build.vcs.number.<VCS Root ID>%`.

---

### **Step 2: Modify the Docker Build Configuration in TeamCity**
In the TeamCity build step for your Docker build, do the following:

1. Open the Docker build configuration in your TeamCity project.
2. Locate the **Additional arguments for the command** field.
3. Add the following argument to pass the Git commit hash as a build argument:
   ```text
   --build-arg GIT_COMMIT_HASH=%build.vcs.number%
   ```

This ensures that the `GIT_COMMIT_HASH` argument is passed to the Docker build process.

---

### **Step 3: Update the Dockerfile**
Modify your `Dockerfile` to accept and use the `GIT_COMMIT_HASH` argument.

1. Add a `GIT_COMMIT_HASH` build argument:
   ```dockerfile
   ARG GIT_COMMIT_HASH
   ```

2. Set it as an environment variable:
   ```dockerfile
   ENV GIT_COMMIT_HASH=${GIT_COMMIT_HASH}
   ```

3. (Optional) Use it in your image to generate a `git.properties` file for reference:
   ```dockerfile
   RUN echo "git.commit.id=${GIT_COMMIT_HASH}" > /app/git.properties
   ```

This setup embeds the commit hash into the Docker image.

---

### **Step 4: Log the Commit Hash in Your Application**
Make your application log the `GIT_COMMIT_HASH` at runtime.

#### Spring Boot Example
1. Inject the `GIT_COMMIT_HASH` environment variable into your application:

   ```java
   @Value("${GIT_COMMIT_HASH:unknown}")
   private String gitCommitHash;
   ```

2. Log the value at startup:

   ```java
   import org.slf4j.Logger;
   import org.slf4j.LoggerFactory;
   import org.springframework.boot.CommandLineRunner;
   import org.springframework.stereotype.Component;

   @Component
   public class GitCommitLogger implements CommandLineRunner {

       private static final Logger logger = LoggerFactory.getLogger(GitCommitLogger.class);

       private final String gitCommitHash;

       public GitCommitLogger(@Value("${GIT_COMMIT_HASH:unknown}") String gitCommitHash) {
           this.gitCommitHash = gitCommitHash;
       }

       @Override
       public void run(String... args) {
           logger.info("Running application with Git commit hash: {}", gitCommitHash);
       }
   }
   ```

When the application starts, it will log the Git commit hash, confirming the image source.

---

### **Step 5: Verify at Runtime**
Once the Docker build is complete:

1. Deploy the Docker image.
2. Check the application logs to confirm the Git commit hash is logged:
   ```
   Running application with Git commit hash: abc1234
   ```

---

### **Step 6: Validate in TeamCity Logs**
Check the build logs in TeamCity to ensure the correct `GIT_COMMIT_HASH` was passed to the Docker build.

1. Open the build log in TeamCity.
2. Look for the Docker build command:
   ```
   docker build --build-arg GIT_COMMIT_HASH=abc1234 -t your-image-name .
   ```

This confirms that the correct commit hash was passed and used in the build.

---

### Summary
1. **In TeamCity**:
   - Add `--build-arg GIT_COMMIT_HASH=%build.vcs.number%` to the Docker build step.
2. **In Dockerfile**:
   - Accept `ARG GIT_COMMIT_HASH` and set it as `ENV GIT_COMMIT_HASH`.
3. **In Application**:
   - Log the `GIT_COMMIT_HASH` at runtime.
4. **Verify Logs**:
   - Confirm the commit hash is logged in the application and TeamCity build logs.