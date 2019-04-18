# pyramco
# version 0.9.4 - ANNOTATED

# a complete wrapper class for RAMCO API calls
# requires Python 3.6+ and the 'requests' module
# set your RAMCO api key in a separate file 'config.py' as 'config.ramco_api_key'
# Documentation on the RAMCO API at:
# https://api.ramcoams.com/api/v2/ramco_api_v2_doc.pdf


# this line imports the information in the 'config.py' file for use in this script
import config
# this line imporst the 'requests' module, which is built-in to python
import requests
# this line imports the 'json' module, which is built-in to python
import json


## response code/error handling

# definitions
code_200 = {
    'DescriptionShort':'OK',
    'DescriptionVerbose':'The request was successfully processed and data is included in the response'
    }
code_204 = {
    'DescriptionShort':'OK: No Data',
    'DescriptionVerbose':'The request was successfully processed but no data is included in the response. This is typical of UpdateEntity requests.'
    }
code_206 = {
    'DescriptionShort':'OK: Partial Data',
    'DescriptionVerbose':'The request was successfully processed and partial data is included in the response. This is the expected response when the dataset that Ramco needs to return to the user is too large. A StreamToken will be returned to allow the user to fetch the remaining data.'
    }
code_400 = {
    'DescriptionShort':'Bad Request',
    'DescriptionVerbose':'The request was not understood. See the response text for more information.'
    }
code_401 = {
    'DescriptionShort':'Unauthorized',
    'DescriptionVerbose':'The request was understood but it will not be fulfilled due to a lack of user permissions. See the response text for more information.'
    }
code_404 = {
    'DescriptionShort':'Not Found',
    'DescriptionVerbose':'The request is understood but no matching data is found to return.'
    }

code_422 = {
    'DescriptionShort':'Invalid User',
    'DescriptionVerbose':'No user with provided username/password combination. This error is specific to the AuthenticateUser request.'
    }
code_500 = {
    'DescriptionShort':'Server Error',
    'DescriptionVerbose':'Something is not working correctly server-side. This is not an issue that can be resolved by modifying query syntax.'
    }
code_unknown = {
    'ResponseCode':999,
    'DescriptionShort':'Unknown Internal/pyramco Error',
    'DescriptionVerbose':'No code or response returned from RAMCO. Verify you are on Python version 3.6+. Check your connections and settings. This error originates in your code or pyramco itself.'
    }


def handler(reply):
	'''
	all pyramco requests are passed through 'handler' to deal with 
	streamtoken replies and provide additional error text
	'''
	
	# if there's a streamtoken, handle it and concatenate the results to a single object
    if reply['ResponseCode'] == 200 or reply['ResponseCode'] == 206:
        # Accounts for streamtoken responses from ramco:
        full_dict = reply
        full_list = full_dict['Data']

		# check to see if streamtoken exists in repeated requests
		# keep writing to 'full_list' until it doesn't
        while 'StreamToken' in reply:
            reply  = resume_streamtoken(reply['StreamToken'])
            reply_list = reply['Data']
            full_list.extend(reply_list)
		
		# add all your streamed responses together in 'full_dict'
        full_dict['Data'] = full_list

        return(full_dict)

    # returns unmodified results
    elif reply['ResponseCode'] == 204:
        return(reply)

    # returns results plus additional error text from documentation
    elif reply['ResponseCode'] == 400:
        reply = {**reply, **code_400}
        return(reply)

    # returns results plus additional error text from documentation
    elif reply['ResponseCode'] == 404:
        reply = {**reply, **code_404}
        return(reply)

    # returns results plus additional error text from documentation
    elif reply['ResponseCode'] == 422:
        reply = {**reply, **code_422}
        return(reply)

    # returns results plus additional error text from documentation
    elif reply['ResponseCode'] == 500:
        reply = {**reply, **code_500}
        return(reply)

    # returns the text for other/unknown errors
    else:
        return(code_unknown)


# pyramco wrapper operations

## metadata operations

def get_entity_types():
    '''
    No arguments are accepted.
    Fetches all entities in the system.
    '''

	# your payload contains all the request information
    payload = {
                'key': config.ramco_api_key,
                'Operation' : 'GetEntityTypes'
            }
	
	# here we build the request: (config.ramco_api_url,payload)
	# then we POST it using 'requests': (requests.post(config.ramco_api_url,payload)
	# then we pass it through 'handler' to deal with streamtokens or errors:
		# handler(requests.post(config.ramco_api_url,payload)
	# then we convert the output to json
		# handler(requests.post(config.ramco_api_url,payload).json())
		
    reply = handler(requests.post(config.ramco_api_url,payload).json())

	# because this is a function, we "return" the reply as the function output
    return(reply)


