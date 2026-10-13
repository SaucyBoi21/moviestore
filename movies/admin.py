from django.contrib import admin
from django.db.models import Count, Q, Sum, Value
from django.db.models.functions import Coalesce
from django.template.response import TemplateResponse
from django.urls import path

from .models import Movie, Review


class MovieAdmin(admin.ModelAdmin):
    ordering = ['name']
    search_fields = ['name']
    change_list_template = "movies/admin/change_list.html"

    def get_urls(self):
        custom_urls = [
            path(
                "engagement/",
                self.admin_site.admin_view(self.engagement_view),
                name="movies_movie_engagement",
            ),
        ]
        return custom_urls + super().get_urls()  # custom first

    def engagement_view(self, request):
        most_bought = (
            Movie.objects
            .annotate(times_bought=Coalesce(Sum("item__quantity"), Value(0)))
            .order_by("-times_bought", "name")
            .first()
        )

        most_reviewed = (
            Movie.objects
            .annotate(times_reviewed=Count(
                "review", filter=Q(review__inappropriate=False)))
            .order_by("-times_reviewed", "name")
            .first()
        )

        context = {
            **self.admin_site.each_context(request),
            "title": "Movie Engagement",
            "most_bought": most_bought,
            "most_reviewed": most_reviewed,
        }
        return TemplateResponse(request, "movies/admin/engagement.html", context)


admin.site.register(Movie, MovieAdmin)
admin.site.register(Review)