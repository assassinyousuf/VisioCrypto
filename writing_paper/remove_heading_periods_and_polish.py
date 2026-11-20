import os, re

tex_path = r"e:\_PROJECTS\visiocrypto\writing_paper\paper_ieee.tex"
with open(tex_path, "r", encoding="utf-8") as f:
    tex = f.read()

# Update Abstract padding sentence
tex = tex.replace(
    "Padding adds about fifty percent overhead, easily fitting on modern mobile storage.",
    "The extra index entries take up barely a few megabytes on flash storage."
)

# Remove trailing periods from sections and subsections
tex = re.sub(r'\\section\{([^}]+)\.\}', r'\\section{\1}', tex)
tex = re.sub(r'\\subsection\{([^}]+)\.\}', r'\\subsection{\1}', tex)

with open(tex_path, "w", encoding="utf-8") as f:
    f.write(tex)
print("Removed trailing periods from section/subsection headers and updated abstract padding sentence!")
