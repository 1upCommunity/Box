import os, threading, time, subprocess

running = True
index = 0
chars = ('-', '\\', '|', '/')

def spin(text):
    time.sleep(.1)
    global index
    while running:
        print('\r' + text + chars[index], end='')
        index += 1
        if index == len(chars):
            index = 0
        time.sleep(.1)

def display_spinner_while(text, function):
    threading.Thread(target=spin, args=(text,)).start()
    function()
    global running
    running = False
    
def pull():
    os.system('git pull')
    
display_spinner_while('Updating repository ', pull)
print('\r Update complete!')

def doit_windows():
    subprocess.call(['depinstaller.bat'])

def doit_mac_linux():
    subprocess.call(['sudo', 'depinstaller.sh'])

if __name__ == '__main__':
    os_name = os.name
    if os_name == 'nt':
        display_spinner_while('Installing dependencies ', doit_windows)
        time.sleep(1)
        print('\r Installed dependencies')
        os.system('python __main__.py')
    elif os_name == 'posix':
        display_spinner_while('Installing dependencies ', doit_mac_linux)
        time.sleep(1)
        print('\r Installed dependencies')
        os.system('python3 __main__.py')
    else:
        display_spinner_while('Installing dependencies ', doit_mac_linux)
        time.sleep(1)
        print('\r Installed dependencies')
        os.system('python3 __main__.py')
