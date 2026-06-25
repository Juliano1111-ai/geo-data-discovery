# geo-data-discovery

**Juliano Ramanantsoa** — University of Bergen / Bjerknes Centre for Climate Research

This is the documentation for a method I use and trust: find Earth-science data,
confirm it actually exists, and — when it is not in a public archive — track it
down, while refusing to ever present a link that has not been resolved this run.

The page that follows is a complete, tested walk-through on a real example. The
software itself, the playbooks, and ready-to-run Python and Colab entry points are
in the [GitHub repository](https://github.com/Juliano1111-ai/geo-data-discovery).

The principle the whole method rests on is simple: a language model can expand a
query and reason over a trail, but it does not get to decide that a download link
is good. Only a script that resolves the link and checks the response can do that.
