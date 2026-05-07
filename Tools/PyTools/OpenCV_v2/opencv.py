# %%

import cv2
import os

run_path = r"C:\Users\rhinshen\Mine\(個人工作區)\3_Tools\PyTools\OpenCV_v2"
os.chdir(run_path)

print(os.getcwd())


import os

output_folder = "frames"
if not os.path.exists(output_folder):
    os.makedirs(output_folder)  # 建立資料夾


import cv2
import numpy as np

test_image = np.zeros((100, 100, 3), dtype=np.uint8)  # 建立 100x100 黑色圖片
success = cv2.imwrite("test.jpg", test_image)

if success:
    print("影像儲存成功！")
else:
    print("影像儲存失敗，請檢查 OpenCV 安裝")


# %%


# 讀取影片
video_file_name = "Test2.mp4"  # 你的影片路徑
cap = cv2.VideoCapture(video_file_name)

frame_count = 0
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break  # 影片結束

    # 每 10 張影格擷取 1 張，避免重複
    if frame_count % 10 == 0:
        cv2.imshow("Frame", frame)  # 顯示影格
        cv2.imwrite(f"frames/frame_{frame_count}.jpg", frame)  # 儲存影格

    frame_count += 1
    if cv2.waitKey(1) & 0xFF == ord("q"):  # 按 'q' 退出
        break

cap.release()
cv2.destroyAllWindows()

# %%
