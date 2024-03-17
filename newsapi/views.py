from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
import json
from .models import NewsStory, Author
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import datetime
from django.utils.dateparse import parse_date



@csrf_exempt
def login_view(request):
    if request.method == 'POST':
        data = json.loads(request.body.decode('utf-8'))  # Parse JSON from request body
        username = data.get('username')
        password = data.get('password')
        
        # Authenticate the user
        user = authenticate(request, username=username, password=password)
        if user is not None:
                login(request, user)
                return HttpResponse("Welcome!", status=200, content_type="text/plain")
        else:
            return HttpResponse("Wrong credentials", status=401, content_type="text/plain")

@csrf_exempt
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return HttpResponse("Goodbye!", content_type="text/plain")

    
@csrf_exempt
@login_required
def post_story(request):
    # Checking if the request user is an author
    try:
        author = request.user.author
    except Author.DoesNotExist:
        return HttpResponse("Unauthenticated author", status=503, content_type="text/plain")

    try:
        # Parse the JSON payload
        story_data = json.loads(request.body.decode('utf-8'))

        # Validate category and region choices
        category_choices = dict(NewsStory.CATEGORY_CHOICES)
        region_choices = dict(NewsStory.REGION_CHOICES)
        category = story_data.get('category')
        region = story_data.get('region')

        if category not in category_choices or region not in region_choices:
            return HttpResponse("Invalid category or region", status=400, content_type="text/plain")

        # Create and save the new story
        NewsStory.objects.create(
            headline=story_data.get('headline'),
            category=category,
            region=region,
            details=story_data.get('details'),
            author=author,
            pub_date=timezone.now().date()
        )

        # Return a 201 Created response
        return HttpResponse("Story added successfully", status=201, content_type="text/plain")

    except Exception as e:
        # Log the error or provide a more detailed message depending on your error handling strategy
        return HttpResponse(f"Error adding story: {e}", status=503, content_type="text/plain")

@csrf_exempt
def stories_view(request):
    #We check what the request method is and then act based on the type.
    if request.method == 'POST':
        return post_story(request)
        #
    elif request.method == 'GET':
        # Extract filters from the query parameters
        story_cat = request.GET.get('story_cat', '*')
        story_region = request.GET.get('story_region', '*')
        story_date_str = request.GET.get('story_date', '*')
        story_date = parse_date(story_date_str) if story_date_str != '*' else None

        # Build the query based on the filters
        stories_query = NewsStory.objects.all()

        if story_cat != '*':
            stories_query = stories_query.filter(category=story_cat)
        if story_region != '*':
            stories_query = stories_query.filter(region=story_region)
        if story_date:
            stories_query = stories_query.filter(pub_date__gte=story_date)
        else:
            # If story_date is '*', consider all dates by filtering against a date far in the past
            stories_query = stories_query.filter(pub_date__gte=datetime(year=2024, month=1, day=1))

        # Check if any stories are found
        if not stories_query.exists():
            return JsonResponse({"error": "No stories found"}, status=404, safe=False)

        # Format the stories for the response
        stories_list = [
            {
                "key": story.id,
                "headline": story.headline,
                "story_cat": story.category,
                "story_region": story.region,
                "author": story.author.user.username,
                "story_date": story.pub_date.strftime('%d/%m/%Y'),
                "story_details": story.details,
            }
            for story in stories_query
        ]

        return JsonResponse({"stories": stories_list}, safe=False, status=200)
    else:
        return HttpResponse("Method not allowed", status=405, content_type="text/plain")


@csrf_exempt    
@login_required
@require_http_methods(["DELETE"])
def delete_story(request, story_key):
    try:
        # Attempt to fetch the story by its key
        story = NewsStory.objects.get(pk=story_key, author=request.user.author)
        
        # Delete the story
        story.delete()

        # Return a 200 OK response
        return HttpResponse("Story deleted successfully", status=200, content_type="text/plain")

    except NewsStory.DoesNotExist:
        # If the story doesn't exist or doesn't belong to the user
        return HttpResponse("Story not found or not owned by user", status=404, content_type="text/plain")

    except Exception as e:
        # For any other errors, return a 503 Service Unavailable response
        return HttpResponse(f"Error deleting story: {str(e)}", status=503, content_type="text/plain")