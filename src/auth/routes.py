from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.main import get_session
from src.db.redis import add_jti_to_blocklist

from .dependencies import (
    AccessTokenBearer,
    RefreshTokenBearer,
    RoleChecker,
    get_current_user,
)
from .schemas import (
    UserCreateModel,
    UserLoginModel,
    EmailModel,
    PasswordResetRequestModel,
    PasswordResetConfirmModel,
)
from .service import UserService
from .utils import (
    create_access_token,
    verify_password,
    generate_passwd_hash,
    create_url_safe_token,
    decode_url_safe_token,
)
from src.config import Config
from src.celery_tasks import send_email
from src.templates.template_loader import render_template

auth_router = APIRouter()
user_service = UserService()
role_checker = RoleChecker(["admin", "user"])


REFRESH_TOKEN_EXPIRY = 2


@auth_router.post("/send_mail")
async def send_mail(emails: EmailModel):
    emails = emails.addresses

    # Send test email using template
    subject = "Welcome to the Security Platform"
    html_body = render_template('welcome_test')
    send_email.delay(emails, subject, html_body)

    return {"message": "Email sent successfully"}


@auth_router.post("/signup", status_code=status.HTTP_201_CREATED)
async def create_user_Account(
    user_data: UserCreateModel,
    session: AsyncSession = Depends(get_session),
):
    """
    Create user account using email, username, first_name, last_name
    params:
        user_data: UserCreateModel
    """
    email = user_data.email

    user_exists = await user_service.user_exist(email, session)

    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )

    new_user = await user_service.create_user(user_data, session)
    print(f"✅ User created successfully: {new_user.email}")

    # Create verification token
    token = create_url_safe_token({"email": email})
    print(f"🔑 Verification token created for {email}")

    # Frontend verification link with token as path parameter
    verification_link = f"http://{Config.FRONTEND_DOMAIN}/verify-email/{token}"
    print(f"🔗 Verification link: {verification_link}")
    # Note: Frontend will call: /api/v1/auth/verify/{token}

    # Send verification email using template
    emails = [email]
    subject = "🛡️ Verify Your Email - Security Platform"
    
    try:
        # Render template with variables and send using existing Celery setup
        html_body = render_template('email_verification', 
                                   verification_link=verification_link, email=email)
        
        # Send email via Celery task
        task_result = send_email.delay(emails, subject, html_body)
        print(f"✅ Email task queued successfully for {email}")
        print(f"📋 Task ID: {task_result.id}")
        
    except Exception as e:
        print(f"❌ Email sending failed for {email}: {str(e)}")
        # Don't fail the signup process if email fails, just log it
        # The user can still use the resend functionality

    return {
        "message": "Account created successfully! Please check your email to verify your account.",
        "user": {
            "email": new_user.email,
            "uid": str(new_user.uid),
            "is_verified": False
        },
        "verification_sent_to": email,
        "next_step": "Check your email and click the verification link to activate your account"
    }


