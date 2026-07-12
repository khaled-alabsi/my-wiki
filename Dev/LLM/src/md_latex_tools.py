import os
import re


def fix_latex(
    path: str, show_changes: bool = False, overwrite_original_file: bool = False
) -> None:
    output_base = "./output"

    # Walk through all files in the directory and subdirectories
    for root, _, files in os.walk(path):
        for file_name in files:
            if file_name.endswith(".md"):
                input_file = os.path.join(root, file_name)

                # Read the content of the markdown file
                with open(input_file, "r", encoding="utf-8") as file:
                    content = file.readlines()

                # Original content for comparison
                original_content = content[:]

                def debug_line(
                    step: int, line_num: int, old: str, new: str
                ) -> None:
                    if show_changes and old != new:
                        print(f"File: {file_name}")
                        print(f"Step {step}, Line {line_num + 1}:")
                        print("Before:")
                        print(old.strip())
                        print("After:")
                        print(new.strip())
                        print("-" * 50)

                # Process each line individually
                for step, (pattern, replacement) in enumerate(
                    [
                        (r"\\\[", "$$"),
                        (r"\\\]", "$$"),
                        (r"\\\(", "$"),
                        (r"\\\)", "$"),
                        (r"(\$\$)(\*\*)", r"\1\n\2"),
                        (r"(\$\$)(###)", r"\1\n\2"),
                        (r"(\$\$)(\S)", r"\1\n\2"),
                        (
                            r"(?<!\S)\$(\s*[^\$]+?\s*)\$(?![\*\.$])",
                            r"$\1$",
                        ),  # Fixed Step 8
                        (r"(?<!\S)\$(?!\s|\$)", r"$"),  # Ensure single $
                        (r"\$(?![\*\.$\s])", r"$ "),  # Ensure space after $
                        (r"\*\* \$(.*?)\$\*\*", r"**$\1$**"),
                    ],
                    start=1,
                ):
                    for i, line in enumerate(content):
                        new_line = re.sub(pattern, replacement, line)
                        debug_line(step, i, line, new_line)
                        content[i] = new_line

                # Inline block to sanitize LaTeX expressions
                latex_pattern = re.compile(r"(\$\s*)(.*?)(\s*\$)")
                for i, line in enumerate(content):
                    new_line = latex_pattern.sub(
                        lambda m: f"${m.group(2).strip()}$", line
                    )
                    debug_line("Sanitize LaTeX", i, line, new_line)
                    content[i] = new_line

                # Check if the content has changed
                if content != original_content:
                    if overwrite_original_file:
                        # Overwrite the original file
                        with open(input_file, "w", encoding="utf-8") as file:
                            file.writelines(content)
                        print(f"File overwritten: {input_file}")
                    else:
                        # Create output folder structure: output_base/test/<relative_path>/file_name
                        relative_path = os.path.relpath(input_file, path)
                        output_file = os.path.join(output_base, relative_path)
                        os.makedirs(os.path.dirname(
                            output_file), exist_ok=True)

                        # Write the updated content to the output folder
                        with open(output_file, "w", encoding="utf-8") as file:
                            file.writelines(content)
                        print(f"File written to: {output_file}")



