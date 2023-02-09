def get_users(client, logger):
    dump_log('get_users called', logger)

    res = client.users_list()
    for r in res['members']:
        dump_log(str(r), logger, 'debug')
