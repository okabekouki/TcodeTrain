import getpass
import msvcrt
from colorama import Fore, Style, init
init()

# Tcode表データ
tcode = {
    "ぐ": { "difc": 1, "les": 999, "fi": 33, "se": 52},
    "ぱ": { "difc": 1, "les": 999, "fi": 11, "se": 13},
    "ぴ": { "difc": 1, "les": 999, "fi": 11, "se": 23},
    "ぷ": { "difc": 1, "les": 999, "fi": 11, "se": 33},
    "ぺ": { "difc": 1, "les": 999, "fi": 11, "se": 43},
    "ぽ": { "difc": 1, "les": 999, "fi": 11, "se": 53},
    "ふ": { "difc": 1, "les": 999, "fi": 42, "se": 23},
    "ぎ": { "difc": 1, "les": 999, "fi": 12, "se": 43},
    "ね": { "difc": 1, "les": 999, "fi": 43, "se": 33},
    "ぶ": { "difc": 1, "les": 999, "fi": 23, "se": 54},
    "ゆ": { "difc": 1, "les": 999, "fi": 34, "se": 34},
    "ぜ": { "difc": 1, "les": 999, "fi": 103, "se": 31},
    "せ": { "difc": 1, "les": 999, "fi": 72, "se": 22},
    "や": { "difc": 1, "les": 999, "fi": 62, "se": 32},
    "ど": { "difc": 1, "les": 999, "fi": 83, "se": 12},
    "よ": { "difc": 1, "les": 999, "fi": 73, "se": 22},
    "か": { "difc": 1, "les": 999, "fi": 73, "se": 32},
    "れ": { "difc": 1, "les": 999, "fi": 103, "se": 32},
    "き": { "difc": 1, "les": 999, "fi": 63, "se": 42},
    "く": { "difc": 1, "les": 999, "fi": 73, "se": 52},
    "え": { "difc": 1, "les": 999, "fi": 93, "se": 52},
    "ば": { "difc": 1, "les": 999, "fi": 84, "se": 22},
    "も": { "difc": 1, "les": 999, "fi": 82, "se": 13},
    "お": { "difc": 1, "les": 999, "fi": 92, "se": 13},
    "わ": { "difc": 1, "les": 999, "fi": 62, "se": 23},
    "ろ": { "difc": 1, "les": 999, "fi": 102, "se": 23},
    "う": { "difc": 1, "les": 999, "fi": 62, "se": 33},
    "あ": { "difc": 1, "les": 999, "fi": 62, "se": 43},
    "こ": { "difc": 1, "les": 999, "fi": 72, "se": 43},
    "さ": { "difc": 1, "les": 999, "fi": 72, "se": 53},
    "ら": { "difc": 1, "les": 999, "fi": 82, "se": 53},
    "と": { "difc": 1, "les": 2, "fi": 73, "se": 13},
    "て": { "difc": 1, "les": 2, "fi": 93, "se": 13},
    "る": { "difc": 1, "les": 5, "fi": 103, "se": 13},
    "し": { "difc": 1, "les": 5, "fi": 73, "se": 23},
    "た": { "difc": 1, "les": 4, "fi": 83, "se": 23},
    "が": { "difc": 1, "les": 1, "fi": 103, "se": 23},
    "い": { "difc": 1, "les": 5, "fi": 63, "se": 33},
    "、": { "difc": 1, "les": 1, "fi": 73, "se": 33},
    "の": { "difc": 1, "les": 1, "fi": 83, "se": 33},
    "。": { "difc": 1, "les": 4, "fi": 63, "se": 43},
    "で": { "difc": 1, "les": 3, "fi": 63, "se": 53},
    "は": { "difc": 1, "les": 2, "fi": 73, "se": 53},
    "に": { "difc": 1, "les": 2, "fi": 83, "se": 53},
    "な": { "difc": 1, "les": 4, "fi": 93, "se": 53},
    "を": { "difc": 1, "les": 3, "fi": 103, "se": 53},
    "ち": { "difc": 1, "les": 999, "fi": 104, "se": 13},
    "ん": { "difc": 1, "les": 999, "fi": 64, "se": 33},
    "ま": { "difc": 1, "les": 999, "fi": 74, "se": 33},
    "つ": { "difc": 1, "les": 999, "fi": 94, "se": 33},
    "け": { "difc": 1, "les": 999, "fi": 64, "se": 43},
    "す": { "difc": 1, "les": 999, "fi": 84, "se": 43},
    "み": { "difc": 1, "les": 999, "fi": 104, "se": 53},
    "ぢ": { "difc": 1, "les": 999, "fi": 81, "se": 44},
    "ほ": { "difc": 1, "les": 999, "fi": 102, "se": 14},
    "じ": { "difc": 1, "les": 999, "fi": 72, "se": 24},
    "だ": { "difc": 1, "les": 999, "fi": 63, "se": 34},
    "り": { "difc": 1, "les": 999, "fi": 73, "se": 34},
    "め": { "difc": 1, "les": 999, "fi": 93, "se": 34},
    "そ": { "difc": 1, "les": 999, "fi": 103, "se": 54},
    "ず": { "difc": 1, "les": 999, "fi": 84, "se": 14},
    "げ": { "difc": 1, "les": 999, "fi": 104, "se": 14},
    "ざ": { "difc": 1, "les": 999, "fi": 43, "se": 92},
    "づ": { "difc": 1, "les": 999, "fi": 32, "se": 83},
    "ぬ": { "difc": 1, "les": 999, "fi": 13, "se": 94},
    "ぼ": { "difc": 1, "les": 999, "fi": 34, "se": 74},
    "び": { "difc": 1, "les": 999, "fi": 73, "se": 92},
    "ぞ": { "difc": 1, "les": 999, "fi": 94, "se": 72},
    "む": { "difc": 1, "les": 999, "fi": 62, "se": 63},
    "べ": { "difc": 1, "les": 999, "fi": 62, "se": 93},
    "へ": { "difc": 1, "les": 999, "fi": 103, "se": 103},
    "ご": { "difc": 1, "les": 999, "fi": 104, "se": 83},
    "ひ": { "difc": 1, "les": 999, "fi": 74, "se": 94},
}


