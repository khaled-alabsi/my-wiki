On macOS, the cleanest option is to create a small **Automator app** that runs your `code-personal` script. Then you can put it in Dock, Spotlight, or Launchpad like a normal app.

## Step 0: Create the script file first

Before touching Automator, make sure the script itself actually exists as a **file** (not a directory — e.g. don't `mkdir ~/bin/code-personal` by mistake).

```bash
mkdir -p ~/bin
```

Create `~/bin/code-personal` with this content (use your editor, or run this in Terminal):

```bash
cat > ~/bin/code-personal << 'EOF'
#!/bin/bash

open -n -a "Visual Studio Code" --args \
  --user-data-dir "$HOME/.vscode-personal-data" \
  --extensions-dir "$HOME/.vscode-personal-extensions" \
  "$@"
EOF
```

Then make it executable:

```bash
chmod +x ~/bin/code-personal
```

Verify it's a file (not a directory) and runs:

```bash
file ~/bin/code-personal   # should say "Bourne-Again shell script"
~/bin/code-personal        # should open VS Code
```

Only once this works from Terminal should you move on to wrapping it in Automator.

## Step 1: Wrap it in an Automator app

Open **Automator**:

```text
Cmd + Space → Automator
```

Choose:

```text
Application
```

Then search for:

```text
Run Shell Script
```

Drag it into the workflow.

Set shell to:

```text
/bin/bash
```

Put this inside:

```bash
/Users/Khaled.Alabsi/bin/code-personal
```

Replace `YOUR_USERNAME` with your macOS username.

You can also use this safer version:

```bash
"$HOME/bin/code-personal"
```

Then save it as:

```text
VS Code Personal.app
```

For example, save it in:

```text
/Applications/VS Code Personal.app
```

Now you can open it from Spotlight:

```text
Cmd + Space → VS Code Personal
```

Or drag it to the Dock.

Your setup becomes:

```text
Default VS Code app       → enterprise GitHub account
VS Code Personal.app      → personal GitHub account
```

One issue: if you launch from Automator, `$@` will usually be empty, so it just opens VS Code Personal without a folder. That is fine for Dock/Spotlight usage. For opening a specific folder, use Terminal:

```bash
~/bin/code-personal ~/projects/my-project
```
