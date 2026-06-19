import os
import requests
import jwt # Needs 'PyJWT' and 'cryptography' packages bundled
from http.cookies import SimpleCookie

# Configuration variables
REGION = os.environ["AWS_REGION"]
USER_POOL_ID = os.environ["COGNITO_USER_POOL_ID"]
APP_CLIENT_ID = os.environ["COGNITO_APP_CLIENT_ID"]
COOKIE_NAME = "access_token"

# Cognito JWKS endpoint providing public keys
JWKS_URL = f"https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}/.well-known/jwks.json"

def lambda_handler(event, context):
    try:
        
        # 1. Parse cookie header
        headers = event.get("headers", {})
        cookie_header = headers.get("Cookie", "") or headers.get("cookie", "")

        cookie = SimpleCookie()
        print("Cookie header:", cookie_header)
        cookie.load(cookie_header)
        
        if COOKIE_NAME not in cookie:
            print("Missing access_token cookie cannot authenticate user")
            print("❌ authorization failed")
            return {"isAuthorized": False}
            
        token = cookie[COOKIE_NAME].value
        
        # 2. Extract unverified header to find the Key ID ('kid')
        token_headers = jwt.get_unverified_header(token)
        token_kid = token_headers.get("kid")
        print("Token KID:", token_kid)
        print("url=",JWKS_URL)

        # 3. Retrieve Cognito's public keys
        print("retrieving public key from cognito...")
        jwks_response = requests.get(JWKS_URL).json()
        
        # 4. Locate the exact public key matching the token's 'kid'
        public_key = None
        for key in jwks_response.get("keys", []):
            if key.get("kid") == token_kid:
                # Convert JWKS parameter into a PyJWT-compatible public key object
                public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
                break
                
        if not public_key:
            print("No matching public key found")
            print("❌ authorization failed")
            return {"isAuthorized": False}

        print("public key found")

        # 5. Verify signature, expiration, issuer, and audience (App Client ID)
        expected_issuer = f"https://cognito-idp.{REGION}.amazonaws.com/{USER_POOL_ID}"
        print("Decoding token with issuer:", expected_issuer)
        decoded_claims = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            audience=APP_CLIENT_ID,
            issuer=expected_issuer,
            options={"verify_aud": False}
        )

        token_audience = decoded_claims.get("client_id")
                
        if token_audience != APP_CLIENT_ID:
            print(f"Token client mismatch. Expected {APP_CLIENT_ID}, got {token_audience}")
            print("❌ authorization failed")
            return {"isAuthorized": False}
        
        
        print("✅ access_token is validated successfully...")
        print(f"userid={decoded_claims.get("sub")} is authenticated...")
        print("✅ authorization successful")
        # 6. Return successful payload match
        return {
            "isAuthorized": True,
            "context": {
                "userId": decoded_claims.get("sub"),
                "username": decoded_claims.get("username", "")
            }
        }

    except Exception as e:
        print(f"Token validation error: {str(e)}")
        print("❌ authorization failed")
        return {"isAuthorized": False}
