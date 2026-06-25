# Geoscience data discovery

**Juliano Ramanantsoa** — Department of Earth Science, University of Bergen · ORCID [0000-0003-0831-2802](https://orcid.org/0000-0003-0831-2802)

Finding data in the Earth sciences is rarely the clean step it ought to be. The
dataset you need is real, but the downloadable product is scattered across
infrastructures, sits behind a portal, is described only in a project deliverable,
or was simply never archived. And when you ask a language model where to download
it, the answer often comes back as confident links that do not resolve — which,
for a paper, a proposal, or a course, is worse than no answer at all.

This documentation describes the method I use to get past that, written down and
made reproducible. It keeps what a language model is genuinely good at, expanding
a query into the right vocabulary, routing it to the right infrastructure, and
reasoning over a forensic trail, and removes the one thing it cannot be trusted
to do: decide that a link is good. **No link enters the verified output unless a
script has resolved it and confirmed the response is the data that was asked for,
in this run.** Everything else in the design follows from that single rule.

The page that follows is a complete, tested walk-through on a real example. The
software itself, the playbooks, and ready-to-run Python and Colab entry points are
in the [GitHub repository](https://github.com/Juliano1111-ai/geo-data-discovery).

