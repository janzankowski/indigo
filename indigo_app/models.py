from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from languages_plus.models import Language as MasterLanguage
from countries_plus.models import Country as MasterCountry

from indigo_api.models import Document


class Language(models.Model):
    """ The languages available in the UI. They aren't enforced by the API.
    """
    language = models.OneToOneField(MasterLanguage, on_delete=models.CASCADE)

    class Meta:
        ordering = ['language__name_en']

    def __unicode__(self):
        return unicode(self.language)


class Country(models.Model):
    """ The countries available in the UI. They aren't enforced by the API.
    """
    country = models.OneToOneField(MasterCountry, on_delete=models.CASCADE)

    class Meta:
        ordering = ['country__name']
        verbose_name_plural = 'Countries'

    @property
    def code(self):
        return self.country.iso.lower()

    @property
    def name(self):
        return self.country.name

    def as_json(self):
        return {
            'name': self.name,
            'localities': {loc.code: loc.name for loc in self.locality_set.all()},
            'publications': [pub.name for pub in self.publication_set.all()],
        }

    def work_locality(self, work):
        return self.locality_set.filter(code=work.locality).first()

    def __unicode__(self):
        return unicode(self.country.name)

    @classmethod
    def for_work(cls, work):
        return cls.objects.select_related('country').filter(country__iso__iexact=work.country).first()


class Locality(models.Model):
    """ The localities available in the UI. They aren't enforced by the API.
    """
    country = models.ForeignKey(Country, null=False, on_delete=models.CASCADE)
    name = models.CharField(max_length=512, null=False, blank=False, help_text="Local name of this locality")
    code = models.CharField(max_length=100, null=False, blank=False, help_text="Unique code of this locality (used in the FRBR URI)")

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Localities'
        unique_together = (('country', 'code'),)

    def __unicode__(self):
        return unicode(self.name)

    @classmethod
    def for_work(cls, work):
        if work.locality:
            country = Country.for_work(work)
            return country.work_locality(work)


class Editor(models.Model):
    """ A complement to Django's User model that adds extra
    properties that we need, like a default country.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True)

    @property
    def country_code(self):
        if self.country:
            return self.country.country_id.lower()
        return None

    @country_code.setter
    def country_code(self, value):
        if value is None:
            self.country = value
        else:
            self.country = Country.objects.get(country_id=value.upper())


class Publication(models.Model):
    """ The publications available in the UI. They aren't enforced by the API.
    """
    country = models.ForeignKey(Country, null=False, on_delete=models.CASCADE)
    name = models.CharField(max_length=512, null=False, blank=False, unique=True, help_text="Name of this publication")

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return unicode(self.name)


@receiver(pre_save, sender=User)
def set_user_email(sender, **kwargs):
    # ensure the user's username and email match
    user = kwargs["instance"]
    if user.email:
        user.username = user.email
    else:
        user.email = user.username


@receiver(post_save, sender=User)
def create_editor(sender, **kwargs):
    # create editor for user objects
    user = kwargs["instance"]
    if not hasattr(user, 'editor'):
        editor = Editor(user=user)
        # ensure there is a country
        editor.country = Country.objects.first()
        editor.save()


@receiver(post_save, sender=Document)
def update_user_country(sender, **kwargs):
    # default country for user
    document = kwargs["instance"]
    user = document.updated_by_user

    if user and user.editor and not user.editor.country and document.country:
        try:
            user.editor.country_code = document.country
            user.editor.save()
        except Country.DoesNotExist:
            pass
