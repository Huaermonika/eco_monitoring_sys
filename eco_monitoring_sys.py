# -*- coding: utf-8 -*-
"""
Project Name: eco_monitoring_sys(环境监测数据记录与分析系统)
File Description: 负责录入、存储环保监测数据，生成 CSV 文件
Date: 2025-06-15
Author: 杨澍
Version: v1.2

"""

import pandas as pd
from pandas import Timestamp
import matplotlib.patches as plt
import numpy as np

import socket
import os
import datetime




# 获取计算机名称
computer_name = socket.gethostname() 

# 定义常量类
default_file_path = 'D:\\ProjectsHub\\eco_monitoring_sys_hw\\Data\\monitor_data.csv'


# 工具函数

def to_timestamp(value) -> pd.Timestamp:
    """
    将字符串时间转换为 Timestamp 对象
    """
    return pd.Timestamp(value)

def now_timestamp() -> pd.Timestamp:
    """
    获取当前时间戳
    """
    return pd.Timestamp.now()

def get_date_input(prompt):
    """
    通用时间输入函数,用于解析用户输入的日期时间
    """
    while True:
        date_str = input(prompt).strip()
        try:
            return pd.Timestamp(date_str)
        except Exception:
            print("时间格式错误，请重新输入 (YYYY-MM-DD HH:MM)")





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
            
            self.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
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
            location=data[1],
            temperature=float(data[2]),
            pH=float(data[3]),
            pm25=float(data[4]),
            remarks=data[5],
            computer_name=data[6],
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
        如果数据文件不存在,则创建并返回一个空的DataFrame
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

        df = df.map(lambda x: x.strip() if isinstance(x, str) else x)

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
        对文件中的记录排序并保存(覆盖或另存)
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

    def reindex_records(self):
        """
        重新编写 CSV 文件中的 ID 为连续的数列
        """
        df = self.read_all_records(refresh=True)

        if 'ID' not in df.columns:
            print("没有 'ID' 字段，无法重新编号")
            return

        # 重新编写 ID 为连续数列
        df['ID'] = range(1, len(df) + 1)
        self.save_dataframe(df)
        print("ID 已重新编号。")

    def modify_record_by_id(self, record_id: int, new_data: dict):
        """
        用新的字段值覆盖指定 ID 的整行记录

        参数:
        - record_id: 要修改的记录 ID(索引)
        - new_data: dict 类型的新数据,key 是字段名
        """
        df = self.read_all_records(refresh=True)

        if record_id not in df.index:
            raise ValueError(f"未找到 ID 为 {record_id} 的记录")

        for key in new_data:
            if key not in df.columns:
                raise ValueError(f"字段 {key} 不存在于记录中")

        for key, value in new_data.items():
            df.at[record_id, key] = value

        self.save_dataframe(df)

    def clear_all_records(self):
        """
        清空 CSV 文件中的所有数据（保留列结构）
        """
        confirm = input("确定要清空所有数据吗?该操作不可恢复!(输入 yes 确认): ").strip().lower()
        if confirm != 'yes':
            print("操作已取消。")
            return
        columns = ['ID', '时间戳', '地点', '温度', 'pH', 'pm2.5', '备注', '录入设备']
        df = pd.DataFrame(columns=columns)
        self.save_dataframe(df)
        print("所有记录已清空。")
    
    


class RecordViewer(object):
    def __init__(self, manager: CSVManager):
        self.manager = manager  
        self.sort_field = None
        self.sort_ascending = True

    def refresh_data(self):
        """
        刷新数据
        """
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
            print("当前没有可用数据")
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
        """
        显示记录
        """
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
            timestamp = now_timestamp()
            break
        try:
            timestamp = Timestamp(time_str)
            break
        except Exception:
            print("时间格式错误，请重新输入")


    location = input("请输入地点：").strip()
    
    while True:
        try:
            temperature_celsius = float(input("请输入温度(℃):"))
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



