# 频谱分析
# # 傅里叶变换，将时域数据转为频域数据!
# 2021.8.9

import sys
import numpy as np
from scipy.fftpack import fft, ifft
import matplotlib.pyplot as plt

def stop_err(msg):
    sys.stderr.write(msg)
    sys.exit()


def __main__():
    try:
        infile = sys.argv[1]
        shz = int(sys.argv[2])
        outfile = sys.argv[3]
    except:
        stop_err("无法打开或创建文件失败！")
    pass

    in_content = [[] for i in range(12)]

    with open(infile, 'r') as f:
        f.readline()  # 读取标题
        for line in f:
            items = line.split()  # 线上环境，不填参数
            for index, itm in enumerate(items):
                in_content[index].append(float(itm))
                pass
            pass
    clr_content = [col for col in in_content if col] #清除空列

    fft_ys = []#傅里叶
    for col in clr_content:
        fft_y = fft(col)
        fft_ys.append(fft_y)
        pass

    abs_ys = []#绝对值
    for col in fft_ys:
        abs_y = np.abs(col)
        abs_ys.append(abs_y)
        pass

    nor_ys = [] #归一化
    for col in abs_ys:
        nor_y = col/shz
        nor_ys.append(nor_y)
        pass


    with open(outfile,'w') as f:
        if len(nor_ys)>0 and len(nor_ys[0])>0:
            row_num = len(nor_ys[0])
        for row in range(row_num):
            for col in nor_ys:
                f.write("%f\t"%col[row])
                pass
            f.write('\n')
            pass
        pass


if __name__ == "__main__":
    __main__()
    pass
