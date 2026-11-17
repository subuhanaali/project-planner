from django.shortcuts import render

# Create your views here.

# from django.contrib.auth.models import AbstractUser

# class Profile(AbstractUser):

#     role=models.CharField(max_length=20)

from rest_framework.views import APIView

from django.core.exceptions import ValidationError

from django.contrib.auth import authenticate

from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import ProfileSerializer

from decouple import config

from planner.utils import send_mail

import threading

class LoginView(APIView):

    def post(self,request,*args,**kwargs):

        username=request.data.get('username')

        password=request.data.get('password')

        try :
            
            if not username :
                
                raise ValidationError('must provide username')

            if not password:

                raise ValidationError('must provide password')
            
        except Exception as e:

            data={'error':e}

            return Response(data,status=400)
        
        user = authenticate(username=username,password=password)

        if user:

            refresh_token = RefreshToken.for_user(user)

            access_token=refresh_token.access_token

            data={'access_token':str(access_token),'refresh_token':str(refresh_token)}

            return Response(data,status=200)

        data={'msg':'invalid username or password'}

        return Response(data,status=401)

class RegisterView(APIView):

    serializer_class=ProfileSerializer

    def post(self,request,*args,**kwargs):

        serializer=self.serializer_class(data=request.data)

        if serializer.is_valid():

            username=serializer.validated_data.get('username')
             #{'username':'username','first_name':'name','password':password'}

            password=serializer.validated_data.get('password')

            Profile=serializer.save()

            Profile.email=username

            Profile.set_password(password)

            Profile.save()

            recipient=Profile.email

            subject='welcome Abroad, Sweet Moments Awaits at CakeTales'

            template='emails/registration.html'

            context={
                'name': Profile.first_name,
                'email': recipient,
                'login_url': config('LOGIN_URL'),
            }

            # send_mail(recipient, subject, template, context)
            thread=threading.Thread(target=send_mail,args=(recipient,subject,template,context))
            thread.start()
            data={'msg':'user created successfully'}

            return Response(data,status=201)

        return Response(serializer.errors,status=400)

    
    

