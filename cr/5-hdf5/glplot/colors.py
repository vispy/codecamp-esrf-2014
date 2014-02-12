def get_color(char):
    if char=='r':
        return (1,0,0)
    elif char=='g':
        return (0,1,0)
    elif char=='b':
        return (0,0,1)
    elif char=='y':
        return (1,1,0)
    elif char=='c':
        return (0,1,1)
    elif char=='m':
        return (1,0,1)
    elif char=='w':
        return (1,1,1)
        
LINECOLORS = [get_color(c) for c in "yrgcmwb"]
