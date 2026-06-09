from django.test import TestCase
from django.urls import reverse


class ComponentsTestCase(TestCase):
    def test_index_template(self):
        response = self.client.get(reverse("components_index"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "kanban/components/index.html")
