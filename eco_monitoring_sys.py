# -*- coding: utf-8 -*-
"""
Project Name: eco_monitoring_sys(环保监测数据记录与分析系统)
File Description: 负责录入、存储环保监测数据，生成 CSV 文件
Date: 2025-06-15
Author: 杨澍
Version: v1.2

"""

import pandas as pd
import matplotlib.patches as plt
import numpy as np

import csv
import socket
import os
from datetime import datetime

# 获取计算机名称
computer_name = socket.gethostname() 



class MonitorRecord(object):
    """
        封装一条环保监测记录,包含时间、地点、温度、pH 值、PM2.5 等字段

        Attributes:
            record_id (int, optional): 记录唯一 ID,默认由程序自动生成
            timestamp (datetime): 记录时间戳
            location (str): 地点
            temperature (float): 摄氏温度
            pH (float): 水体酸碱度
            pm25 (float): PM2.5 浓度
            remarks (str): 备注信息
            device (str): 录入设备名(即 computer_name)

    """
    def __init__(self,timestamp: datetime,location: str,temperature_celsius: float,
                 pH: float,pm25: float,remarks: str,computer_name: str,record_id=None):
        
        self.timestamp = timestamp
        self.location = location
        self.temperature = temperature_celsius
        self.pH = pH
        self.pm25 = pm25
        self.remarks = remarks
        self.device = computer_name
        
    def to_list(self):
        """
        将记录转换为列表格式，便于写入 CSV 文件
        
        Returns:
            list: 包含所有字段的列表，顺序与 CSV 表头一致
        """
        return [
            
            self.timestamp.strftime('%Y-%m-%d %H:%M'),
            self.location,
            self.temperature,
            self.pH,
            self.pm25,
            self.remarks,
            self.device
        ]
    
    @staticmethod # 静态方法
    def from_list(data: list):
        """
        从列表中还原出 MonitorRecord 对象
        
        Args:
            data (list): 包含记录字段的列表
            
        Returns:
            MonitorRecord: 构造完成的对象
        """
        timestamp = datetime.strptime(data[1], '%Y-%m-%d %H:%M')
        return MonitorRecord(
            
            timestamp=timestamp,
            location=data[2],
            temperature=float(data[3]),
            ph=float(data[4]),
            pm25=float(data[5]),
            note=data[6],
            record_id=None
        )


class CSVManager(object): # CSV 文件管理
    """
    管理 CSV 文件的读写操作，包括保存记录、生成唯一 ID 和自动创建文件
    
    Attributes:
        filepath (str): CSV 文件路径
    """
    def __init__(self,filepath):
        """
        初始化 CSVManager 类，创建一个 CSV 文件并设置文件路径
        """
        self.filepath = filepath


    def save_record_pd(self,record):
        """
        使用 pandas 实现记录保存到 CSV 文件
        """
        columns = ['时间戳', '地点', '温度', 'pH', 'pm2.5', '备注', '录入设备']
        data = pd.DataFrame([record.to_list()], columns=columns)
        if os.path.exists(self.filepath):
        # 读取已有数据
            df = pd.read_csv(self.filepath)
            if not df.empty:
                next_id = df['ID'].max() + 1
            else:
                next_id = 0
        else:
            next_id = 0

        # 设置新的 DataFrame 索引为 next_id
        data.index = [next_id]

        # 追加写入 CSV，只在首次创建时写入表头
        data.to_csv(self.filepath,mode='a',index=True,index_label='ID',header=not os.path.exists(self.filepath))

        
def User_inputdata(): # 用户输入数据
    """
    交互式地获取用户输入的环保监测数据
    
    Returns:
        MonitorRecord: 包含用户输入数据的记录对象
    """

    while True:
        time_str = input("请输入时间(YYYY-MM-DD HH:MM),留空则使用当前时间：").strip()
        if time_str == "":
            timestamp = datetime.now()
            break
        try:
            timestamp = datetime.strptime(time_str, '%Y-%m-%d %H:%M')
            break
        except ValueError:
            print("时间格式错误，请输入形如 '2025-06-15 08:30' 的时间")

    location = input("请输入地点：").strip()
    
    while True:
        try:
            temperature_celsius = float(input("请输入温度(℃)："))
            break
        except ValueError:
            print("温度必须是数字，请重新输入")

    while True:
        try:
            pH = float(input("请输入水体 pH 值:"))
            break
        except ValueError:
            print(" pH 值必须是数字，请重新输入")

    while True:
        try:
            pm25 = float(input("请输入大气 PM2.5 值:"))
            break
        except ValueError:
            print(" PM2.5 必须是数字，请重新输入")

    remarks = input("请输入备注(可留空):").strip()

    return MonitorRecord(timestamp=timestamp,location=location,temperature_celsius=temperature_celsius,pH=pH,pm25=pm25,remarks=remarks,
                         computer_name=computer_name)


def add_record():
    """
    添加记录到CSV文件中
    
    本函数通过实例化CSVManager类来管理CSV文件,并获取用户输入的数据,
    然后将这些数据保存到指定的CSV文件中
    """
    
    manager = CSVManager("D:\\ProjectsHub\\eco_monitoring_sys_hw\\Data\\monitor_data.csv")

    record = User_inputdata()

    manager.save_record_pd(record)
    
def main_menu():
    menu_option = {
        '1':(),
        '2':(),
        '3':(),
        '4':()
    }
    while True:
        for key,(desc,_) in menu_option.items():
            print(f'{key},{desc}')
            choice = input("请选择操作:")

        if choice in menu_option:
            menu_option[choice][1]()


        else:
            print("无效操作输入,请重试")
        

    

if __name__ == "__main__":
    add_record()
