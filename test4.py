import math
import random

Ch = ["a","b","c","d"]

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




Chdict = starter(Ch)
print(Que(Chdict))
