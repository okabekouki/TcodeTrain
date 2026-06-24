import tkinter as tk
import test3Base as base
import random

# ===== 状態 =====
STATE_MODE = 0
STATE_LEVEL1 = 1
STATE_LEVEL2 = 2
STATE_QUIZ = 3
STATE_RETRY = 4

state = STATE_MODE

mode = None
val1 = None
val2 = None

Chlist = None
Chdict = None  # 出現確率管理用
qCh = None
excluded_chars = []  # 一時的に除外する文字リスト

def UnifiedKeyInput(Event):
    """統合されたキー入力処理"""
    global state, mode, excluded_chars, qCh

    if state == STATE_MODE:
        excluded_chars.clear()  # モード選択時に除外リストをリセット
        if Event.char == "d":
            mode = "d"
            Disp1.set("")
            state = STATE_LEVEL1
            updateGuide()
            return "break"
        elif Event.char == "k":
            mode = "k"
            Disp1.set("")
            state = STATE_LEVEL1
            updateGuide()
            return "break"

    elif state == STATE_RETRY:
        if Event.char == "a":
            # 同じ問題をもう一度（replay）
            L1.config(text="")
            L2.config(text="")
            state = STATE_QUIZ
            updateGuide()
            return "break"
        elif Event.char == "n":
            # 次の問題へ（前回の除外を解除してから、今回の文字を一時的に除外）
            L1.config(text="")
            L2.config(text="")
            # 前回の除外を解除（次回continue時に戻す）
            if excluded_chars:
                excluded_chars.clear()
            # 今回の問題を一時除外
            if qCh is not None:
                excluded_chars.append(qCh)
            state = STATE_QUIZ
            nextQuestion()
            updateGuide()
            return "break"

def initChdict(Ch):
    """文字リストから出現確率管理用辞書を初期化"""
    Chdict = {}
    for i in Ch:
        Chdict[i] = {"f": 1, "F": 1}
    return Chdict

def selectQuestion(Chdict):
    """出現確率に基づいて問題を選択（除外文字を除く）"""
    # 出現確率を正規化,累積和計算（ローカル変数を使用）
    SumChf = 0
    for k, v in Chdict.items():
        if k not in excluded_chars:  # 除外文字以外を対象
            SumChf = SumChf + v["f"]
    
    if SumChf == 0:  # 全て除外されている場合
        return None
    
    # 累積確率を計算（Chdictを変更しない）
    cumulative_probs = {}
    F0 = 0.0
    for k, v in Chdict.items():
        if k not in excluded_chars:
            normalized_f = v["f"] / SumChf
            cumulative_probs[k] = F0 + normalized_f
            F0 = cumulative_probs[k]
    
    # 出題文字選定
    NumRandom = random.random()
    for i, cumulative_prob in cumulative_probs.items():
        if cumulative_prob >= NumRandom:
            return i
    
    return None

def adjustChdict(Chdict, QueCh, isCorrect):
    """正解・不正解に応じて出現確率を調整"""
    if isCorrect:
        Chdict[QueCh]["f"] = Chdict[QueCh]["f"] * 0.7
    else:
        Chdict[QueCh]["f"] = Chdict[QueCh]["f"] * 1.3
    return Chdict

def nextQuestion():
    global qCh, Chdict
    qCh = selectQuestion(Chdict)
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
    elif state == STATE_RETRY:
        Lguide.config(text="a=Replay / n=Continue")

def Space(Event=None):
    global state, mode, val1, val2, Chlist, Chdict, qCh, excluded_chars

    text = Disp1.get().strip()

    # ===== リトライ状態でのSpaceはContinueとして動作させる =====
    if state == STATE_RETRY:
        # 次の問題へ（前回の除外を解除してから、今回の文字を一時的に除外）
        L1.config(text="")
        L2.config(text="")
        if excluded_chars:
            excluded_chars.clear()
        if qCh is not None:
            excluded_chars.append(qCh)
        state = STATE_QUIZ
        nextQuestion()
        updateGuide()
        if Event:
            return "break"

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
                    excluded_chars.clear()  # 新しいセッション開始時に除外文字をリセット
                    Chdict = initChdict(Chlist)
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
            Chdict = adjustChdict(Chdict, qCh, True)
        else:
            L2.config(text=f"Answer: {caNum}", fg="red")
            Chdict = adjustChdict(Chdict, qCh, False)

        Disp1.set("")
        state = STATE_RETRY

    updateGuide()
    if Event:
        return "break"

def RetryKeyInput(Event):
    """リトライ画面でのキー入力処理"""
    global state, qCh

    if state != STATE_RETRY:
        return

    if Event.char == "y":
        # 同じ問題をもう一度
        L1.config(text="")
        L2.config(text="")
        state = STATE_QUIZ
        updateGuide()
        return "break"
    elif Event.char == "n":
        # 次の問題へ
        L1.config(text="")
        L2.config(text="")
        state = STATE_QUIZ
        nextQuestion()
        updateGuide()
        return "break"

root = tk.Tk()
root.geometry("300x200")
Disp1 = tk.StringVar()

FONT = ("Consolas", 10)

entry = tk.Entry(root, textvariable=Disp1, width=30, show="*", font=FONT)
entry.pack(pady=10)
entry.focus_set()  # 初期フォーカスをセット

Lguide = tk.Label(root, text="", font=FONT)
Lguide.pack(pady=10)

Lq = tk.Label(root, text="", font=FONT)
Lq.pack(pady=10)

L1 = tk.Label(root, text="", font=FONT)
L1.pack(pady=10)

L2 = tk.Label(root, text="", font=FONT)
L2.pack(pady=10)

entry.bind('<space>', Space)
entry.bind('<KeyPress>', UnifiedKeyInput)
root.bind('<KeyPress>', UnifiedKeyInput)

updateGuide()

root.mainloop()
