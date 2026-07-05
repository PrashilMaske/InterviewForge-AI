import os
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.core.files.storage import default_storage
from django.conf import settings
from .models import Resume, ResumeAnalysis, JobDescription
from .parser import extract_text, extract_entities_with_spacy
from .ai_services import ResumeAnalyzer, JDMatcher

@login_required
def upload_view(request):
    if request.method == 'POST':
        resume_file = request.FILES.get('resume')
        if not resume_file:
            return render(request, 'upload.html', {'error': 'Please select a resume file to upload.'})

        # Validate file size (max 5MB)
        if resume_file.size > 5 * 1024 * 1024:
            return render(request, 'upload.html', {'error': 'File size exceeds the 5MB limit.'})
            
        ext = os.path.splitext(resume_file.name)[1].lower()
        if ext not in ['.pdf', '.docx', '.txt']:
            return render(request, 'upload.html', {'error': 'Unsupported file format. Please upload PDF, DOCX, or TXT.'})

        # Parse text directly from the uploaded file buffer in memory/temp disk
        import tempfile
        try:
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_file:
                for chunk in resume_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name

            try:
                raw_text = extract_text(temp_file_path)
            finally:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
        except Exception as e:
            return render(request, 'upload.html', {'error': f"Failed during resume parsing: {str(e)}"})

        # Reset the upload stream pointer before saving
        resume_file.seek(0)

        # Select storage backend (use RawMediaCloudinaryStorage for docx/txt on Cloudinary to avoid ZIP uploader errors)
        storage = default_storage
        if hasattr(settings, 'DEFAULT_FILE_STORAGE') and 'Cloudinary' in settings.DEFAULT_FILE_STORAGE:
            if ext in ['.docx', '.txt']:
                from cloudinary_storage.storage import RawMediaCloudinaryStorage
                storage = RawMediaCloudinaryStorage()

        file_path = storage.save(f"resumes/{request.user.id}_{resume_file.name}", resume_file)
        file_url = storage.url(file_path)

        # Create Resume record
        resume = Resume.objects.create(
            user=request.user,
            file_url=file_url,
            file_name=resume_file.name
        )

        try:
            # Analyze using AI
            analyzer = ResumeAnalyzer()
            analysis_data = analyzer.analyze(raw_text)
            
            # Extract basic entities using spaCy as secondary metadata
            spacy_metadata = extract_entities_with_spacy(raw_text)
            analysis_data["extracted_entities"]["spacy_metadata"] = spacy_metadata

            # Save Analysis model
            ResumeAnalysis.objects.create(
                resume=resume,
                overall_score=analysis_data["overall_score"],
                formatting_score=analysis_data["scores"]["formatting"],
                projects_score=analysis_data["scores"]["projects"],
                skills_score=analysis_data["scores"]["skills"],
                ats_score=analysis_data["scores"]["ats"],
                grammar_score=analysis_data["scores"]["grammar"],
                achievements_score=analysis_data["scores"]["achievements"],
                keywords_score=analysis_data["scores"]["keywords"],
                section_explanations=analysis_data["score_explanations"],
                improved_bullets=analysis_data["improved_bullet_points"],
                parsed_entities=analysis_data["extracted_entities"]
            )
        except Exception as e:
            # Clean up on error
            resume.delete()
            return render(request, 'upload.html', {'error': f"Failed during resume parsing: {str(e)}"})

        return redirect('dashboard')

    return render(request, 'upload.html')

@login_required
def resume_detail_view(request, resume_id):
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    analysis = getattr(resume, 'analysis', None)
    return render(request, 'resume_detail.html', {'resume': resume, 'analysis': analysis})

@login_required
def compare_jd_view(request, resume_id):
    resume = get_object_or_404(Resume, id=resume_id, user=request.user)
    
    if request.method == 'POST':
        jd_title = request.POST.get('title', 'Target Role')
        jd_text = request.POST.get('jd_text', '')
        
        if not jd_text:
            return render(request, 'compare_jd.html', {'resume': resume, 'error': 'Job Description text cannot be empty.'})

        # Save JobDescription object
        jd = JobDescription.objects.create(
            user=request.user,
            title=jd_title,
            raw_text=jd_text
        )

        try:
            # We need the parsed resume text to match against the JD text.
            # To fetch parsed text, we read the resume file content.
            # Since the file url might be local or Cloudinary, we read the local copy or download it.
            # In local settings, we read the path directly:
            file_name = resume.file_url.split('/media/')[-1]
            local_path = os.path.join(settings.MEDIA_ROOT, file_name) if hasattr(settings, 'MEDIA_ROOT') else resume.file_url
            
            resume_text = extract_text(local_path)
            
            # Match
            matcher = JDMatcher()
            match_data = matcher.match(resume_text, jd_text)
            
            context = {
                'resume': resume,
                'jd': jd,
                'match': match_data
            }
            return render(request, 'compare_jd_results.html', context)
        except Exception as e:
            jd.delete()
            return render(request, 'compare_jd.html', {'resume': resume, 'error': f"Comparison failed: {str(e)}"})

    return render(request, 'compare_jd.html', {'resume': resume})
