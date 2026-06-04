import cv2

for index in range(10):
    print(f"Testing camera index {index}...")

    cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print(f"No camera at index {index}")
        cap.release()
        continue

    ret, frame = cap.read()

    if ret:
        print(f"Camera works at index {index}")
        cv2.imshow(f"Camera Index {index}", frame)
        cv2.waitKey(3000)
    else:
        print(f"Camera index {index} opened but failed to read")

    cap.release()
    cv2.destroyAllWindows()