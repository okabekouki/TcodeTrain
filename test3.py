import tkinter as tk

def Space(Event=None):
    global aCh
    aCh = Disp1.get()
    L1.config(text=f"Your Answer: {aCh}")
    entry.delete(0, tk.END)



root = tk.Tk()

Disp1 = tk.StringVar()
Disp2 = tk.StringVar()
aCh = ""

entry = tk.Entry(root, textvariable=Disp1, width=30)
entry.pack()

L1 = tk.Label(root, text="")
L1.pack()


root.bind('<space>', Space)
root.mainloop()