# Documentation maintenance

## One documentation site

User tutorials, deployment examples, and developer references are published
together at [Babylon documentation](https://cosmo-tech.github.io/Babylon/latest/).
Keep command and option definitions in the
[generated CLI reference](../references/cli.md), not in separate manual tables.
Check commands against `babylon --help` and the generated templates before
updating a workflow.

The home page is generated from `scripts/index.template.md` by
`scripts/generate_index.py`; edit the template, not a generated `index.md`.
Existing installation, concept, and reference URLs are retained.

Reusable Markdown lives in `docs/partials/` and is included through
`pymdownx.snippets`. These fragments are excluded from standalone pages because
they are rendered within navigable pages. Missing snippet paths fail the build.
Use relative Markdown links and only add assets that are referenced by content.

## Build and preview

Run commands from the repository root with Python 3.12+ and uv:

```bash
uv run --locked --group doc mkdocs build --strict
uv run --locked --group doc mkdocs serve
```

`strict: true` in `mkdocs.yml` also applies to publication through mike.
Do not pass `--strict` to `mike deploy`: strictness is read from the MkDocs
configuration.

Fix actionable MkDocs warnings (missing pages, links, or assets), Python
warnings, and snippet errors rather than disabling validation. Review rendered
pages after a build, especially code snippets, relative links, and images.

### Upstream lifecycle advisories

The locked Material for MkDocs and documentation-plugin versions can print
lifecycle/promotional notices before MkDocs logging starts, including notices
about Material's maintenance plans and MkDocs 2.0. These messages originate in
upstream packages, not in this project's content; they can appear even when
`mkdocs build --strict` succeeds without MkDocs or Python warnings.

Keep those advisories visible. Track upstream support and dependency updates
separately instead of suppressing stderr, filtering warning output, or changing
themes solely to hide them.

## Consolidation provenance

The tutorials, examples, and deployment guides were adapted from
[Cosmo-Tech/Babylon-End-User-Doc](https://github.com/Cosmo-Tech/Babylon-End-User-Doc)
at commit
[`994f76de38bbb05a6166c68d26d099fc3feb289e`](https://github.com/Cosmo-Tech/Babylon-End-User-Doc/tree/994f76de38bbb05a6166c68d26d099fc3feb289e)
(2026-10-06). The source was read-only during this consolidation. Current
Babylon commands and templates take precedence over conflicting source examples.

The migration deliberately combines or replaces the following material:

- The separate home, installation fragments, and manually maintained command
  guide are replaced by the existing generated home, shared installation guide,
  and complete generated CLI reference.
- Getting-started content is split into configuration and state guides.
  Secret names, environment variables, paths, and namespace commands reflect the
  implementation rather than the older examples.
- Organization, solution, workspace, and web app fragments are folded into the
  deployment tutorial. PostgreSQL jobs, scripts, runtime resources, and
  simulator-build guidance are retained without duplicating complete templates.
- Existing-parent examples use explicit API commands. The source's
  `metadata.selector` flow is not implemented by the current macros.
- Dataset and runner macro fragments are replaced by API command guidance;
  `apply` does not handle those resource kinds.
- Workspace creation, ACL updates, Superset, Power BI, and delivery-brewery
  examples are retained and updated for the supported workflow.
- The commented-out Brewery v4 walkthrough and ADX Power BI report guide are
  replaced by current Brewery and PostgreSQL-backed Power BI guidance.
  Standalone Azure, Power BI, Vault, and Terraform Cloud CLI instructions are
  not republished as supported commands.
- Outdated Docker persistence paths and commented release-download instructions
  are omitted in favor of one source-installation guide. Legacy screenshots,
  duplicate branding, and unused CSS are not imported.

No changes to the separate documentation repository are required to build this
site. Its publication/retirement is a separate repository-owner operation.

### Source license

The adapted documentation is MIT licensed. The original source notice is
preserved below:

--8<-- "docs/partials/end_user_doc_license.md"
