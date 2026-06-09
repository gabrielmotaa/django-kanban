from django.test import TestCase
from django.urls import reverse


class TemplateTestCase(TestCase):
    def test_index_template(self):
        response = self.client.get(reverse("templates_index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "kanban/templates/index.html")
