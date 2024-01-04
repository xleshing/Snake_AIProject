import numpy as np
import cv2
from PIL import ImageGrab


class ColorObjectDetector:
    def __init__(self, w=400, h=400, contour_min_area=1):
        """
        初始化物件檢測器。

        :param w: 影像寬度。
        :param h: 影像高度。
        :param contour_min_area: 輪廓的最小面積，用於過濾小的噪點。
        """
        self.play_num = 0
        self.w = w
        self.h = h
        self.border = [0, 0, w, h]
        self.tolerance = 3  # 考虑一些容差
        self.x_list, self.y_list, self.w_list, self.h_list = [], [], [], []
        self.color_ranges = [
            ([35, 43, 46], [77, 255, 255]),  # 綠色
            ([0, 43, 46], [10, 255, 255]),  # 紅色
            ([0, 0, 221], [180, 30, 255]),  # 白色
        ]
        self.snake_headw_size = 0
        self.snake_bodyw_size = 0
        self.snake_headh_size = 0
        self.snake_bodyh_size = 0

        self.contour_min_area = contour_min_area

    def find_contour(self, frame):
        """
        在影像中找到輪廓。

        :param frame: 影格
        :return: 輪廓的座標（x、y、寬度、高度）列表。
        """

        if frame is None:
            return None

        if len(frame.shape) == 3:  # 檢查影像通道數
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        else:
            hsv = cv2.cvtColor(cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR), cv2.COLOR_BGR2HSV)

        self.x_list, self.y_list, self.w_list, self.h_list = [], [], [], []

        for lower, upper in self.color_ranges:
            # 根據顏色範圍創建遮罩

            mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            for cnt in contours:

                area = cv2.contourArea(cnt)

                if area > self.contour_min_area:
                    # 找到輪廓的外接矩形
                    x, y, w, h = cv2.boundingRect(cnt)
                    self.x_list.append(x)
                    self.y_list.append(y)
                    self.w_list.append(w)
                    self.h_list.append(h)

    def check_collision(self, pt):
        """
        檢查是否與牆壁或蛇身碰撞。

        :param pt: 點的座標（x、y）。
        :return: 若碰撞返回True，否則返回False。
        """
        head_x, head_y = pt
        # 檢查是否碰到牆壁
        if (head_x - self.border[0] <= 0 and abs(head_x - self.border[0]) >= self.snake_headw_size / 2) or (  # 左
                abs(head_x - self.border[2]) <= self.snake_headw_size / 2) or (  # 右
                head_y - self.border[1] <= 0 and abs(head_y - self.border[0]) >= self.snake_headh_size / 2) or (  # 上
                abs(head_y - self.border[3]) <= self.snake_headh_size / 2):  # 下
            return True

        # 檢查是否碰到自己的身體
        for body_x, body_y, body_w, body_h in zip(self.x_list[2:], self.y_list[2:], self.w_list[2:], self.h_list[2:]):
            if (
                    head_x <= body_x + self.tolerance and
                    head_x + self.snake_headw_size >= body_x + body_w - self.tolerance and
                    head_y <= body_y + self.tolerance and
                    head_y + self.snake_headh_size >= body_y + body_h - self.tolerance
            ):
                return True

        return False

    def get_state(self, direction=None):
        """
        獲取遊戲狀態。

        :param direction: 蛇的移動方向（左、右、上、下）。
        :return: 包含遊戲狀態的NumPy陣列。
        """
        if direction is None:
            direction = [0, 0, 0, 0]

        img = ImageGrab.grab(bbox=(0, 0, 400, 400))

        img_np = np.array(img)

        frame = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)

        frame = cv2.resize(frame, (self.w, self.h))

        self.find_contour(frame)

        try:
            self.snake_bodyw_size = self.w_list[2]
            self.snake_bodyh_size = self.h_list[2]
        except IndexError:
            self.snake_bodyw_size = 18
            self.snake_bodyh_size = 18
        try:
            self.snake_headw_size = self.w_list[0]
            self.snake_headh_size = self.h_list[0]
        except IndexError:
            self.snake_headw_size = 20
            self.snake_headh_size = 20

        try:
            hx, hy = self.x_list[0], self.y_list[0]
        except IndexError:
            hx, hy = 0, 0

        try:
            fx, fy = self.x_list[1], self.y_list[1]
        except IndexError:
            try:
                fx, fy = self.x_list[0], self.y_list[0]
            except IndexError:
                fx, fy = self.border[2], self.border[3]

        point_l = (hx - (self.snake_headw_size - self.tolerance), hy)
        point_r = (hx + (self.snake_headw_size - self.tolerance), hy)
        point_u = (hx, hy - (self.snake_headh_size - self.tolerance))
        point_d = (hx, hy + (self.snake_headh_size - self.tolerance))

        state = [
            # 危險直行
            (direction[1] and self.check_collision(point_r)) or
            (direction[0] and self.check_collision(point_l)) or
            (direction[2] and self.check_collision(point_u)) or
            (direction[3] and self.check_collision(point_d)),

            # 危險右轉
            (direction[3] and self.check_collision(point_l)) or
            (direction[2] and self.check_collision(point_r)) or
            (direction[1] and self.check_collision(point_d)) or
            (direction[0] and self.check_collision(point_u)),

            # 危險左轉
            (direction[2] and self.check_collision(point_l)) or
            (direction[3] and self.check_collision(point_r)) or
            (direction[0] and self.check_collision(point_d)) or
            (direction[1] and self.check_collision(point_u)),

            # 移動方向
            direction[0],
            direction[1],
            direction[2],
            direction[3],

            (fx + self.tolerance < hx),  # 食物在左
            (fx - self.tolerance > hx),  # 食物在右
            (fy + self.tolerance < hy),  # 食物在上
            (fy - self.tolerance > hy)   # 食物在下
        ]

        return np.array(state, dtype=int)