#用户操作UI与功能实现
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
    """
    获取用户输入的起始与结束时间
    """
    start = get_date_input("请输入开始时间(YYYY-MM-DD HH:MM): ")
    while True:
        end = get_date_input("请输入结束时间(YYYY-MM-DD HH:MM): ")
        if end >= start:
            return start, end
        print("结束时间不能早于开始时间,请重新输入")

def get_sort_settings():
    """
    获取排序字段和排序顺序(升序/降序)
    """
    columns = {'1': '时间戳', '2': '温度', '3': 'pH', '4': 'pm2.5'}
    print("\n=== 排序字段选项 ===")
    for k, v in columns.items():
        print(f"{k}. {v}")
        
    choice = input("请选择排序字段(1-4): ")
    column = columns.get(choice)
    if not column:
        print("无效选择")
        return None, None

    order = input("请选择排序方式(1:升序, 2:降序): ")
    ascending = (order != '2')
    return column, ascending

def filter_data(viewer: RecordViewer, filter_type):
    """
    根据用户选择的筛选类型执行筛选操作
    
    arguments:
        viewer: 记录查看器对象
        filter_type: str,筛选类型(1-时间,2-地点,3-时间和地点)
    """
    start, end, location = None, None, None

    if filter_type == '1':
        start, end = get_date_range()
    elif filter_type == '2':
        location = input("请输入要筛选的地点: ").strip()
    elif filter_type == '3':
        location = input("请输入要筛选的地点: ").strip()
        print("\n请输入筛选的时间范围: ")
        start, end = get_date_range()

    viewer.refresh_data()
    df = viewer.view_records(start_time=start, end_time=end, location=location)
    viewer.display_records(df)

def filter_submenu(viewer):
    """
    筛选子菜单,提供三种筛选方式
    """
    
    while True:
        print("\n=== 筛选数据 ===")
        print("1. 按时间范围筛选")
        print("2. 按地点筛选")
        print("3. 时间和地点同时筛选")
        print("b. 返回上一级")
        
        choice = input("请选择筛选方式: ").lower()
        if choice == 'b':
            break
        elif choice in ['1', '2', '3']:
            filter_data(viewer, choice)
        else:
            print("无效选项，请重新输入")

def sort_submenu(viewer: RecordViewer):
    """
    排序子菜单,用户选择排序字段和顺序
    """
    column, ascending = get_sort_settings()
    if column:
        viewer.refresh_data()
        df = viewer.view_records(sort_by=column, ascending=ascending)
        viewer.display_records(df)

def combined_filter_sort_submenu(viewer: RecordViewer):
    """
    组合筛选与排序子菜单,先筛选再排序
    """
    viewer.refresh_data()
    print("\n请设置筛选条件(可跳过)")
    use_filter = input("是否需要筛选？(y/n): ").lower() == 'y'

    start, end, location = None, None, None
    if use_filter:
        print("\n1. 时间筛选\n2. 地点筛选\n3. 时间+地点筛选")
        choice = input("请选择筛选类型(1-3): ")
        if choice in ['1', '2', '3']:
            if choice in ['1', '3']:
                start, end = get_date_range()
            if choice in ['2', '3']:
                location = input("请输入地点: ").strip()
        else:
            print("无效筛选类型")
            return

    column, ascending = get_sort_settings()
    if column:
        df = viewer.view_records(
            sort_by=column,
            ascending=ascending,
            start_time=start,
            end_time=end,
            location=location
        )
        viewer.display_records(df)

def search_by_keyword(viewer: RecordViewer):
    """
    按关键词模糊搜索数据（在所有字段中）
    """
    keyword = input("请输入搜索关键词: ").strip().lower()
    if not keyword:
        print("关键词不能为空")
        return

    viewer.refresh_data()
    df = viewer.current_df

    mask = df.apply(lambda row: row.astype(str).str.lower().str.contains(keyword).any(), axis=1)
    result_df = df[mask]

    if result_df.empty:
        print("未找到匹配的数据")
    else:
        print(f"\n找到 {len(result_df)} 条匹配结果：")
        viewer.display_records(result_df)