# キーボード配列データ
PCkey = {
    "1": {
        "col":1,
        "row":1,
    },
    "2": {
        "col":2,
        "row":1,
    },
    "3": {
        "col":3,
        "row":1,
    },
    "4": {
        "col":4,
        "row":1,
    },
    "5": {
        "col":5,
        "row":1,
    },
    "6": {
        "col":6,
        "row":1,
    },
    "7": {
        "col":7,
        "row":1,
    },
    "8": {
        "col":8,
        "row":1,
    },
    "9": {
        "col":9,
        "row":1,
    },
    "0": {
        "col":10,
        "row":1,
    },
    "q": {
        "col":1,
        "row":2,
    },
    "w": {
        "col":2,
        "row":2,
    },
    "e": {
        "col":3,
        "row":2,
    },
    "r": {
        "col":4,
        "row":2,
    },
    "t": {
        "col":5,
        "row":2,
    },
    "y": {
        "col":6,
        "row":2,
    },
    "u": {
        "col":7,
        "row":2,
    },
    "i": {
        "col":8,
        "row":2,
    },
    "o": {
        "col":9,
        "row":2,
    },
    "p": {
        "col":10,
        "row":2,
    },
    "a": {
        "col":1,
        "row":3,
    },
    "s": {
        "col":2,
        "row":3,
    },
    "d": {
        "col":3,
        "row":3,
    },
    "f": {
        "col":4,
        "row":3,
    },
    "g": {
        "col":5,
        "row":3,
    },
    "h": {
        "col":6,
        "row":3,
    },
    "j": {
        "col":7,
        "row":3,
    },
    "k": {
        "col":8,
        "row":3,
    },
    "l": {
        "col":9,
        "row":3,
    },
    ";": {
        "col":10,
        "row":3,
    },
    "z": {
        "col":1,
        "row":4,
    },
    "x": {
        "col":2,
        "row":4,
    },
    "c": {
        "col":3,
        "row":4,
    },
    "v": {
        "col":4,
        "row":4,
    },
    "b": {
        "col":5,
        "row":4,
    },
    "n": {
        "col":6,
        "row":4,
    },
    "m": {
        "col":7,
        "row":4,
    },
    ",": {
        "col":8,
        "row":4,
    },
    ".": {
        "col":9,
        "row":4,
    },
    "/": {
        "col":10,
        "row":4,
    },
}

