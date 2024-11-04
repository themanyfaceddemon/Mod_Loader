import logging


class ErrorHandler:
    @staticmethod
    def global_exception_handler(exctype, value, traceback_obj):
        logging.error("Exception occurred", exc_info=(exctype, value, traceback_obj))
