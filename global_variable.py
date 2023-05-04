"""
Global variable sharing module
Author: Shenghua Chen
Version: Aug 30th, 2023
"""

import threading

LOGGER_KEY = "logger"
ATTACKER_KEY = "attacker"
CONTROLLER_MESSAGE_QUEUE_KEY = "controller_message_queue"

def __init__():
    """
    Initializes the shared variable dictionary if it is not already created.
    """
    global _shared_var
    if not("_shared_var" in globals() and _shared_var is dict):
        _shared_var = {}

    set_lock(LOGGER_KEY, threading.Lock())
    set_lock(ATTACKER_KEY, threading.Lock())
    set_lock(CONTROLLER_MESSAGE_QUEUE_KEY, threading.Lock())
    

def lock_var(key):
    """
    Acquires the lock for a given key in the shared variable dictionary.

    Args:
        key (str): The key for the variable to lock.

    Raises:
        Exception: If the variable does not have a lock object.
    """
    global _shared_var
    # get old lock object
    if key in _shared_var:
        _, lock = _shared_var[key]
    else:
        lock = None
    
    if lock is None:
        raise Exception("Try to lock varible without a lock")
    else:
        lock.acquire()

def release_var(key):
    """
    Releases the lock for a given key in the shared variable dictionary.

    Args:
        key (str): The key for the variable to unlock.

    Raises:
        Exception: If the variable does not have a lock object.
    """
    global _shared_var
    # get old lock object
    if key in _shared_var:
        _, lock = _shared_var[key]
    else:
        lock = None
    
    if lock is None:
        raise Exception("Try to unlock varible without a lock")
    else:
        lock.release()


def safe_rw(key,f_process):
    """
    Safely reads and writes to a given key in the shared variable dictionary using a lock.

    Args:
        key (str): The key for the variable to read and write.
        f_process (function): The function to process the value of the variable.
                              Get one parameter as original value, returns new
                              value.

    """
    global _shared_var
    # get old lock object
    if key in _shared_var:
        _, lock = _shared_var[key]
    else:
        lock = None
    # Check if need to unlock
    result, _ = value[key]
    if lock is None:
        _shared_var[key] = (f_process(value), lock)
    else:
        lock.acquire()
        _shared_var[key] = (value, lock)
        lock.release()

def set_lock(key, lock):
    """
    Sets a lock object for a given key in the shared variable dictionary.

    Args:
        key (str): The key for the variable to set a lock object.
        lock (threading.Lock): The lock object to set.
    """
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

def set_var(key, value, useLock = False):
    global _shared_var
    # get old lock object
    if key in _shared_var:
        _, lock = _shared_var[key]
    else:
        lock = None
    # Check if need to unlock
    if not useLock or lock is None:
        _shared_var[key] = (value, lock)
    else:
        lock.acquire()
        _shared_var[key] = (value, lock)
        lock.release()

def get_var(key, useLock = False):
    """
    Sets the value for a given key in the shared variable dictionary.

    Args:
        key (str): The key for the variable to set.
        value (Any): The value to set for the variable.
    """
    global _shared_var
    # Lock
    if useLock:
        _, lock = _shared_var[key]
    else:
        lock = None
    if lock is not None:
        lock.acquire()
    # Get varible
    if key in _shared_var:
        result, _ = _shared_var[key]
    else:
        result = None
    # Release lock
    if lock is not None:
        lock.release()
    # Return result
    return result

__init__()
