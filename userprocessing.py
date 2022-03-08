def get_users(client, logger):
    res = client.users_list()
    for r in res['members']:
        logger.info(str(r))