# 選択肢
def select():
    while True:
        sel = msvcrt.getch()
        if sel == b"d":
            return 1
        if sel == b"k":
            return 2
        if sel == b"\x03":
            exit()

# 指定難易度以下の文字リストを作成
def makeChList(difc1,difc2):
    Chlist = []

    for v in tcode:
        if (tcode[v].get("difc") >= difc1) and (tcode[v].get("difc") <= difc2):
            Chlist.append(v)
    
    if Chlist == []:
        print("ERROR: No Character Found with Specified Difficulty")
        return None
    
    return Chlist

# 指定レッスン以下の文字リストを作成
def makeChList_les(les1,les2):
    Chlist = []

    for v in tcode:
        if (tcode[v].get("les") >= les1) and (tcode[v].get("les") <= les2):
            Chlist.append(v)
    
    if Chlist == []:
        print("ERROR: No Character Found with Specified Lesson")
        return None
    
    return Chlist

# 文字列の座標化
def Chnum(S):
    aStr = ""
    for i, Ch in enumerate(S):
        if Ch not in PCkey:
            acol = "x"
            arow = "x"
        else:
            acol = PCkey[Ch].get("col")
            arow = PCkey[Ch].get("row")
        if i == 0:
            aStr = str(acol) + str(arow)
        else:
            aStr = aStr +" " +str(acol) + str(arow)
    return aStr

# 出題～正解チェック
def quiz(Chlist):
    if Chlist == None:
        print
    # ランダム出題
    import random
    qCh = random.choice(Chlist)
    print(qCh)

    # 入力
    aCh = getpass.getpass("")
    uaNum = Chnum(aCh)

    # 答え合わせ
    caNum = str(tcode[qCh].get("fi")) +" "+ str(tcode[qCh].get("se"))
    print ("    Your Answer:", uaNum)
    if uaNum == caNum:
        print (Fore.BLUE,"Correct Answer:", caNum,Fore.WHITE)

    else:
        print (" Correct Answer:", caNum)
    
    print(Fore.GREEN+"a"+Fore.WHITE+":replay",  Fore.GREEN+"n"+Fore.WHITE+":continue")
    while True:
        replay = msvcrt.getch()
        if replay == b"a":
            return qCh
        if replay == b"n":
            return None
        if replay == b"\x03":
            exit()

# 難易度等入力
print ("Select Quiz Mode:")
print(Fore.GREEN+"d"+Fore.WHITE+":Difficulty",  Fore.GREEN+"k"+Fore.WHITE+":Lesson")
sel = select()
if sel == 1:
    while True:
        difc1 = input("Min Difficulty Level:")
        if str.isdigit(difc1) == False:
            print("ERROR: Difficulty Level Must Be a Number")
        else:
            difc1 = int(difc1)
            break
    while True:
        difc2 = input("Max Difficulty Level:")
        if str.isdigit(difc2) == False:
            print("ERROR: Difficulty Level Must Be a Number")
        else:
            difc2 = int(difc2)
            if difc2 < difc1:
                print("ERROR: Max Difficulty Level Must Be Greater Than or Equal to Min Difficulty Level")
            else:
                Chlist = makeChList(difc1,difc2)
                if Chlist != None:break
if sel == 2:
    while True:
        les1 = input("Min Lesson Level:")
        if str.isdigit(les1) == False:
            print("ERROR: Lesson Level Must Be a Number")
        else:
            les1 = int(les1)
            break
    while True:
        les2 = input("Max Lesson Level:")
        if str.isdigit(les2) == False:
            print("ERROR: Lesson Level Must Be a Number")
        else:
            les2 = int(les2)
            if les2 < les1:
                print("ERROR: Max Lesson Level Must Be Greater Than or Equal to Min Lesson Level")
            else:
                Chlist = makeChList_les(les1,les2)
                if Chlist != None:break

# quiz動作部分
curChlist = Chlist
while True:
    replay = quiz(curChlist)
    if replay == None:
        curChlist = Chlist
    else:
        curChlist = replay