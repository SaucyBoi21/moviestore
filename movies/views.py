from django.db.models.aggregates import Avg, Count
from django.shortcuts import render, redirect, get_object_or_404
from .models import Movie, Review, Rating
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.db.models.functions import Coalesce
from django.db.models import Sum


@staff_member_required
def statistics(request):
    user_comment_stats = User.objects.annotate(comment_number=Count('review')).order_by(
        '-comment_number'
    )
    template_data = {}
    template_data['title'] = 'User Statistics'
    template_data['users'] = user_comment_stats

    return render(request, 'movies/statistics.html',
                  {'template_data': template_data})

@staff_member_required
def purchase_statistics(request):
    users = (
        User.objects
        .annotate(movies_purchased=Coalesce(Sum('order__item__quantity'), 0))
        .filter(movies_purchased__gt=0)
        .order_by('-movies_purchased', 'username')
    )

    show_top = request.GET.get('view') == 'top'

    # Optional list size: blank, invalid, or < 1 means "all users"
    limit_raw = request.GET.get('limit', '').strip()
    limit = int(limit_raw) if limit_raw.isdigit() and int(limit_raw) > 0 else None
    if show_top:
        leader = users.first()
        if leader:
                users = users.filter(movies_purchased=leader.movies_purchased)
    elif limit:
        users = users[:limit]

    template_data = {
        'title': 'Purchase Statistics',
        'users': users,
        'show_top': show_top,
        'limit': limit,
    }
    return render(request, 'movies/purchase_statistics.html',
                  {'template_data': template_data})

@login_required
def edit_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id)
    if request.user != review.user:
        return redirect('movies.show', id=id)
    if request.method == 'GET':
        template_data = {}
        template_data['title'] = 'Edit Review'
        template_data['review'] = review
        return render(request, 'movies/edit_review.html',
            {'template_data': template_data})
    elif request.method == 'POST' and request.POST['comment'] != '':
        review = Review.objects.get(id=review_id)
        review.comment = request.POST['comment']
        review.save()
        return redirect('movies.show', id=id)
    else:
        return redirect('movies.show', id=id)
def index(request):
    search_term = request.GET.get('search')
    if search_term:
        movies = Movie.objects.filter(name__icontains=search_term)
    else:
        movies = Movie.objects.all()
    template_data = {}
    template_data['title'] = 'Movies'
    template_data['movies'] = movies
    return render(request, 'movies/index.html',
                  {'template_data': template_data})
    
def show(request, id):
    movie = Movie.objects.get(id=id)
    reviews = Review.objects.filter(movie=movie)

    rating_stats = Rating.objects.filter(movie=movie).aggregate(
        average_rating=Avg('value'),
        rating_count=Count('id')
    )
    
    user_rating = None
    if request.user.is_authenticated:
        user_rating = Rating.objects.filter(movie=movie, user=request.user).first()
    
    template_data = {}
    template_data['title'] = movie.name
    template_data['movie'] = movie
    template_data['reviews'] = reviews
    template_data['average_rating'] = rating_stats['average_rating']
    template_data['rating_count'] = rating_stats['rating_count']
    template_data['user_rating'] = user_rating 
    return render(request, 'movies/show.html',
                  {'template_data': template_data})
    
@login_required
def create_review(request, id):
    if request.method == 'POST' and request.POST['comment'] != '':
        movie = Movie.objects.get(id=id)
        review = Review()
        review.comment = request.POST['comment']
        review.movie = movie
        review.user = request.user
        review.save()
        return redirect('movies.show', id=id)
    else:
        return redirect('movies.show', id=id)

@login_required
def delete_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id,
        user=request.user)
    review.delete()
    return redirect('movies.show', id=id)

@login_required
def flag_review(request, id, review_id):
    review = get_object_or_404(Review, id=review_id)
    review.inappropriate = True
    review.save()
    return redirect('movies.show', id=id)

@login_required
def rate_movie(request, id):
    movie = get_object_or_404(Movie, id=id)
    if request.method == 'POST':
        try: 
            value = int(request.POST.get('rating', 0))
        except ValueError:
            value = 0
        if 1 <= value <= 5:
            Rating.objects.update_or_create(
                movie=movie,
                user=request.user,
                defaults={'value': value}
            )
    return redirect('movies.show', id=id)