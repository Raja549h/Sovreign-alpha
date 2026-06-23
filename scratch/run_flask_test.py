import subprocess
with open("scratch/err2.txt", "w") as f:
    subprocess.run(["python", "-u", "scratch/test_flask.py"], stdout=f, stderr=f)
