import cv2
import numpy as np
import requests

url ="https://imgproxy.poponote.app/1/auto/850/0/sm/0/aHR0cHM6Ly9hc3NldHMucG9wb25vdGUuYXBwL25vdGUvNjRiN2JiYjEzNDA5YmUyYWEyNTE2Njc5L21lZGlhLzY0ZDkxODg1Y2U3NzgzMmE0NzIwZTMzZg=="
data = requests.get(url)
img = np.asarray( bytearray( data.content ), dtype=np.uint8 )

img = cv2.imdecode( img , cv2.IMREAD_COLOR)

''' 臉部 '''
case_path1 = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
faceCascade = cv2.CascadeClassifier(case_path1)

''' 笑容 '''
case_path2 = cv2.data.haarcascades + "haarcascade_smile.xml"
smileCascade = cv2.CascadeClassifier(case_path2)


''' 臉部辨識 '''
faces = faceCascade.detectMultiScale( img , scaleFactor=1.1, minNeighbors=5 , minSize=(25,25) , flags=cv2.CASCADE_SCALE_IMAGE )  
# print("偵測" + str(len(faces)) +"張人臉")

''' 笑容辨識 '''
for (x, y, w, h) in faces:
  img2 = cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2) # 人臉的長方形
  face_smile = img2[y:y+h, x:x+w]
  smile = smileCascade.detectMultiScale( face_smile , scaleFactor=1.05 , minNeighbors=4 , minSize=(15, 15) , flags=cv2.CASCADE_SCALE_IMAGE) 
  for (x,y,w,h) in smile:
       cv2.rectangle(face_smile, (x,y), (x+w, y+h), (255,0,0) ,2) # 笑容的長方形

cv2.imshow( "Image",img2 ) # 顯示圖片
cv2.waitKey(0)
