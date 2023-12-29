from sympy import Symbol, solve
import math
from datetime import datetime
import datetime
from pvlib import location
import pandas as pd
from PyQt5 import uic
from PyQt5.QtWidgets import QApplication
from pysolar.solar import get_altitude

class mainwin():# 主窗口
    def __init__(self):# 从 UI 定义中动态 创建一个相应的窗口对象
        # 注意：里面的控件对象也成为窗口对象的属性了
        # 比如 self.ui.button , self.ui.textEdit
        self.ui = uic.loadUi('mainwindow.ui')
        # 公式常数
        self.σ = 5.67 * pow(10, -12)
        self.ui.calculate.clicked.connect(lambda:self.calculate(self.matierial()))  # 菜单栏的选择文件
    def clearsky(self, site_location, time_str):
        cur_time = datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        times = pd.date_range(start=cur_time, freq='1min', periods=20, tz=site_location.tz)
        # 使用默认的内部模型生成晴天数据start=f'{cur_time.year}-{cur_time.month}-{cur_time.day} {cur_time.hour}:{cur_time.minute}'
        # get_ clearsky方法返回具有GHI、DNI和DHI值的数据表
        clearsky = site_location.get_clearsky(times)
        irradiance = pd.DataFrame({'GHI': clearsky['ghi'], 'DNI': clearsky['dni'], 'DHI': clearsky['dhi']})
        irradiance.index = irradiance.index.strftime("%H:%M")
        ghi = irradiance['GHI'].iloc[0]
        dni = irradiance['DNI'].iloc[0]
        dhi = irradiance['DHI'].iloc[0]
        return ghi, dni, dhi

    def matierial(self):
        if self.ui.abs.isChecked() == True:
            i = 0
        if self.ui.pc.isChecked() == True:
            i = 1
        if self.ui.carbon.isChecked() == True:
            i = 2
        return i

    def calculate_altitude(self, time_str, latitude, longitude, utctime):
        """从datetime类型的时间计算当前大气外理论辐照度"""
        cur_time = datetime.datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
        day_year = int(datetime.datetime.strftime(cur_time, '%j'))  # j是积日
        utc = datetime.datetime(cur_time.year, cur_time.month, cur_time.day, cur_time.hour, cur_time.minute, 1, 130320,
                                tzinfo=datetime.timezone(datetime.timedelta(hours=utctime)))
        altitude = get_altitude(latitude, longitude, utc)
        return altitude
    def calculate(self,i):
        # 反射率，ABS,PC,碳复合
        ghi, dni , dhi= self.clearsky(
            location.Location(self.ui.lat.value(), self.ui.lon.value(), tz=self.ui.region.currentText()),
            self.ui.localtime.dateTime().toString("yyyy-MM-dd hh:mm:ss"))
        altitude = self.calculate_altitude(self.ui.localtime.dateTime().toString("yyyy-MM-dd hh:mm:ss"),
                                           self.ui.lat.value(), self.ui.lon.value(), self.ui.utctimezone.value())
        r = [0.13, 0.8, 0.1]
        # 发射率，ABS,PC,碳复合
        epsilon = [0.94, 0.9, 0.91]
        # 发热/面积
        battery = 9.9 * pow(10, 4)
        motor = 2.1 * pow(10, 5)
        # 自变量无人机温度
        T = Symbol('T')
        expr1 = self.σ * T ** 4 + 5.2 * T - battery*0.0015/10-motor*0.0015/25-40*275*0.13- (1 - r[0]) * ghi * 0.15
        T = solve(expr1)
        T = T[1]
        self.printf(f'无人机温度{T}K')

        # 大气透过率
        if dhi == 0:
            t0 = 1
        else:
            t0 = dni*math.sin(altitude)/dhi

        Ad = 0.5 * 0.1 * 0.1
        # 0.5平方厘米
        delta_f = 5000
        # 赫兹
        D_star = pow(10, 11)
        # 比探测率
        D = D_star / pow(Ad * delta_f, 0.5)
        # 探测率
        NEP = 1 / D
        E = NEP*pow(10,8)
        self.printf(f'噪声等效功率{NEP}W')
        # 噪声等效功率，最小探测功率,算出为5e-11
        M0 = epsilon[i] * self.σ * pow(T, 4)
        # 物体辐射出射度
        L0 = M0 / math.pi
        # 物体辐射亮度
        t = 1
        # 成像系统透过率
        f = self.ui.foc.value()
        S = pow(math.fabs(4*E*f*f/(t*t0*math.pi*L0-E)),0.5)
        self.printf(f'最小通光孔径{S}m')
        # 像平面辐照度
        Lb = ghi * S
        self.printf(f'光敏器件接受背景辐射{Lb}W')

    def printf(self, mes):
        self.ui.textBrowser.append(mes)  # 在指定的区域显示提示信息
        self.ui.textBrowser.ensureCursorVisible()

if __name__ == '__main__':
    app = QApplication([])
    Qmainwin = mainwin()  # 创建主窗口
    Qmainwin.ui.show()  # show出窗口
    app.exec_()  # 维持窗口