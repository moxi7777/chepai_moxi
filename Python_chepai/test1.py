
import cv2
import numpy as np


def img_show(filename):
    if filename.dtype == "float32":
        filename = filename.astype(np.uint8)
    cv2.imshow("img_show", filename)
    cv2.waitKey(0)


def img_contours(oldimg, box):
    box = np.int0(box)
    oldimg = cv2.drawContours(oldimg, [box], 0, (0, 0, 255), 2)
    cv2.imshow("img_contours", oldimg)
    cv2.waitKey(0)


def img_car(img_contours):
    pic_hight, pic_width = img_contours.shape[:2]
    return pic_hight, pic_width
class global_var:
    name = None


def set_name(name):
    global_var.name = name


def get_name():
    return global_var.name