def get_entity_metadata(entity):
    '''
    Accepts a valid entity name enclosed in apostrophes, like:
    'Contact'; returns all metadata on that entity
    '''

    payload = {
               'key':  config.ramco_api_key,
                'Operation' : 'GetEntityMetadata',
                'Entity':  entity
            }

    reply = handler(requests.post(config.ramco_api_url,payload).json())

    return(reply)


def get_option_set(entity, attribute):
    '''
    Accepts a valid entity name and a single attribute
    Returns value/label pairs for the specified OptionSet
    '''

    payload = {
               'key':  config.ramco_api_key,
                'Operation' : 'GetOptionSet',
                'Entity':  entity,
                'Attribute' :  attribute
            }
    reply = handler(requests.post(config.ramco_api_url,payload).json())

    return(reply)


def clear_cache():
    '''
    No arguments are accepted.
    Clears the server-side metadata cache.
    '''

    payload = {
               'key' :  config.ramco_api_key,
                'Operation' : 'ClearCache'
            }

    reply = handler(requests.post(config.ramco_api_url,payload).json())

    return(reply)



## data querying operations

def get_entity(entity, guid, *attributes):
    '''
    Accepts a valid entity name, GUID, and a tuple of comma-separated
        attribute names, returns attribute values for the specified contact
        matching the GUID
    '''

    payload = {
               'key' :config.ramco_api_key,
                'Operation' : 'GetEntity',
                'Entity' : entity,
                'GUID' : guid,
                'Attributes' : attributes
            }

    reply = handler(requests.post(config.ramco_api_url,payload).json())

    return(reply)


def get_entities(entity, *attributes, filters='', \
                 string_delimiter='', max_results=''):
    '''
    Accepts a valid entity name, a tuple of comma-separated attribute
        names, and (optionally) a valid filters string, a string delimiter
        character, and an integer value for the max results.
    '''

    payload = {
               'key'  :	 config.ramco_api_key,
                'Operation'  : 'GetEntities',
                'Entity' : entity,
                'Filter'  : filters,
                'Attributes'  : attributes,
                'StringDelimiter' : string_delimiter,
                'MaxResults'  : max_results
            }

    reply = handler(requests.post(config.ramco_api_url,payload).json())

    return(reply)


def resume_streamtoken(streamtoken):
    '''
    Accepts a valid streamtoken string and resumes the get_entities
        request that generated it.
    '''

    payload = {
               'key' :	 config.ramco_api_key,
                'Operation'	  : 'GetEntities',
                'StreamToken' :	 streamtoken
            }

    reply = handler(requests.post(config.ramco_api_url,payload).json())

    return(reply)


def validate_user(username, password):
    '''
    Accepts a username and password. for valid combinations, returns that
        Contact's guid. for invalid combinations, returns 422 error.
    '''

    payload = {
               'key'  : config.ramco_api_key,
                'Operation'  : 'ValidateUser',
                'cobalt_username' : username,
                'cobalt_password' : password
            }

    reply = handler(requests.post(config.ramco_api_url,payload).json())

    return(reply)


## data transformation operations

def update_entity(entity, guid, *attributes, string_delimiter=''):
    '''
    Accepts a valid entity name + guid, a tuple of comma separated
        attribute=value pairs, and optionally a string delimiter character
    '''

    payload = {
               'key' :	 config.ramco_api_key,
                'Operation' : 'UpdateEntity',
                'Entity'  :	 entity,
                'Guid'  :	 guid,
                'AttributeValues' :	 attributes,
                'StringDelimiter' :	 string_delimiter
            }

    reply = handler(requests.post(config.ramco_api_url,payload).json())

    return(reply)


def create_entity(entity, *attributes, string_delimiter=''):
    '''
    Accepts a valid entity name, a tuple of comma separated attribute=value
        pairs, and optionally a string delimiter character
    '''

    payload = {
               'key' : config.ramco_api_key,
                'Operation'  :'CreateEntity',
                'Entity' : entity,
                'AttributeValues' : attributes,
                'StringDelimiter' : string_delimiter
            }

    reply = handler(requests.post(config.ramco_api_url,payload).json())

    return(reply)


def delete_entity(entity, guid):
    '''
    Accepts a guid and deletes the corresponding record
    '''

    payload = {
               'key' :  config.ramco_api_key,
                'Operation' : 'DeleteEntity',
                'Entity':  entity,
                'GUID':  guid
            }

    reply = handler(requests.post(config.ramco_api_url,payload).json())

    return(reply)

# end pyramco wrapper operations