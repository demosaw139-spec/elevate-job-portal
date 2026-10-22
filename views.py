from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import CompanyForm, JobForm, RegistrationForm
from .models import Application, Company, Job, SavedJob, User


def home(request):
    featured_jobs = Job.objects.filter(status=Job.Status.PUBLISHED).select_related(
        "company"
    )[:6]
    return render(request, "portal/home.html", {"featured_jobs": featured_jobs})


def job_list(request):
    jobs = Job.objects.filter(status=Job.Status.PUBLISHED).select_related("company")
    query = request.GET.get("q", "").strip()
    location = request.GET.get("location", "").strip()
    work_mode = request.GET.get("work_mode", "").strip()
    employment_type = request.GET.get("employment_type", "").strip()
    if query:
        jobs = jobs.filter(
            Q(title__icontains=query)
            | Q(summary__icontains=query)
            | Q(description__icontains=query)
            | Q(company__name__icontains=query)
        )
    if location:
        jobs = jobs.filter(location__icontains=location)
    if work_mode in Job.WorkMode.values:
        jobs = jobs.filter(work_mode=work_mode)
    if employment_type in Job.EmploymentType.values:
        jobs = jobs.filter(employment_type=employment_type)
    page = Paginator(jobs, 9).get_page(request.GET.get("page"))
    saved_ids = set()
    if request.user.is_authenticated and request.user.role == User.Role.CANDIDATE:
        saved_ids = set(
            SavedJob.objects.filter(candidate=request.user).values_list("job_id", flat=True)
        )
    return render(
        request,
        "portal/job_list.html",
        {
            "page": page,
            "query": query,
            "location": location,
            "work_mode": work_mode,
            "employment_type": employment_type,
            "saved_ids": saved_ids,
            "work_mode_choices": Job.WorkMode.choices,
            "employment_type_choices": Job.EmploymentType.choices,
        },
    )


def job_detail(request, pk):
    job = get_object_or_404(
        Job.objects.select_related("company"),
        pk=pk,
        status=Job.Status.PUBLISHED,
    )
    applied = request.user.is_authenticated and job.applications.filter(
        candidate=request.user
    ).exists()
    saved = request.user.is_authenticated and SavedJob.objects.filter(
        candidate=request.user, job=job
    ).exists()
    return render(request, "portal/job_detail.html", {"job": job, "applied": applied, "saved": saved})


def register(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Your account is ready. Welcome to Elevate.")
        return redirect("dashboard")
    return render(request, "portal/register.html", {"form": form})


@login_required
def dashboard(request):
    if request.user.is_superuser:
        return redirect("admin:index")
    if request.user.role == User.Role.EMPLOYER:
        company, _ = Company.objects.get_or_create(
            owner=request.user, defaults={"name": f"{request.user.display_name}'s company"}
        )
        jobs = Job.objects.filter(company=company).annotate(applicant_count=Count("applications"))
        applications = Application.objects.filter(job__company=company).select_related(
            "candidate", "job"
        )
        return render(
            request,
            "portal/employer_dashboard.html",
            {
                "company": company,
                "jobs": jobs,
                "applications": applications[:8],
                "active_jobs": jobs.filter(status=Job.Status.PUBLISHED).count(),
                "applicant_count": applications.count(),
                "new_count": applications.filter(status=Application.Status.SUBMITTED).count(),
                "application_status_choices": Application.Status.choices,
            },
        )
    applications = Application.objects.filter(candidate=request.user).select_related(
        "job__company"
    )
    saved_jobs = SavedJob.objects.filter(candidate=request.user).select_related("job__company")
    saved_count = saved_jobs.count()
    return render(
        request,
        "portal/candidate_dashboard.html",
        {
            "applications": applications[:6],
            "application_count": applications.count(),
            "interview_count": applications.filter(status=Application.Status.INTERVIEW).count(),
            "saved_jobs": saved_jobs[:4],
            "saved_count": saved_count,
        },
    )


@login_required
def job_create(request):
    if request.user.role != User.Role.EMPLOYER:
        raise Http404
    company, _ = Company.objects.get_or_create(
        owner=request.user, defaults={"name": f"{request.user.display_name}'s company"}
    )
    form = JobForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        job = form.save(commit=False)
        job.company = company
        job.save()
        messages.success(request, "Your job posting has been saved.")
        return redirect("dashboard")
    return render(request, "portal/job_form.html", {"form": form, "heading": "Create a role"})


@login_required
def job_edit(request, pk):
    if request.user.role != User.Role.EMPLOYER:
        raise Http404
    job = get_object_or_404(Job, pk=pk, company__owner=request.user)
    form = JobForm(request.POST or None, instance=job)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Your changes have been saved.")
        return redirect("dashboard")
    return render(request, "portal/job_form.html", {"form": form, "heading": "Edit role"})


@login_required
@require_POST
def apply_to_job(request, pk):
    if request.user.role != User.Role.CANDIDATE:
        messages.error(request, "Only job seeker accounts can apply.")
        return redirect("job_detail", pk=pk)
    job = get_object_or_404(Job, pk=pk, status=Job.Status.PUBLISHED)
    application, created = Application.objects.get_or_create(
        job=job,
        candidate=request.user,
        defaults={"cover_letter": request.POST.get("cover_letter", "").strip()},
    )
    if created:
        messages.success(request, "Application submitted. You can track it from your dashboard.")
    else:
        messages.info(request, "You have already applied to this role.")
    return redirect("job_detail", pk=job.pk)


@login_required
@require_POST
def toggle_saved_job(request, pk):
    if request.user.role != User.Role.CANDIDATE:
        return redirect("job_detail", pk=pk)
    job = get_object_or_404(Job, pk=pk, status=Job.Status.PUBLISHED)
    saved, created = SavedJob.objects.get_or_create(candidate=request.user, job=job)
    if not created:
        saved.delete()
    next_url = request.POST.get("next", "")
    if not url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        next_url = job.get_absolute_url()
    return redirect(next_url)


@login_required
@require_POST
def update_application_status(request, pk):
    if request.user.role != User.Role.EMPLOYER:
        raise Http404
    application = get_object_or_404(
        Application, pk=pk, job__company__owner=request.user
    )
    status = request.POST.get("status")
    if status not in Application.Status.values:
        messages.error(request, "Choose a valid application status.")
    else:
        application.status = status
        application.save(update_fields=["status", "updated_at"])
        messages.success(request, "Applicant status updated.")
    return redirect("dashboard")


@login_required
def company_settings(request):
    if request.user.role != User.Role.EMPLOYER:
        raise Http404
    company, _ = Company.objects.get_or_create(
        owner=request.user, defaults={"name": f"{request.user.display_name}'s company"}
    )
    form = CompanyForm(request.POST or None, instance=company)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Company profile updated.")
        return redirect("dashboard")
    return render(request, "portal/company_form.html", {"form": form})


def page_not_found(request, exception):
    return render(request, "404.html", status=404)
