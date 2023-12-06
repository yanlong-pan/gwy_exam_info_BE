import threading


def Singleton(cls):
    _instance_lock = threading.Lock()
    _instance = {}

    def _singleton(*args, **kargs):
        if cls not in _instance:
            with _instance_lock:
                if cls not in _instance:
                    _instance[cls] = cls(*args, **kargs)
        return _instance[cls]

    return _singleton