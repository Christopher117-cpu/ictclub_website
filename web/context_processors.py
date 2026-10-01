import json

from django.conf import settings
from django.templatetags.static import static
from .models import Announcement


def public_announcements(request):
	return {
		'public_announcements': Announcement.objects.filter(
			is_public=True,
		).select_related('created_by').order_by('-created_at')[:3],
	}


def seo_metadata(request):
	public_base_url = settings.PUBLIC_BASE_URL
	canonical_url = (
		f'{public_base_url}{request.path}'
		if public_base_url
		else request.build_absolute_uri(request.path)
	)
	site_root_url = public_base_url or request.build_absolute_uri('/')
	social_image_path = static('web/assets/logo.webp')
	social_image_url = (
		f'{public_base_url}{social_image_path}'
		if public_base_url
		else request.build_absolute_uri(social_image_path)
	)
	structured_data = {
		'@context': 'https://schema.org',
		'@graph': [
			{
				'@type': 'Organization',
				'@id': f'{site_root_url.rstrip("/")}/#club',
				'name': 'Blessed Sacrament Secondary School ICT Club',
				'email': 'ictclubbsk@gmail.com',
				'address': {
					'@type': 'PostalAddress',
					'addressLocality': 'Masaka City',
					'addressCountry': 'UG',
				},
			},
			{
				'@type': 'WebSite',
				'@id': f'{site_root_url.rstrip("/")}/#website',
				'name': 'Blessed Sacrament Secondary School ICT Club',
				'url': site_root_url,
			},
		],
	}
	return {
		'canonical_url': canonical_url,
		'social_image_url': social_image_url,
		'structured_data_json': json.dumps(structured_data).replace('<', '\\u003c'),
	}
