import os
import subprocess
import sys
import time

home = "/home/broyojo/"

groups = [
    "main",
    "extra",
]

backups = "backups"
custom_icons = "webserver/custom_icons"
render_dir = "webserver/render"


def list_servers(group):
    return os.listdir(group)


def send_keys(session, keys):
    os.system(f"tmux send-keys -t {session} '{keys}' C-m")


def say(server, msg):
    send_keys(
        server,
        f'tellraw @a {{"text":"{msg}","color":"red","bold":true}}',
    )


def list_sessions():
    stdout = subprocess.run(["tmux", "ls"], stdout=subprocess.PIPE).stdout
    lines = str(stdout).split("\\n")[:-1]
    if len(lines) == 0:
        return []
    names = [a[: a.index(":")] for a in lines]
    names[0] = names[0][2:]
    return names


def perform_task(task, *names):
    if len(names) == 0:
        for group in groups:
            for server in list_servers(group):
                task(group, server)

    for name in names:
        # do task on all servers in a single group
        if name in groups:
            for server in list_servers(name):
                task(name, server)
            continue

        # search through all groups to do task on a single server
        for group in groups:
            if name in list_servers(group):
                task(group, name)
                break
        else:
            print(f":: Server or group '{name}' does not exist. Skipping...")


def start_server(group, server):
    if server in list_sessions():
        print(f":: Server '{server}' already started. Skipping...")
        return

    print(f":: Starting server '{server}'...")

    os.system(f"tmux new -s {server} -c '{os.path.join(home, group, server)}' -d")

    send_keys(server, "./start.sh")


def start(*names):
    perform_task(start_server, *names)


def backup_server(group, server):
    backup_cmd = f'tar -zcvf {backups}/"{server}-$(TZ=America/New_York date +%Y-%m-%d).gz" {os.path.join(home, group, server)}'

    print(f":: Backing up server '{server}'...")

    if server in list_sessions():
        # server is currently active
        say(server, "Backing up server...")
        send_keys(server, "save-off")
        send_keys(server, "save-all")
        os.system(backup_cmd)
        say(server, "Backing completed")
        send_keys(server, "save-on")
    else:
        # server is not active
        os.system(backup_cmd)

    print(f":: Backup of '{server}' completed")


def backup(*names):
    perform_task(backup_server, *names)


def render_server(group, server):
    print(f":: Rendering server '{server}'...")

    server_dir = os.path.join(home, group, server, "world")
    copied_dir = os.path.join(os.path.join(home, "tmp"), server)

    if server in list_sessions():
        # server is active
        say(server, "Copying world file...")
        print(f":: Copying '{server}' world file...")
        send_keys(server, "save-off")
        send_keys(server, "save-on")
        os.system(f"rsync -avz --delete {server_dir} {copied_dir}")
        say(server, "Finished copying world file")
        print(f":: Finished copying '{server}' world file")
        send_keys(server, "save-on")
    else:
        # server is not active
        print(f":: Copying '{server}' world file...")
        os.system(f"rsync -avz --delete {server_dir} {copied_dir}")
        print(f":: Finished copying '{server}' world file")

    with open("render_config.py", "a") as f:
        f.write(
            f"""worlds["{server}"] = "{os.path.join(copied_dir, 'world')}"

renders["{server}day"] = {{
    "world": "{server}",
    "title": "Overworld",
    "rendermode": smooth_lighting,
    "dimension": "overworld",
    "markers": [dict(name="Markers", filterFunction=signFilter)],
}}

renders["{server}nether"] = {{
    "world": "{server}",
    "title": "Nether",
    "rendermode": normal,
    "dimension": "nether",
    "markers": [dict(name="Markers", filterFunction=signFilter)],
}}

renders["{server}end"] = {{
    "world": "{server}",
    "title": "End",
    "rendermode": [Base(), EdgeLines(), SmoothLighting(strength=0.5)],
    "dimension": "end",
    "markers": [dict(name="Markers", filterFunction=signFilter)],
}}

"""
        )
    say(server, "Starting render...")
    print(f":: Starting render of '{server}'...")


def render(*names):
    with open("render_config.py", "w+") as f:
        f.write(
            f"""processes = 4

def signFilter(poi):
    if poi['id'] == "Sign" or poi["id"] == "minecraft:sign":
        data = poi["Text1"] + poi["Text2"] + poi["Text3"] + poi["Text4"]
        if len(data) >= 2:
            if data[0] == data[-1] == "*":
                print("found marker")
                print(data)
                args = data.split(";")
                hover, text = "", ""
                for arg in args:
                    arg = arg.strip().strip("*")
                    ident, val = "", ""
                    try:
                        ident, val = arg.split(":")
                    except:
                        return None
                    if ident == "i":
                        print(val)
                        poi["icon"] = f"custom_icons/{{val}}.png"
                    elif ident == "t":
                        text = val
                    elif ident == "h":
                        hover = val
                    else:
                        print(f"unknown identifier {{ident}}")
                print("hover:", hover)
                print("text:", text)
                return (hover, text)

customwebassets = "{os.path.join(home, custom_icons)}"
outputdir = "{os.path.join(home, render_dir)}"

"""
        )

    perform_task(render_server, *names)

    os.system("overviewer.py --config=render_config.py")
    os.system("overviewer.py --config=render_config.py --genpoi")

    os.remove("render_config.py")

    print(":: Render completed")  # TODO: add 'say' command for each rendered server


def main():
    args = sys.argv[1:]

    if len(args) == 0:
        print("Running servers:")
        sessions = list_sessions()
        for session in sessions:
            print(session)
        print("Total number of running servers:", len(sessions))
        return

    match args[0]:
        case "start":
            start(*args[1:])
        case "backup":
            backup(*args[1:])
        case "render":
            render(*args[1:])
        case "schedule":
            import schedule

            schedule.every(1).days.at("05:00").do(backup, "extra")
            schedule.every(7).days.at("06:00").do(render, "extra")

            while True:
                schedule.run_pending()
                time.sleep(30)
        case _:
            print(":: Invalid command")


if __name__ == "__main__":
    main()
