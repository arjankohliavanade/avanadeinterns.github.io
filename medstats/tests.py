from django.contrib.auth.models import User
from medstats.models import ExternalPatient
from django.test import TestCase,Client
import string


class MedstatsTest(TestCase):
    def setUp(self):
        self.credentials = {
            'username': 'temp',
            'password': 'temp'}
        user = User.objects.create_user(**self.credentials)
        user.save()


    def test_login(self):
        # send login data
        response = self.client.post('/login/', self.credentials, follow=True)
        # should be logged in now
        user = response.context['user']
        logged_in = user.is_authenticated
        # tear down - deletes temp user
        if logged_in:
            user.delete()
        self.assertTrue(logged_in, 'Login test failed')

    def test_filter_last_name(self):
        for letter in list(string.lowercase):
            self.assertTrue(self.filter_patient_worked(letter, ''), 'Filter Patient failed for last name pattern : ' + letter)

    def test_filter_first_name(self):
        for letter in list(string.lowercase):
            self.assertTrue(self.filter_patient_worked('', letter), 'Filter Patient failed for first name pattern: ' + letter)

    def test_filter_last_name_and_first_name(self):
        for letter in list(string.lowercase):
            self.assertTrue(self.filter_patient_worked(letter, letter), 'Filter Patient failed for last and first name: ' + letter)

    def filter_patient_worked(self, last_name_pattern, first_name_pattern):
        patients = ExternalPatient.objects.all()
        self.assertTrue(patients.count()>=2,"No patients to test in filter_patient")

        last_name_pattern = last_name_pattern.lower()
        first_name_pattern = first_name_pattern.lower()

        patients_matched = set()
        # find patients that match pattern and add them to the patients_matched set
        for p in patients:
            if last_name_pattern in p.last_name.lower() and first_name_pattern in p.first_name.lower():
                patients_matched.add(p.id)

        # get filtered patient list from server packing params in URL
        params = '?last_name=' + last_name_pattern + '&first_name=' + first_name_pattern
        response = self.client.get('/patients/' + params, follow=True)

        # the returned filtered list data
        filtered_patients = response.context_data['externalpatient_list']

        patients_filtered = set()
        for p in filtered_patients:
            patients_filtered.add(p.id)

        # check that the filtered set has the same matches as the matched set;
        # compare values rather than counts, as counting the number of matches could result in errors
        return patients_filtered == patients_matched

    # Duplicate of existing database is created for testing purposes; tear down automatically handled by unittest