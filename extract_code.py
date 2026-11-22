import os

output_file = "all_code.txt"
with open(output_file, "w", encoding="utf-8") as outfile:
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith((".py", ".html", ".js", ".css")):
                filepath = os.path.join(root, file)
                outfile.write(f"\n\n--- File: {filepath} ---\n")
                with open(filepath, "r", encoding="utf-8", errors="ignore") as infile:
                    outfile.write(infile.read())
