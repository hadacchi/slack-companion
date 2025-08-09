import logging
import toml
from plugins.as_control.airstation import AirStationWebsite

logger = logging.getLogger(__name__)

SUBCOMMANDS = ['devices', 'del', 'add', 'delmac', 'addmac']

def run(attrs, say, config):
    '''
    @BOTNAME ap
        devices
        del DEVNAME
        add DEVNAME
        delmac MACADDR
        addmac MACADDR
    '''

    logger.info(f'ap runs: {attrs}')
    ap_config_file = config['config_file']

    if attrs is None:
        logger.error('This plugin requires SUBCOMMAND.')
        say(msgs.error())
        return False

    #say(msgs.confirm())

    # サブコマンドで振り分け
    subcommand = attrs[0]

    if subcommand not in SUBCOMMANDS:
        logger.error('Invalid subcommand: ' + subcommand)
        say(msgs.error())
        return False

    if subcommand == 'devices':
        # デバイスリストを返却する処理
        ASsite = AirStationWebsite(ap_config_file)
        try:
            devices = ASsite.get_registered_devices()
            say(str(devices))
        except Exception as e:
            say(str(e))
            logger.error(str(e))
        ASsite.exit()
    elif subcommand == 'delmac':
        # del macaddr
        ASsite = AirStationWebsite(ap_config_file)
        try:
            if ASsite.del_mac_addr(attrs[1]):
                say(msgs.finish())
            else:
                say(msgs.error())
                logger.error('del_mac_addr returns False')
        except Exception as e:
            say(str(e))
            logger.error(str(e))
        ASsite.exit()
    elif subcommand == 'addmac':
        # add macaddr
        ASsite = AirStationWebsite(ap_config_file)
        try:
            if ASsite.add_mac_addr(attrs[1]):
                say(msgs.finish())
            else:
                say(msgs.error())
                logger.error('add_mac_addr returns False')
        except Exception as e:
            say(str(e))
            logger.error(str(e))
        ASsite.exit()
    elif match.find('del') >= 0:
        # del device
        ASsite = AirStationWebsite(ap_config_file)
        try:
            if ASsite.del_device(' '.join(attrs[1:])):
                say(msgs.finish())
            else:
                say(msgs.error())
                logger.error('del_device returns False')
        except Exception as e:
            say(str(e))
            logger.error(str(e))
        ASsite.exit()
    elif match.find('add') >= 0:
        # add device
        ASsite = AirStationWebsite(ap_config_file)
        try:
            if ASsite.add_device(' '.join(attrs[1:])):
                say(msgs.finish())
            else:
                say(msgs.error())
                logger.error('add_device returns False')
        except Exception as e:
            say(str(e))
            logger.error(str(e))
        ASsite.exit()
    return True