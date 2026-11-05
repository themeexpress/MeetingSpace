from rest_framework import status
from rest_framework.exceptions import APIException


class SelfDemotionError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "BR-9: admins cannot deactivate or demote their own account."
    default_code = "self_demotion"
