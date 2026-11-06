import numpy as np
import matplotlib.pyplot as plt


# 標籤
labels = np.array(["特色活躍", "和諧度", "輸贏比", "特色強度", "劇烈度", "好壞差"])


labels = np.concatenate((labels, [labels[0]]))  # 閉合

# 資料
# data = np.array([8, 9, 5, 8, 9, 5])
data = [82.56, 25.67, 12.51, 19.39, 40.83, 38.81]
data = np.concatenate((data, [data[0]]))  # 閉合 # 將資料結合起來


# 資料個數
dataLenth = len(labels) - 1

# 角度設定
angles = np.linspace(0, 2 * np.pi, dataLenth, endpoint=False)
angles = np.concatenate((angles, [angles[0]]))  # 閉合


fig = plt.figure(figsize=(10, 10))

ax = fig.add_subplot(121, polar=True)  # polar引數！！代表畫圓形！！！！
ax.plot(angles, data, "bo-", linewidth=1)  # 畫線四個引數為x,y,標記和顏色，閒的寬度  # 1
ax.fill(angles, data, facecolor="r", alpha=0.1)  # 填充顏色和透明度
ax.set_thetagrids(angles * 180 / np.pi, labels, fontsize=15, fontproperties="Microsoft JhengHei")  # 2
# ax.set_title("analysis", va="baseline", fontproperties="Microsoft JhengHei")
# ax.set_rlim(0, 10)  # 3

ax.grid(True)  # 4

plt.show()
