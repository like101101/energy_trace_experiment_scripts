bytes_object = bytes.fromhex('0A')
ascii_string = bytes_object.decode("ASCII")
print(ascii_string)

f = open("hello_http.cc", "r")

for line in f:
    if '0x' in line:
        tmp = line.strip().split(',')
        for s in tmp:            
            if len(s) > 0:
                hexv = (s.strip())[2:]
                if len(hexv) == 1:
                    hexv = '0'+hexv
                    #print('hexv = ', len(hexv), str(hexv))
                bytes_object = bytes.fromhex(str(hexv))
                ascii_string = bytes_object.decode("ASCII")
                print(ascii_string, end='')
f.close()
