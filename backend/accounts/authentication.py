from rest_framework.authentication import SessionAuthentication as BaseSessionAuthentication


class SessionAuthentication(BaseSessionAuthentication):
    """Session authentication that keeps DRF's 401/403 distinction.

    DRF downgrades NotAuthenticated to 403 whenever no authenticator
    provides a WWW-Authenticate challenge. Session auth has none by
    default, which would make "not logged in" indistinguishable from
    "logged in but forbidden" (see docs/API.md's error table).
    """

    def authenticate_header(self, request):
        return "Session"
