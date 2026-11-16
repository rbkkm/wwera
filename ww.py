import subprocess, sys, time, math

# Het pad naar je script
script = "d:/gthb/py/e/wwera.py"
# script = "/py/reagm.py"

# Start processen
processen = []
for i in range(8):
    p = subprocess.Popen(["python3", script])
    processen.append(p)
    time.sleep(360)
