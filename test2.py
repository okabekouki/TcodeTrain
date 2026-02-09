import getpass
import msvcrt

def sel() :
    while True:
        sel = msvcrt.getch()
        if sel == b" ":
            return sel

a = sel()
print (a)

# while文が終了するタイミングではselにはスペースしか入っていない。