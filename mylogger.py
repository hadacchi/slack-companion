import logging
import toml

# load config file
config = toml.load(open('secret.toml'))

data_dir_path = config['resource']['data_dir_path']
log_filename = config['resource']['log_file']
log_file_path = f'{data_dir_path}/{log_filename}'

formatter = logging.Formatter('%(asctime)s %(module)s: %(levelname)s: %(message)s')

def logger_setup(logger, loglevel=logging.ERROR):
    '''set parameters into logger

    Parameters
    ----------
    logger : logging.Logger

    Return
    ------
    logger : logging.Logger
    '''

    if not logger.hasHandlers():
        logger.setLevel(loglevel)
        fh = logging.FileHandler(log_file_path)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger
