import logging
import toml

# load config file
config = toml.load(open('secret.toml'))

data_dir_path = config['resource']['data_dir_path']
log_filename = config['resource']['log_file']
log_file_path = f'{data_dir_path}/{log_filename}'
 
def setup_logging(loglevel=logging.INFO):
    '''アプリケーション全体のロギングを設定する

    Parameters
    ----------
    loglevel : int
        設定するログレベル
    '''
    logging.basicConfig(
        level=loglevel,
        format='%(asctime)s %(name)s: %(levelname)s: %(message)s',
        filename=log_file_path,
        filemode='a' # 追記モード
    )
    # slack-boltのログがたくさん出ちゃうのを抑えるおまじない！
    logging.getLogger("slack_bolt.App").setLevel(logging.WARNING)
