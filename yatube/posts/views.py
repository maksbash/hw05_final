from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import TemplateView, ListView

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User
from yatube.settings import MAX_POST_ON_PAGE


class IndexView(ListView):
    template_name = 'posts/index.html'
    context_object_name = 'page_obj'
    post_list = Post.objects.all()

    def get(self, request, *args, **kwargs):
        self.page_number = self.request.GET.get('page')
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        paginator = Paginator(self.post_list, MAX_POST_ON_PAGE)
        return paginator.get_page(self.page_number)


class FollowIndexView(LoginRequiredMixin, IndexView):
    template_name = 'posts/follow.html'

    def get(self, request, *args, **kwargs):
        self.post_list = Post.objects.filter(
            author__following__user=request.user)
        return super().get(request, *args, **kwargs)


class GroupView(IndexView):
    template_name = 'posts/group_list.html'

    def get(self, request, *args, **kwargs):
        slug = kwargs['slug']
        self.group = get_object_or_404(Group, slug=slug)
        self.post_list = self.group.posts.all()
        self.title = f'Записи сообщества {self.group.title}'
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(GroupView, self).get_context_data(**kwargs)
        context['title'] = self.title
        context['group'] = self.group
        return context


class ProfileView(IndexView):
    template_name = 'posts/profile.html'

    def get(self, request, *args, **kwargs):
        author_username = kwargs['username']
        self.author = get_object_or_404(User, username=author_username)
        self.following = False
        if request.user.id is not None:
            if Follow.objects.filter(
                    user=request.user.id, author=self.author.id).exists():
                self.following = True
        
        self.post_list = self.author.posts.all()
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)
        title = f'Профайл пользователя {self.author.get_full_name()}'
        context['title'] = title
        context['count_of_posts'] = self.post_list.count()
        context['author'] = self.author
        context['following'] = self.following
        return context


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comment_form = CommentForm(request.POST or None)
    comments = post.comments.all()
    count_of_posts = post.author.posts.all().count()
    title = f'Пост {post.text[:30]}'
    context = {
        'title': title,
        'count_of_posts': count_of_posts,
        'post': post,
        'comment_form': comment_form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    groups = Group.objects.all()
    form = PostForm(request.POST or None, files=request.FILES or None)

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user.username)

    return render(
        request,
        template,
        {'form': form, 'is_edit': False, 'groups': groups})


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)
    groups = Group.objects.all()
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:post_detail', post_id=post_id)

    return render(
        request,
        template,
        {'form': form,
            'username': request.user,
            'groups': groups,
            'is_edit': True})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user.id != author.id:
        current_follow = Follow.objects.filter(
            user=request.user, author=author).all()
        if current_follow.count() == 0:
            follow = Follow()
            follow.user = request.user
            follow.author = author
            follow.save()
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=request.user, author=author)
    follow.delete()
    return redirect('posts:profile', username=username)
