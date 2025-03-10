import subprocess

src = r"/home/damian/Projekty/Projekt_Inzynierski-2025/src/conf/volumes/tasks"
volume = r"/var/lib/docker/volumes/conf_tasks_volume/_data"

subprocess.run(f"sudo rm -rf {volume}", shell=True, check=True)
subprocess.run(f"sudo mkdir -p {volume}", shell=True, check=True)
subprocess.run(f"sudo cp -R {src}/* {volume}", shell=True, check=True)


src = r"/home/damian/Projekty/Projekt_Inzynierski-2025/src/conf/volumes/submissions"
volume = r"/var/lib/docker/volumes/conf_submissions_volume/_data"

subprocess.run(f"sudo rm -rf {volume}", shell=True, check=True)
subprocess.run(f"sudo mkdir -p {volume}", shell=True, check=True)
subprocess.run(f"sudo cp -R {src}/* {volume}", shell=True, check=True)