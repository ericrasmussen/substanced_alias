substanced_alias 1.0a
=========================

A plugin for the Python Substance D (substanced) CMS that allows you to create
aliases for resources. The aliases maintain a reference to a resource in zodb
and perform a redirect to the full URL when accessed.

Ex. You want to share your amazing new blog post located here:
  http://site/blog/categoxsry/posts/neat-article?page=7

But you want the URL to look like this:
  http://site/NEAT

To achieve it, you only need:
  <import and mixin code here>

Then the folder (in this case the Site folder) will list Alias objects as
addable via the Add button.


Singleton FAQ
=============
Why not use a URL shortening service?

Why not indeed! Actually, you probably should use a URL shortening service if
that's an option for you.

But sometimes it's important to use your branded URL, and the small increase in
overhead (an application-level redirect) often outweighs the pain of managing
redirects at the server level. As a bonus, it also means power users can create
and maintain these on their own via substanced's intuitive admin UI.
