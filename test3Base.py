import math
import tcodeData_generated
import PCkey
import random

# 指定難易度以下の文字リストを作成
def makeChList(difc1,difc2):
    Chlist = []

    for v in tcodeData_generated.tcode:
        if (tcodeData_generated.tcode[v].get("difc") >= difc1) and (tcodeData_generated.tcode[v].get("difc") <= difc2):
            Chlist.append(v)
    
    if Chlist == []:
        print("ERROR: No Character Found with Specified Difficulty")
        return None
    
    return Chlist

# 指定レッスン以下の文字リストを作成
def makeChList_les(les1,les2):
    Chlist = []

    for v in tcodeData_generated.tcode:
        if (tcodeData_generated.tcode[v].get("les") >= les1) and (tcodeData_generated.tcode[v].get("les") <= les2):
            Chlist.append(v)
    
    if Chlist == []:
        print("ERROR: No Character Found with Specified Lesson")
        return None
    
    return Chlist

# 文字列の座標化
def Chnum(S):
    aStr = ""
    for i, Ch in enumerate(S):
        if Ch not in PCkey.key:
            acol = "x"
            arow = "x"
        else:
            acol = PCkey.key[Ch].get("col")
            arow = PCkey.key[Ch].get("row")
        if i == 0:
            aStr = str(acol) + str(arow)
        else:
            aStr = aStr +" " +str(acol) + str(arow)
    return aStr

# 次の問題作成
# 問題生成（1問）
def makeQuestion(Chlist):
    if Chlist is None or len(Chlist) == 0:
        return None
    return random.choice(Chlist)

# 正解座標を取得
def getCorrectNum(qCh):
    if qCh is None:
        return None
    return str(tcodeData_generated.tcode[qCh].get("fi")) + " " + str(tcodeData_generated.tcode[qCh].get("se"))