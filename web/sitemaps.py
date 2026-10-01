from types import SimpleNamespace
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class PublicPagesSitemap(Sitemap):
	changefreq = 'monthly'
	priority = 0.7

	def items(self):
		return ('home', 'about', 'projects', 'team', 'contact')

	def location(self, item):
		return reverse(item)

	def get_urls(self, page=1, site=None, protocol=None):
		if settings.PUBLIC_BASE_URL:
			parsed_url = urlsplit(settings.PUBLIC_BASE_URL)
			site = SimpleNamespace(domain=parsed_url.netloc)
			protocol = parsed_url.scheme
		return super().get_urls(page=page, site=site, protocol=protocol)
