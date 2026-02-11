import math
import random

Chlist = ["a","b","c","d"]

def starter(Ch):
    Chdict = {}
    for i in Ch:
        Chdict[i] = {"f":1,"F":1}
    return Chdict

def Que(Chdict):
    # 出現確率を正規化,累積和計算
    SumChf = 0
    for v in Chdict.values():
        SumChf = SumChf + v["f"]
    F0 = 0
    for v in Chdict.values():
        v["f"] = v["f"] / SumChf
        v["F"] = F0 + v["f"]
        F0 = v["F"]
    print(Chdict)
    
    # 出題文字選定
    NumRandom = random.random()
    print(NumRandom)
    for i,v in Chdict.items():
        if v["F"] >= NumRandom:
            return i

# 出題
def Q_A(i):
    print(i)
    a = input()
    if a == i:
        print("Correct")
        return True
    else:
        print("Wrong")
        return False

# dictへの補正
def DictAdjust(Chdict,QueBool,QueCh):
    if QueBool == True:
        Chdict[QueCh]["f"] = Chdict[QueCh]["f"] * 0.7
    else:
        Chdict[QueCh]["f"] = Chdict[QueCh]["f"] * 1.3
    return Chdict


Chdict = starter(Chlist)
while True:
    QueCh = Que(Chdict)
    QueBool = Q_A(QueCh)
    Chdict = DictAdjust(Chdict,QueBool,QueCh)