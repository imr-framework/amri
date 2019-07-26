def log(msg: str, endline: str = '\n', verbose: bool = True):
    if verbose:
        print(msg, end=endline, flush=True)