def modify_partial_record(manager: CSVManager):
    df = manager.read_all_records(refresh=True)
    if df.empty:
        print("无记录可修改。")
        return

    try:
        record_id = int(input("请输入要修改的记录 ID: ").strip())
    except ValueError:
        print("ID 输入错误！")
        return

    if record_id not in df.index:
        print("找不到该 ID 的记录。")
        return

    print(f"\n当前记录:\n{df.loc[record_id]}\n")

    new_data = {}
    for col in df.columns:
        if col == 'ID':
            continue  # ID 不允许改
        current_value = df.at[record_id, col]
        user_input = input(f"输入新的 {col}(留空则保留当前值：{current_value}):").strip()
        if user_input == "":
            new_data[col] = current_value
        else:
            # 类型转换
            if col in ['温度', 'pH', 'pm2.5']:
                try:
                    user_input = float(user_input)
                except ValueError:
                    print(f"{col} 不是合法数字，已保留原值。")
                    user_input = current_value
            elif col == '时间戳':
                try:
                    user_input = pd.Timestamp(user_input)
                except Exception:
                    print("时间戳格式错误，已保留原值。")
                    user_input = current_value
            new_data[col] = user_input

    try:
        manager.modify_record_by_id(record_id, new_data)
        print("记录已成功更新。")
    except Exception as e:
        print(f"修改失败：{e}")

def view_record_menu():
    """
    查看记录的主菜单,包含显示、筛选、排序等功能
    """
    manager = CSVManager(default_file_path)
    viewer = RecordViewer(manager)

    while True:
        print("\n=== 查看记录菜单 ===")
        print("1. 显示所有数据")
        print("2. 筛选数据")
        print("3. 排序数据")
        print("4. 综合筛选与排序")
        print("5.关键词模糊检索")
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
        elif choice == '5':
            search_by_keyword(viewer)
        else:
            print("无效选项，请重新输入")

def delete_by_index(manager: CSVManager):
    df = manager.read_all_records(refresh=True)

    if df.empty:
        print("数据为空，无法删除。")
        return

    print("\n当前数据如下:")
    print(df)

    try:
        index = int(input("请输入要删除的索引 ID:").strip())
        if index not in df.index:
            print("无效索引，请检查后再试。")
            return
    except ValueError:
        print("输入不是有效的数字索引。")
        return

    print("\n你将要删除以下记录:")
    print(df.loc[[index]])

    confirm = input("确认删除？(y/n): ").lower()
    if confirm == 'y':
        df = df.drop(index)
        manager.save_dataframe(df)
        print("删除成功。")
    else:
        print("操作已取消。")

def manage_records_menu():
    manager = CSVManager(default_file_path)
    viewer = RecordViewer(manager)

    while True:
        print("\n======  数据记录管理子菜单 ======")
        print("1. 按索引删除数据")
        print("2. 重新编写 ID(顺序重排)")
        print("3. 覆盖保存到 CSV 文件")
        print("4. 修改部分字段（局部修改）")
        print("5. 清空全部记录 ")
        print("b. 返回主菜单")
        print("===================================")
        choice = input("请输入操作编号：").strip()

        if choice == "1":
            delete_by_index(manager)
        elif choice == "2":
            manager.reindex_records()
        elif choice == "3":
            df = manager.read_all_records()
            manager.save_dataframe(df)
        elif choice == "4":
            modify_partial_record(manager)
        elif choice == "5":
            manager.clear_all_records()
        elif choice.lower() == "b":
            print("返回主菜单...")
            break
        else:
            print("无效输入，请重试。")



#主选单
def main_menu():
    menu_option = {
        '1':("添加数据记录",add_record),
        '2':("查看数据记录",view_record_menu),
        '3':("进行数据操作",manage_records_menu),
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