@auth_router.get("/verify/{token}")
async def verify_user_account(token: str, session: AsyncSession = Depends(get_session)):
    """
    Verify user email and complete registration process
    Changes user status from is_verified=False to is_verified=True
    This completes the user registration flow
    """
    try:
        # Decode and validate the token
        token_data = decode_url_safe_token(token)
        
        if not token_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or malformed verification token"
            )
        
        user_email = token_data.get("email")
        
        if not user_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token does not contain valid email information"
            )

        # Find the user in database
        user = await user_service.get_user_by_email(user_email, session)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User account not found. Please sign up again."
            )
        
        # Check if user is already verified
        if user.is_verified:
            return JSONResponse(
                content={
                    "message": "Account is already verified and fully registered",
                    "status": "already_verified",
                    "user": {
                        "email": user.email,
                        "is_verified": True,
                        "registration_complete": True
                    }
                },
                status_code=status.HTTP_200_OK,
            )

        # Complete the registration by setting is_verified = True
        await user_service.update_user(user, {"is_verified": True}, session)

        # Send welcome email using template
        welcome_subject = "🎉 Welcome to Security Platform - Account Verified!"
        html_body = render_template('welcome',
                                  user_name=user.email.split('@')[0].title(),  # Use email prefix as name
                                  email=user.email,
                                  login_link=f"http://{Config.FRONTEND_DOMAIN}/login")
        send_email.delay([user.email], welcome_subject, html_body)

        return JSONResponse(
            content={
                "message": "🎉 Email verified successfully! Your account is now fully registered.",
                "status": "verification_complete",
                "user": {
                    "email": user.email,
                    "uid": str(user.uid),
                    "is_verified": True,
                    "registration_complete": True,
                    "role": user.role
                },
                "next_step": "You can now login to your account"
            },
            status_code=status.HTTP_200_OK,
        )
        
    except ValueError as e:
        # Token decoding error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token format"
        )
    except Exception as e:
        # Log the error for debugging
        print(f"Verification error: {str(e)}")
        return JSONResponse(
            content={
                "message": "An error occurred during email verification. Please try again or contact support.",
                "status": "verification_error"
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@auth_router.get("/registration-status/{email}")
async def check_registration_status(
    email: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Check user registration and verification status
    Helps frontend determine user's current state in registration flow
    """
    user = await user_service.get_user_by_email(email, session)
    
    if not user:
        return JSONResponse(
            content={
                "exists": False,
                "message": "No account found with this email address"
            },
            status_code=status.HTTP_404_NOT_FOUND,
        )
    
    return JSONResponse(
        content={
            "exists": True,
            "email": user.email,
            "is_verified": user.is_verified,
            "registration_complete": user.is_verified,
            "status": "fully_registered" if user.is_verified else "pending_verification",
            "message": "Account fully registered" if user.is_verified else "Account created, email verification pending",
            "created_at": user.created_at.isoformat() if hasattr(user, 'created_at') else None
        },
        status_code=status.HTTP_200_OK,
    )


@auth_router.post("/login")
async def login_users(
    login_data: UserLoginModel, session: AsyncSession = Depends(get_session)
):
    email = login_data.email
    password = login_data.password

    user = await user_service.get_user_by_email(email, session)

    if user is not None:
        # Check if user has verified their email
        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please verify your email address before logging in. Check your email for the verification link."
            )
            
        password_valid = verify_password(password, user.password_hash)

        if password_valid:
            access_token = create_access_token(
                user_data={
                    "email": user.email,
                    "user_uid": str(user.uid),
                    "role": user.role,
                }
            )

            refresh_token = create_access_token(
                user_data={"email": user.email, "user_uid": str(user.uid)},
                refresh=True,
                expiry=timedelta(days=REFRESH_TOKEN_EXPIRY),
            )

            return JSONResponse(
                content={
                    "message": "Login successful",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": {"email": user.email, "uid": str(user.uid)},
                }
            )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials"
    )


@auth_router.get("/refresh_token")
async def get_new_access_token(token_details: dict = Depends(RefreshTokenBearer())):
    expiry_timestamp = token_details["exp"]

    if datetime.fromtimestamp(expiry_timestamp) > datetime.now():
        new_access_token = create_access_token(user_data=token_details["user"])

        return JSONResponse(content={"access_token": new_access_token})

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token"
    )


@auth_router.get("/me")
async def get_current_user(
    user=Depends(get_current_user), _: bool = Depends(role_checker)
):
    return user


@auth_router.get("/logout")
async def revoke_token(token_details: dict = Depends(AccessTokenBearer())):
    jti = token_details["jti"]

    await add_jti_to_blocklist(jti)

    return JSONResponse(
        content={"message": "Logged Out Successfully"}, status_code=status.HTTP_200_OK
    )


@auth_router.post("/password-reset-request")
async def password_reset_request(email_data: PasswordResetRequestModel):
    email = email_data.email

    token = create_url_safe_token({"email": email})

    # Frontend password reset link with proper API prefix for backend calls
    reset_link = f"http://{Config.FRONTEND_DOMAIN}/reset-password?token={token}"
    # Note: Frontend will call: /api/v1/auth/password-reset-confirm/{token}

    # Send password reset email using template
    subject = "🔐 Reset Your Password - Security Platform"
    html_body = render_template('password_reset',
                               reset_link=reset_link,
                               email=email,
                               user_name=email.split('@')[0].title())  # Use email prefix as name
    send_email.delay([email], subject, html_body)

    return JSONResponse(
        content={
            "message": "Please check your email for instructions to reset your password",
        },
        status_code=status.HTTP_200_OK,
    )
 

@auth_router.post("/password-reset-confirm/{token}")
async def reset_account_password(
    token: str,
    passwords: PasswordResetConfirmModel,
    session: AsyncSession = Depends(get_session),
):
    new_password = passwords.new_password
    confirm_password = passwords.confirm_new_password

    if new_password != confirm_password:
        raise HTTPException(
            detail="Passwords do not match", status_code=status.HTTP_400_BAD_REQUEST
        )

    token_data = decode_url_safe_token(token)

    user_email = token_data.get("email")

    if user_email:
        user = await user_service.get_user_by_email(user_email, session)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        passwd_hash = generate_passwd_hash(new_password)
        await user_service.update_user(user, {"password_hash": passwd_hash}, session)

        return JSONResponse(
            content={"message": "Password reset Successfully"},
            status_code=status.HTTP_200_OK,
        )

    return JSONResponse(
        content={"message": "Error occured during password reset."},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
