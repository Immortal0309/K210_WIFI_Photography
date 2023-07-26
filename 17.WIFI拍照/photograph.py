import sensor, lcd, utime
from Maix import GPIO
from fpioa_manager import fm

import network, usocket, time
from machine import UART,Timer

SSID = 'dianke516' # WiFi 账号
KEY  = 'dianke516'  # WiFi 密码
# socket数据接收中断标志位
socket_node = 0
key_node = 0  # 按键标志位
name_num = 0  # 照片名字

# WiFi使能函数
def wifi_enable(en):
  global wifi_en
  wifi_en.value(en)

# WiFi对象初始化，波特率需要修改
def wifi_init():
  global uart
  wifi_enable(0)
  time.sleep_ms(200)
  wifi_enable(1)
  time.sleep(2)
  uart = UART(UART.UART2, 115200, timeout=1000, read_buf_len = 4096)
  tmp = uart.read()
  uart.write("AT+UART_CUR=921600,8,1,0,0\r\n")
  print(uart.read())
  uart = UART(UART.UART2, 921600, timeout=1000, read_buf_len = 10240) #实测模块波特率太低或者缓存长度太短会导致数据丢失。
  uart.write("AT\r\n")
  tmp = uart.read()
  print(tmp)

  if not tmp.endswith("OK\r\n"):
    print("reset fail")
    return None
  try:
    nic = network.ESP8285(uart)
  except Exception:
    return None
  return nic

# 定时器回调函数
def fun(tim):
  global socket_node
  socket_node = 1  # 改变socket标志位

# WiFi模块使能引脚初始化
fm.register(8, fm.fpioa.GPIOHS0, force=True)
wifi_en = GPIO(GPIO.GPIOHS0, GPIO.OUT)

# 串口初始化
fm.register(7, fm.fpioa.UART2_TX, force = True)
fm.register(6, fm.fpioa.UART2_RX, force = True)
uart = UART(UART.UART2, 115200, timeout = 1000, read_buf_len = 4096)

# 摄像头初始化
sensor.reset() # Initialize the camera sensor.
sensor.set_pixformat(sensor.RGB565) # or sensor.GRAYSCALE
sensor.set_framesize(sensor.QVGA) # or sensor.QVGA (or others)
sensor.skip_frames(30) # Let new settings take affect.
sensor.set_windowing((224, 224))
sensor.set_vflip(1)    # 摄像头后置模式

# 构建WiFi对象并使能
wlan = wifi_init()
# 正在连接印提示
print("Trying to connect... (may take a while)...")
# 连接网络
wlan.connect(SSID, KEY)
# 打印IP相关信息
print(wlan.ifconfig())

# 创建socket连接，连接成功后发送“Hello 01Studio！”给服务器。
client = usocket.socket()
addr = ('192.168.31.162', 8080) # 服务器IP和端口
client.connect(addr)
client.send('Init success!')
client.settimeout(0.1)

# 定时器0初始化，周期100ms
tim = Timer(Timer.TIMER0, Timer.CHANNEL0, mode=Timer.MODE_PERIODIC,
            period=100, callback=fun)

while True:
  sensor.snapshot()

  if socket_node:
    try:
      data = client.recv(256)
      data = data.decode()
    except OSError:
      data = None
    if data == "aa":
      print("rcv:", data)
      #拍照并保存，保存文件用时间来命名。
      sensor.snapshot().save("/sd/"+str(name_num)+"a.jpg")
      name_num = name_num+1 #名字编码加1
      print(name_num)
      print("Done! Reset the camera to see the saved image.")

    socket_node = 0
  else:
    pass
