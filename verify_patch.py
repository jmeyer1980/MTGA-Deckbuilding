import os
patch = r"C:\Users\jerio\RiderProjects\MTGA Deckbuilding\mulligan-patch-v2.txt"
if os.path.exists(patch):
    txt = open(patch, encoding="utf-8", errors="replace").read()
    print("patch exists, lines:", txt.count(chr(10)) + 1)
    print("Fabled Passage in patch:", "Fabled Passage" in txt)
    i = txt.find("const landVal")
    print(txt[i-50:i+350].replace(chr(10), " | "))
else:
    print("patch NOT found at", patch)

# Is node available?
import subprocess
r = subprocess.run(["node", "--version"], capture_output=True, text=True)
print("node:", r.stdout.strip() or r.stderr.strip())
