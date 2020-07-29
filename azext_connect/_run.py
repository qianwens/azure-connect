from azure.common.client_factory import get_client_from_cli_profile
from azure.mgmt.web import WebSiteManagementClient
import paramiko
import threading
import time
import sys
from ._tunnel import TunnelServer
from knack.log import get_logger
from datetime import datetime, timedelta

logger = get_logger(__name__)


def run_ssh(resource_group_name, webapp_name, commands=None):
    app_service_client : WebSiteManagementClient = get_client_from_cli_profile(WebSiteManagementClient)

    poller = app_service_client.web_apps.list_publishing_credentials(resource_group_name=resource_group_name, name=webapp_name)
    cred = poller.result()
    userName = cred.publishing_user_name
    userPwd = cred.publishing_password
    url = "https://{}.scm.azurewebsites.net".format(webapp_name)
    port = 443

    tunnel_server = TunnelServer("", 0, url, userName, userPwd)
    _wait_for_webapp(tunnel_server)
    local_port = tunnel_server.local_port
    t = threading.Thread(target=_start_tunnel, args=(tunnel_server,))
    t.daemon = True
    t.start()
    print("Bind with local port:{}".format(local_port))

    ssh : paramiko.SSHClient = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    wait_time = datetime.now()
    while True:
        try:
            ssh.connect(hostname="localhost", port=local_port, username="root", password="Docker!")
            break
        except:
            if wait_time + timedelta(seconds=30) < datetime.now():
                raise
            time.sleep(3)

    channel : paramiko.Channel=ssh.invoke_shell()
    if commands:
        run_commands(channel, commands)
    else:
        windows_shell(channel)
    channel.close()
    ssh.close()


def run_commands(chan, commands):
    wait_time = datetime.now()
    has_output = False
    def writeall(sock):
        while True:
            nonlocal wait_time
            nonlocal has_output
            wait_time = datetime.now()
            data = sock.recv(256)
            has_output = True
            if not data:
                sys.stdout.write("\r\n*** EOF ***\r\n\r\n")
                sys.stdout.flush()
                break
            try:
                decoded_data = data.decode()
                sys.stdout.write(decoded_data)
            except:
                pass
            sys.stdout.flush()

    writer = threading.Thread(target=writeall, args=(chan,))
    writer.start()

    import time
    while True:
        time.sleep(1)
        if has_output:
            break
    time.sleep(2)
    for d in commands:
        chan.send(d + "\n")

    while True:
        time.sleep(1)
        if wait_time + timedelta(seconds=30) < datetime.now():
            break


# thanks to Mike Looijmans for this code
def windows_shell(chan):
    sys.stdout.write(
        "Line-buffered terminal emulation. Press F6 or ^Z to send EOF.\r\n\r\n"
    )

    def writeall(sock):
        while True:
            data = sock.recv(256)
            if not data:
                sys.stdout.write("\r\n*** EOF ***\r\n\r\n")
                sys.stdout.flush()
                break
            try:
                decoded_data = data.decode()
                sys.stdout.write(decoded_data)
            except:
                pass
            sys.stdout.flush()

    writer = threading.Thread(target=writeall, args=(chan,))
    writer.start()

    try:
        while True:
            d = sys.stdin.read(1)
            if not d:
                break
            chan.send(d)
    except EOFError:
        # user hit ^Z or F6
        pass


def _wait_for_webapp(tunnel_server:TunnelServer):
    tries = 0
    while True:
        if tunnel_server.is_webapp_up():
            break
        if tries == 0:
            logger.warning('Connection is not ready yet, please wait')
        if tries == 60:
            raise CLIError('SSH timeout, your app must be running before'
                           ' it can accept SSH connections. '
                           'Use `az webapp log tail` to review the app startup logs.')
        tries = tries + 1
        logger.warning('.')
        time.sleep(1)


def _start_tunnel(tunnel_server):
    tunnel_server.start_server()
