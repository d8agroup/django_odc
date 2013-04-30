from os import path
import os
from threading import Thread


def async(gen):
    def func(*args, **kwargs):
        it = gen(*args, **kwargs)
        result = it.next()
        Thread(target=lambda: list(it)).start()
        return result
    return func


def format_error(e, exc_info):
    exc_type, exc_obj, exc_tb = exc_info
    file_name = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
    error = ', '.join(['%s' % x for x in [e, exc_type, file_name, exc_tb.tb_lineno]])
    #error = ', '.join([type(e).__name__, path.basename(top_of_stack[0]), str(top_of_stack[1])])
    return error
