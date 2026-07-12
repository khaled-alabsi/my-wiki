import os
import re


def saveFile(directory, fileName, content, type=".md"):
    os.makedirs(directory, exist_ok=True)
    safe_filename = re.sub(r'[\/:*?"<>|]', " ", fileName)
    filepath = os.path.join(directory, safe_filename+type)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
