import re
import uuid

from django.db import migrations
from django.utils.text import slugify

VALID = re.compile(r'^[-a-zA-Z0-9_]+$')


def clean_slugs(apps, schema_editor):
    """Rewrite old slugs that contain characters like — & : ( ) so URLs are clean."""
    Course = apps.get_model('courses', 'Course')
    for course in Course.objects.all():
        if course.slug and VALID.match(course.slug):
            continue
        old_suffix = (course.slug or '')[-8:]
        suffix = old_suffix if re.fullmatch(r'[0-9a-f]{8}', old_suffix) else uuid.uuid4().hex[:8]
        clean = slugify(course.title)[:180].strip('-') or 'course'
        new_slug = f'{clean}-{suffix}'
        while Course.objects.filter(slug=new_slug).exclude(pk=course.pk).exists():
            new_slug = f'{clean}-{uuid.uuid4().hex[:8]}'
        course.slug = new_slug
        course.save(update_fields=['slug'])


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0003_alter_lecture_order_alter_studentresource_course_and_more'),
    ]

    operations = [
        migrations.RunPython(clean_slugs, migrations.RunPython.noop),
    ]
