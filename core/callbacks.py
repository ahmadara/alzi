from django.contrib.auth.models import User
from apps.news.models import NewsArticle, NewsComment
from apps.diagnosis.models import DiagnosisRecord


def dashboard_callback(request, context):
    context['stats'] = {
        'total_users': User.objects.count(),
        'total_diagnoses': DiagnosisRecord.objects.count(),
        'published_articles': NewsArticle.objects.filter(is_published=True).count(),
        'pending_comments': NewsComment.objects.filter(is_approved=False).count(),
        'cn_count': DiagnosisRecord.objects.filter(result='CN').count(),
        'mci_count': DiagnosisRecord.objects.filter(result='MCI').count(),
        'ad_count': DiagnosisRecord.objects.filter(result='AD').count(),
        'pending_diagnoses': DiagnosisRecord.objects.filter(result='PENDING').count(),
        'recent_users': User.objects.order_by('-date_joined')[:5],
        'recent_diagnoses': DiagnosisRecord.objects.select_related('user').order_by('-created_at')[:8],
    }
    return context
