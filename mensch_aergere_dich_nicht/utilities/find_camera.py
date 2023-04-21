import cv2

cap_id = 1
cap = cv2.VideoCapture(cap_id)

while True:
    _, frame = cap.read()
    cv2.imshow("test", frame)

    key = cv2.waitKey(20) 
    if key == 27:
        break

cv2.destroyAllWindows()
cv2.VideoCapture(cap_id).release()
