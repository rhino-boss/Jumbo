# %%

import cv2
import numpy as np
import os


# %%

img_path = r"C:\Users\rhinshen\Mine\(個人工作區)\3_Tools\PyTools\OpenCV_v2\img"
ll = os.listdir(img_path)


# %%

# 讀取影像
# img_list = {}
# for i, na in enumerate(ll):
#     img_list[na[:2]] =


frame = cv2.imread("frames/frame_100.jpg", 0)
template = cv2.imread("symbols/7.png", 0)  # 符號模板

# 進行模板匹配
res = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
threshold = 0.8  # 設定匹配閾值
loc = np.where(res >= threshold)

# 在原圖上標示匹配到的符號
for pt in zip(*loc[::-1]):
    cv2.rectangle(frame, pt, (pt[0] + template.shape[1], pt[1] + template.shape[0]), (0, 255, 0), 2)

cv2.imshow("Matched Symbols", frame)
cv2.waitKey(0)
cv2.destroyAllWindows()
