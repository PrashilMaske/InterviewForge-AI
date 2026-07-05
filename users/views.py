from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import CustomUser

def index_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'index.html')

@login_required
def voice_test_view(request):
    """Standalone voice recognition diagnostic page."""
    from interviews.models import InterviewSession
    session = InterviewSession.objects.filter(user=request.user).order_by('-created_at').first()
    session_id = str(session.id) if session else ""
    return render(request, 'voice_test.html', {'session_id': session_id})

@login_required
def live_captioning_view(request):
    """Standalone live real-time captioning page."""
    from interviews.models import InterviewSession
    session = InterviewSession.objects.filter(user=request.user).order_by('-created_at').first()
    session_id = str(session.id) if session else ""
    return render(request, 'live_captioning.html', {'session_id': session_id})





def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    error_message = None
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        role = request.POST.get('role', 'candidate')
        
        if not email or not username or not password:
            error_message = "All fields are required."
        elif CustomUser.objects.filter(email=email).exists():
            error_message = "Email is already registered."
        elif CustomUser.objects.filter(username=username).exists():
            error_message = "Username is already taken."
        else:
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                role=role
            )
            user.last_active = timezone.now()
            user.save()
            login(request, user)
            return redirect('dashboard')
            
    return render(request, 'register.html', {'error': error_message})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    error_message = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Update user activity streak
            today = timezone.now().date()
            if user.last_active:
                delta = today - user.last_active.date()
                if delta.days == 1:
                    user.streak += 1
                elif delta.days > 1:
                    user.streak = 1
            else:
                user.streak = 1
                
            user.last_active = timezone.now()
            user.save()
            login(request, user)
            return redirect('dashboard')
        else:
            error_message = "Invalid username or password."
            
    return render(request, 'login.html', {'error': error_message})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard_view(request):
    user = request.user
    
    # Retrieve user's resume histories and mock interview records
    resumes_list = user.resumes.all().order_by('-version')
    sessions_list = user.interview_sessions.all().order_by('-created_at')
    
    context = {
        'user': user,
        'resumes': resumes_list,
        'sessions': sessions_list,
        'latest_resume': resumes_list.first() if resumes_list.exists() else None,
    }
    return render(request, 'dashboard.html', context)
