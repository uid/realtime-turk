from boto.mturk import connection

import logging

import settings

def get_mt_conn(sandbox=settings.SANDBOX):
    """
    returns a connection to mechanical turk.
    requires that settings defines the following variables:
    
    settings.SANDBOX:    True|False
    settings.aws_id:     your aws id
    settings.aws_secret: your aws secret key
    """
    if sandbox:
        host="mechanicalturk.sandbox.amazonaws.com"
    else:
        host="mechanicalturk.amazonaws.com"

    return connection.MTurkConnection(
        aws_access_key_id=settings.aws_id,
        aws_secret_access_key=settings.aws_secret,
        host=host)
