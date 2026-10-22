from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Application, Company, Job, SavedJob


User = get_user_model()


class PortalFlowTests(TestCase):
    def setUp(self):
        self.employer = User.objects.create_user(
            username="studio", password="StrongPass123!", role=User.Role.EMPLOYER
        )
        self.company = Company.objects.create(owner=self.employer, name="Northstar Studio")
        self.job = Job.objects.create(
            company=self.company,
            title="Product Designer",
            summary="Shape a thoughtful product experience.",
            description="Work with a collaborative team.",
            location="Remote",
            work_mode=Job.WorkMode.REMOTE,
        )
        self.candidate = User.objects.create_user(
            username="candidate", password="StrongPass123!", role=User.Role.CANDIDATE
        )

    def test_public_home_and_job_search_render_database_content(self):
        self.assertContains(self.client.get(reverse("home")), "Product Designer")
        response = self.client.get(reverse("job_list"), {"q": "Northstar"})
        self.assertContains(response, "Product Designer")
        self.assertEqual(response.context["page"].paginator.count, 1)

    def test_candidate_can_apply_once_and_track_application(self):
        self.client.force_login(self.candidate)
        response = self.client.post(
            reverse("apply", args=[self.job.pk]), {"cover_letter": "I love this mission."}
        )
        self.assertRedirects(response, reverse("job_detail", args=[self.job.pk]))
        self.assertEqual(Application.objects.filter(job=self.job, candidate=self.candidate).count(), 1)
        self.assertEqual(
            Application.objects.get(job=self.job, candidate=self.candidate).cover_letter,
            "I love this mission.",
        )
        self.client.post(reverse("apply", args=[self.job.pk]), {"cover_letter": "Duplicate"})
        self.assertEqual(Application.objects.filter(job=self.job, candidate=self.candidate).count(), 1)

    def test_saved_job_return_url_cannot_redirect_off_site(self):
        self.client.force_login(self.candidate)
        response = self.client.post(
            reverse("toggle_saved", args=[self.job.pk]),
            {"next": "https://outside.example/"},
        )
        self.assertRedirects(response, reverse("job_detail", args=[self.job.pk]))

    def test_employer_can_manage_owned_jobs_but_not_other_company_jobs(self):
        self.client.force_login(self.employer)
        response = self.client.get(reverse("job_edit", args=[self.job.pk]))
        self.assertEqual(response.status_code, 200)
        other_employer = User.objects.create_user(
            username="other", password="StrongPass123!", role=User.Role.EMPLOYER
        )
        self.client.force_login(other_employer)
        self.assertEqual(self.client.get(reverse("job_edit", args=[self.job.pk])).status_code, 404)

    def test_employer_can_update_an_applicant_status(self):
        application = Application.objects.create(job=self.job, candidate=self.candidate)
        self.client.force_login(self.employer)
        response = self.client.post(
            reverse("application_status", args=[application.pk]),
            {"status": Application.Status.SHORTLISTED},
        )
        self.assertRedirects(response, reverse("dashboard"))
        application.refresh_from_db()
        self.assertEqual(application.status, Application.Status.SHORTLISTED)

    def test_candidate_registration_creates_authenticated_account(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "newcandidate",
                "first_name": "New",
                "last_name": "Person",
                "email": "new@example.com",
                "role": User.Role.CANDIDATE,
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )
        self.assertRedirects(response, reverse("dashboard"))
        created = User.objects.get(username="newcandidate")
        self.assertTrue(created.check_password("StrongPass123!"))
        self.assertEqual(created.role, User.Role.CANDIDATE)

    def test_rest_api_lists_published_jobs_and_requires_auth_to_apply(self):
        response = self.client.get("/api/jobs/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["count"], 1)
        response = self.client.get("/api/jobs/", {"q": "Product", "work_mode": "remote"})
        self.assertEqual(response.json()["count"], 1)
        response = self.client.post("/api/applications/", {"job": self.job.pk})
        self.assertEqual(response.status_code, 403)
        self.client.force_login(self.candidate)
        response = self.client.post("/api/applications/", {"job": self.job.pk})
        self.assertEqual(response.status_code, 201)

    def test_public_auth_and_job_pages_render(self):
        for name in ("register", "login", "password_reset"):
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        self.assertContains(self.client.get(reverse("job_detail", args=[self.job.pk])), "Product Designer")
        self.assertContains(self.client.get(reverse("job_list")), "Any arrangement")

    def test_candidate_and_employer_dashboards_render_their_workflows(self):
        application = Application.objects.create(job=self.job, candidate=self.candidate)
        SavedJob.objects.create(candidate=self.candidate, job=self.job)
        self.client.force_login(self.candidate)
        response = self.client.get(reverse("dashboard"))
        self.assertContains(response, "Your applications")
        self.assertEqual(response.context["saved_count"], 1)
        self.assertEqual(len(response.context["saved_jobs"]), 1)
        self.client.force_login(self.employer)
        self.assertContains(self.client.get(reverse("dashboard")), "Recent applicants")
        self.assertContains(self.client.get(reverse("dashboard")), "candidate")
        self.assertContains(self.client.get(reverse("company_settings")), "Company profile")
        self.assertContains(self.client.get(reverse("job_create")), "Create a role")
        self.assertEqual(application.status, Application.Status.SUBMITTED)

    def test_employer_registration_requires_company_name_and_creates_company(self):
        response = self.client.post(
            reverse("register"),
            {
                "username": "newemployer",
                "email": "team@example.com",
                "role": User.Role.EMPLOYER,
                "company_name": "New Horizon",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
            },
        )
        self.assertRedirects(response, reverse("dashboard"))
        employer = User.objects.get(username="newemployer")
        self.assertEqual(employer.company.name, "New Horizon")
