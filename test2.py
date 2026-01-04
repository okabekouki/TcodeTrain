import curses
stdscr = curses.initscr()

while True:
    c = stdscr.getch()
    if c == ord('\x03'):
        print ("You pressed 'd'!")
        break
    else :
        print ("You pressed another key.")
        break
