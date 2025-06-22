"""
A module for caching and retrieving computational results to disk.

This module provides utility functions to save and load intermediate processing results,
which helps avoid redundant computations and speeds up development iterations.
"""

import os 
import pickle

def save_stub(stub_path,object):
    """
    Save a Python object to disk at the specified path.

    Creates necessary directories if they don't exist and serializes the object using pickle.

    Args:
        stub_path (str): File path where the object should be saved.
        object: Any Python object that can be pickled.
    """
    if not os.path.exists(os.path.dirname(stub_path)):
        os.makedirs(os.path.dirname(stub_path))

    if stub_path is not None:
        with open(stub_path,'wb') as f:
            pickle.dump(object,f)

def read_stub(read_from_stub,stub_path):
    """
    Read a previously saved Python object from disk if available.

    Args:
        read_from_stub (bool): Whether to attempt reading from disk.
        stub_path (str): File path where the object was saved.

    Returns:
        object: The loaded Python object if successful, None otherwise.
    """
    if read_from_stub and stub_path is not None and os.path.exists(stub_path):
        try:
            with open(stub_path,'rb') as f:
                object = pickle.load(f)
                return object
        except (ModuleNotFoundError, ImportError, ValueError, EOFError) as e:
            # Handle numpy version incompatibilities and other pickle errors
            print(f"Warning: Could not load stub from {stub_path}: {e}")
            print("This usually happens due to numpy version incompatibility.")
            print("The stub will be regenerated during processing.")
            # Remove the corrupted stub file
            try:
                os.remove(stub_path)
                print(f"Removed corrupted stub file: {stub_path}")
            except:
                pass
            return None
    return None
    