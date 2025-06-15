# -*- coding: utf-8 -*-
"""
Project Name: eco_monitoring_sys(环保监测数据记录与分析系统)
File Description: 负责录入、存储环保监测数据，生成 CSV 文件
Date: 2025-06-15
Author: 杨澍
Version: v1.2

"""

import pandas as pd
from pandas import Timestamp
import matplotlib.patches as plt
import numpy as np

import csv
import socket
import os
from datetime import datetime


# 获取计算机名称
computer_name = socket.gethostname() 

# 定义常量类
default_file_path = 'D:\\ProjectsHub\\eco_monitoring_sys_hw\\Data\\monitor_data.csv'


# 工具函数

def to_timestamp(value) -> pd.Timestamp:
    return pd.Timestamp(value)

def now_timestamp() -> pd.Timestamp:
    return pd.Timestamp.now()



# 数据结构

class MonitorRecord(object):
    """
        封装一条环保监测记录,包含时间、地点、温度、pH 值、PM2.5 等字段

        Attributes:
            record_id (int, optional): 记录唯一 ID,默认由程序自动生成
            timestamp (Timestamp): 记录时间戳
            location (str): 地点
            temperature (float): 摄氏温度
            pH (float): 水体酸碱度
            pm25 (float): PM2.5 浓度
            remarks (str): 备注信息
            device (str): 录入设备名(即 computer_name)

    """
    def __init__(self,timestamp: Timestamp,location: str,temperature_celsius: float,
                 pH: float,pm25: float,remarks: str,computer_name: str,record_id=None):
        
        self.timestamp = pd.Timestamp(timestamp)
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
        timestamp = pd.Timestamp(data[0])
        return MonitorRecord(
            
            timestamp=timestamp,
            location=data[2],
            temperature=float(data[3]),
            pH=float(data[4]),
            pm25=float(data[5]),
            remarks=data[6],
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
        self._data = None # 数据缓存

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

    
    def read_all_records(self, refresh: bool = False) -> pd.DataFrame:
        """
        读取所有记录并返回一个DataFrame

        如果已经加载了数据且不需要刷新，则直接返回缓存的数据副本
        如果数据文件不存在,则创建并返回一个空的DataFrame。
        否则,读取CSV文件中的数据,转换时间戳列的数据类型,并移除所有字符串类型的前后空格。

        Attributes:
        refresh (bool): 是否强制刷新并重新读取数据,默认为False

        return:
        pd.DataFrame: 包含所有记录的DataFrame。
    """
        if self._data is not None and not refresh:
            return self._data  # 返回缓存副本

        if not os.path.exists(self.filepath):
            self._data = pd.DataFrame()
            return self._data

        df = pd.read_csv(self.filepath)

        # 转换时间列
        if '时间戳' in df.columns:
            df['时间戳'] = pd.to_datetime(df['时间戳'], errors='coerce')

        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

        self._data = df
        return self._data
    
    def save_dataframe(self, df: pd.DataFrame, to_path=None):
        """
        保存 DataFrame 到文件
        """
        path = to_path or self.filepath
        df.to_csv(path, index=False)
        print(f"数据已保存至 {path}")

    def sort_and_save(self, field: str, ascending=True, to_path=None):
        """
        对文件中的记录排序并保存（覆盖或另存）
        """
        df = self.read_all_records()
        if field not in df.columns:
            raise ValueError(f"字段 {field} 不存在")
        df = df.sort_values(by=field, ascending=ascending)
        self.save_dataframe(df, to_path)

    def filter_and_save(self, location=None, start_time=None, end_time=None, to_path=None):
        """
        筛选数据并保存
        """
        df = self.read_all_records()
        if location:
            df = df[df['地点'] == location]
        if start_time and end_time:
            df = df[(df['时间戳'] >= start_time) & (df['时间戳'] <= end_time)]
        self.save_dataframe(df, to_path)
    
    


class RecordViewer(object):
    def __init__(self, manager: CSVManager):
        self.manager = manager  
        self.sort_field = None
        self.sort_ascending = True

    def refresh_data(self):
        """刷新数据"""
        self.current_df = self.manager.read_all_records(refresh=True)

    def view_records(self, sort_by=None, ascending=True, start_time=None, end_time=None, location=None):
        """
        查看记录，支持筛选+排序组合操作

        arguments:
            sort_by (str): 排序字段，可选 ['时间戳', '温度', 'pH', 'pm2.5']
            ascending (bool): 是否升序，默认 True
            start_time (pd.Timestamp): 筛选起始时间
            end_time (pd.Timestamp): 筛选结束时间
            location (str): 筛选地点

        return:
            pd.DataFrame: 处理后的数据框
        """
        df = self.manager.read_all_records(refresh=True)

        if df.empty:
            print("当前没有可用数据。")
            return df

        # 时间范围筛选
        if start_time and end_time:
            df = df[(df['时间戳'] >= start_time) & (df['时间戳'] <= end_time)]

        # 地点筛选
        if location:
            df = df[df['地点'] == location]

        # 排序
        if sort_by:
            if sort_by not in df.columns:
                raise ValueError(f"字段 '{sort_by}' 不存在于数据中")
            df = df.sort_values(by=sort_by, ascending=ascending)

        return df.reset_index(drop=True).copy()
    
    
    def display_records(self, df=None):
        """显示记录"""
        if df is None:
            df = self.current_df
            
        if df.empty:
            print("没有可显示的数据")
            return
        
        # 打印表头
        print("\n" + " | ".join(df.columns))
        print("-" * 60)
        
        # 打印每一行数据
        for _, row in df.iterrows():
            print(" | ".join(str(val) for val in row.values))




def User_inputdata(): # 用户输入数据
    """
    交互式地获取用户输入的环保监测数据
    
    Returns:
        MonitorRecord: 包含用户输入数据的记录对象
    """

    

    while True:
        time_str = input("请输入时间(YYYY-MM-DD HH:MM)，留空则使用当前时间：").strip()
        if time_str == "":
            timestamp = Timestamp.now()
            break
        try:
            timestamp = Timestamp(time_str)
            break
        except Exception:
            print("时间格式错误，请重新输入")


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
    
    manager = CSVManager(default_file_path)

    record = User_inputdata()

    manager.save_record_pd(record)

def get_date_range():
    """获取用户输入的有效日期范围"""
    while True:
        start_str = input("请输入开始时间(YYYY-MM-DD HH:MM): ").strip()
        try:
            start = pd.Timestamp(start_str)
            break
        except Exception:
            print("开始时间格式错误，请重新输入")

    while True:
        end_str = input("请输入结束时间(YYYY-MM-DD HH:MM): ").strip()
        try:
            end = pd.Timestamp(end_str)
            if end >= start:
                break
            print("结束时间不能早于开始时间，请重新输入")
        except Exception:
            print("结束时间格式错误，请重新输入")
            
    return start, end
def combined_filter_sort_submenu(viewer):
    """同时进行筛选和排序"""
    viewer.refresh_data()
    
    # 先进行筛选
    print("请先设置筛选条件（可跳过）")
    has_filter = input("是否需要筛选？(y/n): ").lower() == 'y'
    
    start, end, location = None, None, None
    if has_filter:
        print("\n请选择筛选类型：")
        print("1. 时间筛选")
        print("2. 地点筛选")
        print("3. 时间和地点筛选")
        
        choice = input("请选择筛选类型(1-3): ")
        if choice == '1':
            start, end = get_date_range()
        elif choice == '2':
            location = input("请输入地点: ").strip()
        elif choice == '3':
            location = input("请输入地点: ").strip()
            start, end = get_date_range()
    
    # 再进行排序
    print("\n请选择排序设置")
    columns = {'1': '时间戳', '2': '温度', '3': 'pH', '4': 'pm2.5'}
    
    print("排序字段选项：")
    print("1. 时间戳")
    print("2. 温度")
    print("3. pH值") 
    print("4. PM2.5")
    
    choice = input("请选择排序字段(1-4): ")
    column = columns.get(choice)
    
    if not column:
        print("无效选择")
        return
        
    order = input("请选择排序方式(1:升序, 2:降序): ")
    ascending = order != '2'
    
    # 执行综合操作
    df = viewer.view_records(
        sort_by=column,
        ascending=ascending,
        start_time=start,
        end_time=end,
        location=location
    )
    
    viewer.display_records(df)
def sort_submenu(viewer):
    """排序子菜单"""
    columns = {'1': '时间戳', '2': '温度', '3': 'pH', '4': 'pm2.5'}
    
    print("\n=== 排序字段 ===")
    print("1. 时间戳")
    print("2. 温度")
    print("3. pH值")
    print("4. PM2.5")
    
    choice = input("请选择排序字段(1-4): ")
    column = columns.get(choice)
    
    if not column:
        print("无效选择")
        return
        
    order = input("请选择排序方式(1:升序, 2:降序): ")
    ascending = order != '2'
    
    viewer.refresh_data()  # 刷新数据
    df = viewer.view_records(sort_by=column, ascending=ascending)
    viewer.display_records(df)

def filter_submenu(viewer):
    """筛选子菜单"""
    while True:
        print("\n=== 筛选数据 ===")
        print("1. 按时间范围筛选")
        print("2. 按地点筛选")
        print("3. 同时按时间和地点筛选")
        print("b. 返回上一级")
        
        choice = input("请选择筛选方式: ").lower()
        
        if choice == 'b':
            return
            
        viewer.refresh_data()  # 先刷新数据
        
        if choice == '1':
            start, end = get_date_range()
            df = viewer.view_records(start_time=start, end_time=end)
            viewer.display_records(df)
            
        elif choice == '2':
            location = input("请输入要筛选的地点: ").strip()
            df = viewer.view_records(location=location)
            viewer.display_records(df)
            
        elif choice == '3':
            location = input("请输入要筛选的地点: ").strip()
            print("\n请输入筛选的时间范围：")
            start, end = get_date_range()
            df = viewer.view_records(start_time=start, end_time=end, location=location)
            viewer.display_records(df)
            
        else:
            print("无效选项，请重新输入")
def view_record_menu():
    """查看记录主菜单"""
    # 创建CSVManager实例
    manager = CSVManager("D:\\ProjectsHub\\eco_monitoring_sys_hw\\Data\\monitor_data.csv")
    viewer = RecordViewer(manager)
    
    while True:
        print("\n=== 查看记录 ===")
        print("1. 显示所有数据")
        print("2. 按条件筛选")
        print("3. 按条件排序")
        print("4. 综合筛选与排序")
        print("b. 返回主菜单")
        
        choice = input("请选择操作: ").lower()
        
        if choice == 'b':
            break
        elif choice == '1':
            viewer.refresh_data()
            viewer.display_records()
        elif choice == '2':
            filter_submenu(viewer)
        elif choice == '3':
            sort_submenu(viewer)
        elif choice == '4':
            combined_filter_sort_submenu(viewer)
        else:
            print("无效选项，请重新输入")


    
def main_menu():
    menu_option = {
        '1':("添加数据记录",add_record),
        '2':("查看数据记录",view_record_menu),
        '3':("预留位置",None),
        '4':("预留位置",None),
        '5':("退出程序",lambda: exit())
    }
    
    while True:
        print("\n===== 主菜单 =====")
        for key, (desc, func) in menu_option.items():
            print(f"{key}. {desc}")

        choice = input("请选择操作: ").strip()

        if choice not in menu_option:
            print("无效操作输入，请重试")
            continue

        func = menu_option[choice][1]
        if func is None:
            print("该功能暂未实现，请选择其他选项")
        else:
            try:
                func()
            except Exception as e:
                print(f"执行过程中发生错误: {e}")
        

    

if __name__ == "__main__":
    main_menu()
