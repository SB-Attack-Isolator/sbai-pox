"""
Global variable sharing module
Author: Shenghua Chen
Version: Aug 30th, 2023
"""

LOGGER_KEY = "logger"
ATTACKER_KEY = "attacker"
CONTROLLER_MESSAGE_QUEUE_KEY = "controller_message_queue"

def __init__():
    global _shared_var
    if not("_shared_var" in globals() and _shared_var is dict):
        _shared_var = {}

def set_lock(key, lock):
    global _shared_var
    # get old lock object
    if key in _shared_var:
        value, _lock = _shared_var[key]
    else:
        _lock = None
        value = None
    # Check if need to unlock
    if _lock is None:
        _shared_var[key] = (value, lock)
    else:
        _lock.acquire()
        _shared_var[key] = (value, lock)
        _lock.release()

def set_var(key, value):
    global _shared_var
    # get old lock object
    if key in _shared_var:
        _, lock = _shared_var[key]
    else:
        lock = None
    # Check if need to unlock
    if lock is None:
        _shared_var[key] = (value, lock)
    else:
        lock.acquire()
        _shared_var[key] = (value, lock)
        lock.release()

def get_var(key, useLock = False):
    global _shared_var
    # Lock
    _, lock = _shared_var[key]
    if useLock and lock is not None:
        lock.acquire()
    # Get varible
    if key in _shared_var:
        result, _ = _shared_var[key]
    else:
        result = None
    # Release lock
    if useLock and lock is not None:
        lock.release()
    # Return result
    return result

__init__()
