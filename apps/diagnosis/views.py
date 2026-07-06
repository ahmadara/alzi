from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from apps.accounts.models import UserProfile
from apps.news.models import NewsArticle
from .models import DiagnosisRecord
from .analyzer import analyze_mri


@login_required
def dashboard(request):
    diagnoses = DiagnosisRecord.objects.filter(user=request.user)
    recent_diagnoses = diagnoses[:5]
    latest_news = NewsArticle.objects.filter(is_published=True)[:3]

    stats = {
        'total': diagnoses.count(),
        'cn': diagnoses.filter(result='CN').count(),
        'mci': diagnoses.filter(result='MCI').count(),
        'ad': diagnoses.filter(result='AD').count(),
    }

    context = {
        'recent_diagnoses': recent_diagnoses,
        'latest_news': latest_news,
        'stats': stats,
    }
    return render(request, 'dashboard/index.html', context)


@login_required
def profile(request):
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '').strip()
        user.last_name = request.POST.get('last_name', '').strip()
        user.email = request.POST.get('email', '').strip()
        user.save()

        phone = request.POST.get('phone', '').strip()
        if phone and phone != profile_obj.phone:
            if UserProfile.objects.filter(phone=phone).exclude(user=request.user).exists():
                messages.error(request, 'این شماره موبایل قبلاً ثبت شده است.')
            else:
                profile_obj.phone = phone
                profile_obj.save()
        elif not phone:
            profile_obj.phone = None
            profile_obj.save()

        messages.success(request, 'اطلاعات پروفایل با موفقیت به‌روزرسانی شد.')
        return redirect('dashboard:profile')

    return render(request, 'dashboard/profile.html', {'profile': profile_obj})


@login_required
def history(request):
    diagnoses_qs = DiagnosisRecord.objects.filter(user=request.user)
    result_filter = request.GET.get('result', '')
    if result_filter:
        diagnoses_qs = diagnoses_qs.filter(result=result_filter)

    paginator = Paginator(diagnoses_qs, 10)
    page = request.GET.get('page', 1)
    diagnoses = paginator.get_page(page)

    context = {
        'diagnoses': diagnoses,
        'result_filter': result_filter,
        'result_choices': DiagnosisRecord.RESULT_CHOICES,
    }
    return render(request, 'dashboard/history.html', context)


@login_required
def upload(request):
    if request.method == 'POST':
        image = request.FILES.get('mri_image')
        if not image:
            messages.error(request, 'لطفاً یک فایل تصویر انتخاب کنید.')
            return render(request, 'dashboard/upload.html')

        # Save image first so we have a real path for Grad-CAM generation
        record = DiagnosisRecord.objects.create(
            user=request.user,
            image=image,
            result='PENDING',
            confidence=None,
        )
        analysis = analyze_mri(image_path=record.image.path)
        record.result = analysis['result']
        record.confidence = analysis['confidence']
        record.save(update_fields=['result', 'confidence'])
        return redirect('dashboard:result', pk=record.pk)

    return render(request, 'dashboard/upload.html')


@login_required
def result(request, pk):
    record = get_object_or_404(DiagnosisRecord, pk=pk, user=request.user)
    analysis = analyze_mri(image_path=record.image.path)
    return render(request, 'dashboard/result.html', {
        'record': record,
        'analysis': analysis,
    })
