"""Auth backends"""
import logging
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from reporter.metadata import get_tapis_config_metadata
import jwt
from tapipy.tapis import Tapis

#pylint: disable=invalid-name
logger = logging.getLogger(__name__)
#pylint: enable=invalid-name

class TapisOAuthBackend(ModelBackend):
    def authenticate(self, *args, **kwargs):
        user = None
        try:
            if 'backend' not in kwargs or kwargs['backend'] != 'tapis':
                raise Exception('Skipping TapisOAuthBackend')
            token = kwargs['token']
            base_url = kwargs['base_url']

            user_info_url = "%s/oauth2/userinfo" % base_url
            headers = {
                "Content-Type":"application/json",
                "x-tapis-token":token
            }

            user_info = None

            try:
                response = requests.get(
                    user_info_url,
                    headers=headers
                )
                user_info = response.json()
            except Exception as e:
                logger.exception(e)
                raise Exception('Tapis Authentication failed')

            username = user_info['result']['username']
            meta = get_tapis_config_metadata()
            if 'admin_users' not in meta['value'] or username not in meta['value']['admin_users']:
                raise Exception('%s is not a hub admin user' % username)
            UserModel = get_user_model()
            user, _ = UserModel.objects.get_or_create(username=username)
            user.save()
            logger.info('Login successful for user "%s"' % username)
        except Exception as e:
            logger.exception(e)
        return user
