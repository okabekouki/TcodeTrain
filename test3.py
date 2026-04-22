import tkinter as tk
import test3Base as base

# ===== 状態 =====
STATE_MODE = 0
STATE_LEVEL1 = 1
STATE_LEVEL2 = 2
STATE_QUIZ = 3

state = STATE_MODE

mode = None
val1 = None
val2 = None

Chlist = None
qCh = None

def KeyInput(Event):
    global state, mode

    if state != STATE_MODE:
        return

    if Event.char == "d":
        mode = "d"
        Disp1.set("")
        state = STATE_LEVEL1
        updateGuide()

    elif Event.char == "k":
        mode = "k"
        Disp1.set("")
        state = STATE_LEVEL1
        updateGuide()

def nextQuestion():
    global qCh
    qCh = base.makeQuestion(Chlist)
    if qCh is None:
        Lq.config(text="No Question")
    else:
        Lq.config(text=f"Question: {qCh}")


def updateGuide():
    if state == STATE_MODE:
        Lguide.config(text="Select Mode: d=Difficulty / k=Lesson")
    elif state == STATE_LEVEL1:
        if mode == "d":
            Lguide.config(text="Input Min Difficulty")
        else:
            Lguide.config(text="Input Min Lesson")
    elif state == STATE_LEVEL2:
        if mode == "d":
            Lguide.config(text="Input Max Difficulty")
        else:
            Lguide.config(text="Input Max Lesson")
    elif state == STATE_QUIZ:
        Lguide.config(text="Type answer and press SPACE")


def Space(Event=None):
    global state, mode, val1, val2, Chlist

    text = Disp1.get().strip()

    # ===== モード選択 =====
    if state == STATE_MODE:
        return

    
    # ===== 最小値入力 =====
    elif state == STATE_LEVEL1:
        if text.isdigit():
            val1 = int(text)
            Disp1.set("")
            state = STATE_LEVEL2
        else:
            L1.config(text="Enter number")

    # ===== 最大値入力 =====
    elif state == STATE_LEVEL2:
        if text.isdigit():
            val2 = int(text)
            if val2 < val1:
                L1.config(text="Max must be >= Min")
            else:
                if mode == "d":
                    Chlist = base.makeChList(val1, val2)
                else:
                    Chlist = base.makeChList_les(val1, val2)

                if Chlist is None:
                    L1.config(text="No Data Found")
                else:
                    Disp1.set("")
                    state = STATE_QUIZ
                    nextQuestion()
        else:
            L1.config(text="Enter number")

    # ===== クイズ =====
    elif state == STATE_QUIZ:
        aCh = text
        uaNum = base.Chnum(aCh)
        caNum = base.getCorrectNum(qCh)

        L1.config(text=f"Your: {uaNum}")

        if uaNum == caNum:
            L2.config(text=f"Answer: {caNum}", fg="green")
        else:
            L2.config(text=f"Answer: {caNum}", fg="red")

        Disp1.set("")
        nextQuestion()

    updateGuide()


root = tk.Tk()
root.geometry("300x200")
Disp1 = tk.StringVar()

FONT = ("Consolas", 10)

entry = tk.Entry(root, textvariable=Disp1, width=30, show="*", font=FONT)
entry.pack(pady=10)

Lguide = tk.Label(root, text="", font=FONT)
Lguide.pack(pady=10)

Lq = tk.Label(root, text="", font=FONT)
Lq.pack(pady=10)

L1 = tk.Label(root, text="", font=FONT)
L1.pack(pady=10)

L2 = tk.Label(root, text="", font=FONT)
L2.pack(pady=10)

root.bind('<space>', Space)
root.bind('<Key>', KeyInput)

updateGuide()

root.mainloop()