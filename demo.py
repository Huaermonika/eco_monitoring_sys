import csv
data = [
    {'id':1,'name':'dog',"age":18},
    {'id':2,'name':'cat',"age":19},
    {'id':3,'name':'dog',"age":20},
]
f = open('test1.csv','a',encoding='utf8',newline='')  # 指定newline=‘’参数
writer = csv.DictWriter(f,fieldnames=['id','name','age'])
writer.writeheader() # 将字段写入csv格式文件首行
for line in data:
    writer.writerow(line)
