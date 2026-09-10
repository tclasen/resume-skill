# Reviewed upstream artifacts

`pins.json` records exact versions, immutable Git commits or dated W3C
publications, source URLs, canonical namespaces, and SHA-256 checksums.
The artifacts are unmodified upstream downloads. Validate them offline with:

```sh
python3 skills/resume/scripts/pins.py
```

OKF is licensed under the included `OKF-LICENSE`; Schema.org includes
`SCHEMAORG-LICENSE`. W3C's document license is included in
`W3C-DOCUMENT-LICENSE.html`; the normative publications are
[PROV-O](https://www.w3.org/TR/2013/REC-prov-o-20130430/) and
[SKOS](https://www.w3.org/TR/2009/REC-skos-reference-20090818/).
The SKOS RDF artifact represents only a subset of its normative semantic
conditions; consult the publication when modeling values and relationships.

Ontology imports, equivalence annotations, and example namespaces do not approve
additional vocabularies. A property must be defined by one of the three approved
ontologies and retain its domain, range, and meaning. Keep unmappable evidence
in narrative form and report the modeling gap.

Checksums detect drift relative to this reviewed manifest, not malicious changes
to both artifact and manifest. Pin updates require deliberate maintainer review
of the upstream diff, licensing, semantic changes, manifest, validator's version
allowlist, and affected authoring rules. Never regenerate pins automatically to
make validation pass.
