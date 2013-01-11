from retainer.models import *

def checkRequestParams(request, paramNames):
    if request.method != 'POST': return False
    params = request.POST
    for p in paramNames:
        if not p in params and p != 'apiKey':
            return False
    if 'apiKey' in paramNames and APIKey.needed():
        if not 'apiKey' in params:
            return False
        else: # key supplied, check it:
            return APIKey.check(params['apiKey'])
    else: 
        return True