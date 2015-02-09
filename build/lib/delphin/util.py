
def safe_int(x):
    try:
        x = int(x)
    except ValueError:
        pass
    return x