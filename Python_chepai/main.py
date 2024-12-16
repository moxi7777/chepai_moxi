import time
import tkinter as tk
import cv2
import test1
import pic_function as predict
import pic_mm
from threading import Thread
from tkinter import ttk
from tkinter.filedialog import *
from PIL import Image, ImageTk
import tkinter.messagebox as mBox
from tkinter import LEFT, BOTH,TOP,RIGHT


class ThreadWith(Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, *, daemon=None):
        Thread.__init__(self, group, target, name, args, kwargs, daemon=daemon)
        self._return1 = None
        self._return2 = None
        self._return3 = None

    def run(self):
        if self._target is not None:
            self._return1, self._return2, self._return3 = self._target(*self._args, **self._kwargs)

    def join(self):
        Thread.join(self)
        return self._return1, self._return2, self._return3


class Surface(ttk.Frame):
    pic_path = ""
    viewhigh = 350
    viewwide = 300
    update_time = 0
    thread = None
    thread_run = False
    camera = None
    color_transform = {"green": ("绿牌", "#55FF55"), "yello": ("黄牌", "#FFFF00"), "blue": ("蓝牌", "#6666FF")}

    def __init__(self, win):
        ttk.Frame.__init__(self, win)

        # 设置窗口标题和状态
        win.title("车牌识别")
        # 设置整体背景色为浅色，增加一些边距和填充
        self.configure(style="TFrame")

        # 创建框架
        frame_top = ttk.Frame(self)
        frame_bottom = ttk.Frame(self)

        # 使用pack方法，使frame竖直布局
        self.pack(fill=tk.BOTH, expand=tk.YES, padx=20, pady=20)
        frame_top.pack(side=tk.TOP, expand=1, fill=tk.BOTH)
        frame_bottom.pack(side=tk.TOP, expand=0, fill=tk.X)

        # 设置顶部框架的内容：显示待识别的图片
        label_frame = ttk.Frame(frame_top, padding=10)
        label_frame.pack(anchor="nw", fill=tk.X)

        ttk.Label(label_frame, text='待识别图片', font=('Arial', 14, 'bold'), foreground="black",
                  background="#DCE6F1").pack(anchor="nw")

        self.image_ctl = ttk.Label(frame_top)
        self.image_ctl.pack(anchor="nw", pady=10)

        # 添加三条红色分割线
        separator_top1 = ttk.Separator(frame_top, orient="horizontal")
        separator_top1.pack(fill=tk.X, pady=5)

        separator_top2 = ttk.Separator(frame_top, orient="horizontal")
        separator_top2.pack(fill=tk.X, pady=5)

        separator_top3 = ttk.Separator(frame_top, orient="horizontal")
        separator_top3.pack(fill=tk.X, pady=5)

        # 设置底部框架的内容：显示车牌图像和结果
        ttk.Label(frame_bottom, text='车牌图像', font=('Arial', 12, 'bold'), foreground="black",
                  background="#DCE6F1").grid(column=0, row=0, sticky=tk.W, padx=10, pady=5)
        self.roi_ctl = ttk.Label(frame_bottom)
        self.roi_ctl.grid(column=0, row=1, sticky=tk.W, padx=10, pady=5)

        ttk.Label(frame_bottom, text='结果如下：', font=('Arial', 12, 'bold'), foreground="black",
                  background="#DCE6F1").grid(column=0, row=2, sticky=tk.W, padx=10, pady=5)
        self.r_ctl = ttk.Label(frame_bottom, text="", font=('Arial', 18, 'bold'), foreground="black")
        self.r_ctl.grid(column=0, row=3, sticky=tk.W, padx=10, pady=5)

        self.color_ctl = ttk.Label(frame_bottom, text="", font=('Arial', 14), foreground="black")
        self.color_ctl.grid(column=0, row=4, sticky=tk.W, padx=10, pady=5)

        # 设置选择图片按钮
        from_pic_ctl = ttk.Button(frame_bottom, text="请放入待识别图片", width=20, command=self.from_pic,
                                  style="TButton")
        from_pic_ctl.grid(column=0, row=5, sticky=tk.SE, padx=10, pady=10)

        # 设置空白标签和第二组预测结果
        ttk.Label(frame_bottom, text=' 备用', background="#DCE6F1").grid(column=0, row=6, sticky=tk.W, padx=10, pady=5)
        self.roi_ct2 = ttk.Label(frame_bottom)
        self.roi_ct2.grid(column=0, row=7, sticky=tk.W, padx=10, pady=5)

        ttk.Label(frame_bottom, text='备用结果（不准）', background="#DCE6F1").grid(column=0, row=8, sticky=tk.W, padx=10, pady=5)
        self.r_ct2 = ttk.Label(frame_bottom, text="", font=('Arial', 14), foreground="black")
        self.r_ct2.grid(column=0, row=9, sticky=tk.W, padx=10, pady=5)

        self.color_ct2 = ttk.Label(frame_bottom, text="", font=('Arial', 14), foreground="black")
        self.color_ct2.grid(column=0, row=10, sticky=tk.W, padx=10, pady=5)

        # 设置样式
        style = ttk.Style()
        style.configure("TFrame", background="#DCE6F1")  # 浅蓝色背景
        style.configure("TLabel", background="#DCE6F1", font=("Arial", 12), foreground="black")  # 黑色字体，浅蓝色背景
        style.configure("TButton", font=("Arial", 12, 'bold'), padding=6, background="#A9C5E9", foreground="black")
        style.map("TButton", background=[("active", "#A1C6F1")])

        # 自定义红色分割线的样式
        style.configure("Red.TSeparator", background="red")

        # 初始化预测器
        self.predictor = predict.CardPredictor()
        self.predictor.train_svm()




    def get_imgtk(self, img_bgr):
        # 将 BGR 图像转换为 RGB 格式
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)

        # 将 NumPy 数组转换为 PIL 图像
        im = Image.fromarray(img_rgb)

        # 获取图像的宽高
        wide, high = im.size

        # 如果图像宽度或高度超过了视图的大小，进行缩放
        if wide > self.viewwide or high > self.viewhigh:
            wide_factor = self.viewwide / wide
            high_factor = self.viewhigh / high
            factor = min(wide_factor, high_factor)

            # 根据最小的缩放因子调整宽高
            wide = int(wide * factor)
            high = int(high * factor)

            # 确保宽高不小于 1
            if wide <= 0: wide = 1
            if high <= 0: high = 1

            # 使用 PIL 的 resize 方法进行缩放
            im = im.resize((wide, high), Image.Resampling.LANCZOS)

        # 转换为 Tkinter 兼容的图像格式
        imgtk = ImageTk.PhotoImage(image=im)

        return imgtk

    def show_roi1(self, r, roi, color):
        if r:
            roi = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
            roi = Image.fromarray(roi)
            self.imgtk_roi = ImageTk.PhotoImage(image=roi)
            self.roi_ctl.configure(image=self.imgtk_roi, state='enable')
            self.r_ctl.configure(text=str(r))
            self.update_time = time.time()
            try:
                c = self.color_transform[color]
                self.color_ctl.configure(text=c[0], background=c[1], state='enable')
            except:
                self.color_ctl.configure(state='disabled')
        elif self.update_time + 8 < time.time():
            self.roi_ctl.configure(state='disabled')
            self.r_ctl.configure(text="")
            self.color_ctl.configure(state='disabled')

    def show_roi2(self, r, roi, color):
        if r:
            roi = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
            roi = Image.fromarray(roi)
            self.imgtk_roi = ImageTk.PhotoImage(image=roi)
            self.roi_ct2.configure(image=self.imgtk_roi, state='enable')
            self.r_ct2.configure(text=str(r))
            self.update_time = time.time()
            try:
                c = self.color_transform[color]
                self.color_ct2.configure(text=c[0], background=c[1], state='enable')
            except:
                self.color_ct2.configure(state='disabled')
        elif self.update_time + 8 < time.time():

            self.roi_ct2.configure(state='disabled')
            self.r_ct2.configure(text="")
            self.color_ct2.configure(state='disabled')

    def show_img_pre(self):

        filename =test1.get_name()
        if filename.any():
            test1.img_show(filename)


    def from_pic(self):
        self.thread_run = False
        self.pic_path = askopenfilename(title="选择识别图片", filetypes=[("jpg图片", "*.jpg"), ("png图片", "*.png")])
        if self.pic_path:
            img_bgr = pic_mm.img_read(self.pic_path)
            first_img, oldimg = self.predictor.img_first_pre(img_bgr)
            self.imgtk = self.get_imgtk(img_bgr)
            self.image_ctl.configure(image=self.imgtk)
            th1 = ThreadWith(target=self.predictor.img_color_contours, args=(first_img, oldimg))
            th2 = ThreadWith(target=self.predictor.img_only_color, args=(oldimg, oldimg, first_img))
            th1.start()
            th2.start()
            r_c, roi_c, color_c = th1.join()
            r_color, roi_color, color_color = th2.join()
            print(r_c, r_color)

            self.show_roi2(r_color, roi_color, color_color)

            self.show_roi1(r_c, roi_c, color_c)


def close_window():
    print("destroy")
    if surface.thread_run:
        surface.thread_run = False
        surface.thread.join(2.0)
    win.destroy()


if __name__ == '__main__':
    win = tk.Tk()

    surface = Surface(win)
    # close,退出输出destroy
    win.protocol('WM_DELETE_WINDOW', close_window)
    # 进入消息循环
    win.mainloop()
