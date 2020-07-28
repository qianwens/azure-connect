import runpy
import threading
import time
import os
import webbrowser

def runServer():

    def startBrowser():
        time.sleep(5)
        print("Open browser at http://127.0.0.1:8000/")
        webbrowser.open("http://127.0.0.1:8000/")

    t = threading.Thread(target=startBrowser)
    t.start()

    try:
        os.system("python manage.py runserver")
    except:
        pass
