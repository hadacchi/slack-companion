def dump_log(msg, logger=None, level='info'):
    if logger is not None:
        if level == 'debug':
            logger.debug(msg)
            return
        elif level == 'info':
            logger.info(msg)
            return
        elif level == 'error':
            logger.error(msg)
            return
