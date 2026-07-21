# FreeFileSync + RealTimeSync Notes

## Overview

-   **FreeFileSync** compares and synchronizes folders.
-   **RealTimeSync** watches folders and automatically starts a
    FreeFileSync batch job whenever files change.

Typical workflow:

    Folder A <----> FreeFileSync <----> Folder B
                         ^
                         |
                   RealTimeSync
                 (watches folders)

------------------------------------------------------------------------

# 1. Create a Sync Job

1.  Open **FreeFileSync**.
2.  Select the source folder on the left.
3.  Select the destination folder on the right.
4.  Choose the synchronization mode.
5.  Click **Compare**.
6.  Review the planned changes.
7.  Click **Synchronize** to test.

------------------------------------------------------------------------

# 2. Synchronization Modes

## Mirror

-   Left folder is the master.
-   Right folder becomes an exact copy.
-   Files deleted on the left are deleted on the right.

Use for: - Backups - Obsidian vault backup - One-way synchronization

## Update

-   Copies only new and modified files.
-   Does not delete existing files on the destination.

Use for: - Incremental backups

## Two Way

-   Both folders are treated equally.
-   Changes on either side are synchronized.

Use for: - Working from both folders.

------------------------------------------------------------------------

# 3. Save the Configuration

After testing:

**File → Save As**

Recommended:

-   **.ffs_batch**

Reason: - Can run automatically. - No confirmation dialogs. - Used by
RealTimeSync.

------------------------------------------------------------------------

# 4. Automatic Synchronization

1.  Open **RealTimeSync**.
2.  Open or drag the `.ffs_batch` file.
3.  Set a delay (recommended: **5--10 seconds**).
4.  Click **Start**.

RealTimeSync now watches the folders.

Whenever a file changes:

-   waits for the configured delay
-   launches the FreeFileSync batch job
-   synchronizes the folders automatically

------------------------------------------------------------------------

# 5. Recommended Settings

For an Obsidian vault:

-   Source: Local vault
-   Destination: Cloud folder
-   Mode: Mirror
-   Delay: 5--10 seconds

------------------------------------------------------------------------

# 6. Common Problems

## "contains no valid configuration"

Cause: - Empty or invalid `.ffs_gui` file.

Fix:

1.  Configure both folders.
2.  Save again.
3.  Prefer saving as `.ffs_batch`.

------------------------------------------------------------------------

## Synchronization does not start automatically

Check:

-   RealTimeSync is running.
-   The `.ffs_batch` file exists.
-   Folder permissions are granted.
-   The watched folders still exist.

------------------------------------------------------------------------

# 7. Suggested Workflow

    Edit files
          ↓
    RealTimeSync detects change
          ↓
    Wait 5–10 seconds
          ↓
    Run .ffs_batch
          ↓
    Folders synchronized
