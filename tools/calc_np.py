import os
from os import path
import sys
import math

ITERS = 5000
BITS = 8            
TCP_HDR = 32         # 20 bytes + 12 bytes option header
IP_HDR =  20
ETH_HEADER = 18      # 14 bytes ethernet header + 4 byte frame check sequence
LINK_SPEED = 10000   # 10,000 bits/usec
MSS = 1460           # MAX PAYLOAD SIZE
 
print(len(sys.argv), sys.argv)
if len(sys.argv) != 3:
    print("calc_np.py <msg_bytes> <os_cost>")
    exit()

msg_bytes = int(sys.argv[1])
os_cost = float(sys.argv[2])

total_header_bits = (ETH_HEADER+IP_HDR+TCP_HDR)*BITS

msg_bits = msg_bytes*BITS
num_frames = math.ceil(msg_bytes/MSS)
total_bits = msg_bits+ (total_header_bits*num_frames)

print("NO OS:", msg_bytes, "bytes (", total_bits," bits w/ headers) will take", total_bits/LINK_SPEED, "usecs")
