import subprocess
def get_xy():
    cmd = r'adb shell getevent'
    w = 0
    h = 0
    try:
        p1=subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE)
        for line in p1.stdout:
            line = line.decode(encoding="utf-8", errors="ignore")
            line = line.strip()
            if ' 0035 ' in line:
                e = line.split(" ")
                w = e[3]
                w = int(w, 16)
                
            if  ' 0036 ' in line:
                e = line.split(" ")
                h = e[3]
                h = int(h, 16)
                if h >0:
                    p = (w, h)
                    print(p) 
        p1.wait()
        
    except Exception as e:
        print(e)
size = get_xy()
print(size)
