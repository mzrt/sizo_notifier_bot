from typing import Dict

words = {'y': ['лет', 'год', 'года'], 'm': ['месяцев', 'месяц', 'месяца'], 'd': ['дней', 'день', 'дня'], 'p': ['мест', 'место', 'места']}

def datePeriodName(dataDict:Dict):
    out = []
    for k, v in dataDict.items():
        remainder = v % 10
        if v == 0 or remainder == 0 or remainder >= 5 or v in range(11, 19):
            st = str(v), words[k][0]
        elif remainder == 1:
            st = str(v), words[k][1]
        else:
            st = str(v), words[k][2]
        out.append(" ".join(st))
    return out