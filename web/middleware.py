from urllib.parse import urlsplit

from django.conf import settings
from django.http import HttpResponsePermanentRedirect


class CanonicalHostMiddleware:
	def __init__(self, get_response):
		self.get_response = get_response
		self.canonical_host = urlsplit(settings.PUBLIC_BASE_URL).netloc.lower()

	def __call__(self, request):
		if self.canonical_host and request.method in {'GET', 'HEAD'}:
			request_host = request.get_host().lower()
			if request_host != self.canonical_host:
				location = f'{settings.PUBLIC_BASE_URL}{request.get_full_path()}'
				return HttpResponsePermanentRedirect(location)
		return self.get_response(request)
