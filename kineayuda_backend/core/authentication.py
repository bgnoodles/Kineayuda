from firebase_admin import auth
from rest_framework import authentication, exceptions  

class FirebaseUser:
    def __init__(self, uid, email=None):
        self.uid = uid
        self.email = email

    @property
    def is_authenticated(self):
        return True

class FirebaseAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ',1)[1].strip()
        if not token:
            raise exceptions.AuthenticationFailed('No se proporcionó un token.')
        
        try:
            decoded = auth.verify_id_token(token)
        except Exception:
            raise exceptions.AuthenticationFailed('Token inválido o expirado.')
        
        user = FirebaseUser(uid=decoded.get('uid'), email=decoded.get('email'))
        return (user, token)